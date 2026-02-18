import logging
import tempfile
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-ignore]

import verifiers as vf
from verifiers.envs.experimental.harbor_env import HarborEnv

logger = logging.getLogger(__name__)

DEFAULT_DOCKER_IMAGE = "python:3.11-slim"


def _load_task_docker_image(task_dir: Path, fallback: str) -> str:
    toml_path = task_dir / "task.toml"
    if not toml_path.exists():
        return fallback
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("environment", {}).get("docker_image", fallback)
    except Exception:
        return fallback


class DataTasksEnv(HarborEnv):
    """Harbor environment for data science / analytics tasks.

    Each task provides:
      - instruction.md    : problem statement the agent reads
      - environment/prepare_data.py : generates synthetic datasets inside the sandbox
      - solution/solve.sh : reference solution
      - tests/test.sh     : verifier that writes 1/0 to /logs/verifier/reward.txt

    The agent has four tools: bash, read_file, write_file, str_replace.
    Per-task Docker images are resolved from task.toml [environment] docker_image.
    """

    def __init__(
        self,
        dataset_path: str | Path,
        tasks: list[str] | None = None,
        agent_workdir: str = "/app",
        docker_image: str = DEFAULT_DOCKER_IMAGE,
        **kwargs,
    ):
        self._dataset_path = Path(dataset_path)
        self._default_docker_image = docker_image
        kwargs.setdefault("sandbox_wait_for_creation_max_attempts", 300)
        super().__init__(
            run_command="python /app/agent.py 2>&1",
            dataset_path=dataset_path,
            tasks=tasks,
            agent_workdir=agent_workdir,
            docker_image=docker_image,
            **kwargs,
        )

    def _get_docker_image_for_task(self, task_name: str) -> str:
        task_dir = self._dataset_path / task_name
        image = _load_task_docker_image(task_dir, self._default_docker_image)
        if image != self._default_docker_image:
            logger.info(f"Task '{task_name}' using custom docker image: {image}")
        return image

    async def get_docker_image(self, state: vf.State) -> str:
        task_name = state.get("task", "")
        if task_name:
            image = self._get_docker_image_for_task(task_name)
            logger.info(f"Task '{task_name}' → docker image: {image}")
            return image
        return self._default_docker_image

    async def post_sandbox_setup(self, state: vf.State) -> None:
        await super().post_sandbox_setup(state)

        sandbox_id = state["sandbox_id"]
        task_name = state.get("task", "")

        logger.info("Installing Python packages in sandbox...")
        result = await self.sandbox_client.execute_command(
            sandbox_id,
            "pip install openai pandas numpy matplotlib 2>&1 | tail -10",
            working_dir=None,
            timeout=600,
        )
        if result and result.stdout:
            logger.info(f"pip install output: {result.stdout.strip()}")

        prepare_script = self._dataset_path / task_name / "environment" / "prepare_data.py"
        if prepare_script.exists():
            logger.info(f"Uploading prepare_data.py for task '{task_name}'...")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
                tmp.write(prepare_script.read_text())
                tmp_path = tmp.name
            try:
                await self.sandbox_client.upload_file(
                    sandbox_id, "/app/prepare_data.py", tmp_path
                )
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            logger.info("Running prepare_data.py to generate data files...")
            result = await self.sandbox_client.execute_command(
                sandbox_id,
                "cd /app && python prepare_data.py 2>&1",
                working_dir=None,
                timeout=300,
            )
            if result and result.stdout:
                logger.info(f"prepare_data.py output: {result.stdout.strip()}")

            result = await self.sandbox_client.execute_command(
                sandbox_id,
                "ls -lh /app/*.csv 2>/dev/null || echo 'WARNING: no CSV files found'",
                working_dir=None,
                timeout=30,
            )
            if result and result.stdout:
                logger.info(f"Data files: {result.stdout.strip()}")
        else:
            logger.warning(f"No prepare_data.py found for task '{task_name}' at {prepare_script}")

        agent_script = self._get_agent_script()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(agent_script)
            tmp_path = tmp.name
        try:
            await self.sandbox_client.upload_file(
                sandbox_id, "/app/agent.py", tmp_path
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        logger.info("Sandbox setup complete. Agent ready.")

    async def build_env_vars(self, state: vf.State) -> dict[str, str]:
        import os
        env_vars = await super().build_env_vars(state)
        env_vars.setdefault(
            "OPENAI_API_KEY",
            os.environ.get("OPENAI_API_KEY", "sk-placeholder"),
        )
        env_vars.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        return env_vars

    @staticmethod
    def _get_agent_script() -> str:
        return r'''#!/usr/bin/env python3
import json
import os
import subprocess
import sys

from openai import OpenAI

MAX_TURNS = 60
MODEL = os.environ.get("OPENAI_MODEL", "openai/gpt-4o")

SYSTEM_PROMPT = (
    "You are an expert data scientist. "
    "You have tools: bash, read_file, write_file, str_replace. "
    "STRATEGY: read /task/instruction.md, then write a COMPLETE Python analysis script to "
    "/app/analyze.py using write_file (using pandas/numpy/matplotlib), then run it with "
    "bash('python /app/analyze.py'). "
    "The script must produce ALL required output files in /app/submission/. "
    "Data files are already in /app/ — do NOT try to read large CSVs with read_file. "
    "After running the script, verify outputs with bash('ls /app/submission/'). "
    "Fix any errors in the script and rerun. When outputs exist, stop."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Execute a shell command and return stdout, stderr, and exit code. "
                "Use this to run Python scripts, inspect files, install packages, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content. Creates parent directories as needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file."},
                    "content": {"type": "string", "description": "The content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace exactly one occurrence of a string in a file. "
                "Fails if the string appears zero or more than one time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file."},
                    "old_str": {"type": "string", "description": "The exact string to find (must appear exactly once)."},
                    "new_str": {"type": "string", "description": "The replacement string."},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
]


def tool_bash(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=300
    )
    parts = []
    if result.stdout:
        parts.append(f"stdout:\n{_truncate(result.stdout)}")
    if result.stderr:
        parts.append(f"stderr:\n{_truncate(result.stderr)}")
    parts.append(f"exit_code: {result.returncode}")
    return "\n".join(parts)


MAX_OUTPUT_CHARS = 5_000


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[...TRUNCATED at {limit} chars — output was {len(text)} chars total]"


def tool_read_file(path: str) -> str:
    try:
        with open(path) as f:
            content = f.read(MAX_OUTPUT_CHARS + 100)
        return _truncate(content)
    except Exception as e:
        return f"Error reading {path}: {e}"


def tool_write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def tool_str_replace(path: str, old_str: str, new_str: str) -> str:
    try:
        with open(path) as f:
            content = f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str not found in {path}"
    if count > 1:
        return f"Error: old_str appears {count} times in {path} (must be exactly 1)"

    new_content = content.replace(old_str, new_str, 1)
    with open(path, "w") as f:
        f.write(new_content)
    return f"Replaced 1 occurrence in {path}"


TOOL_DISPATCH = {
    "bash": lambda args: tool_bash(args["command"]),
    "read_file": lambda args: tool_read_file(args["path"]),
    "write_file": lambda args: tool_write_file(args["path"], args["content"]),
    "str_replace": lambda args: tool_str_replace(args["path"], args["old_str"], args["new_str"]),
}


def main():
    client = OpenAI()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Read /task/instruction.md and complete the data analysis task."},
    ]

    for turn in range(MAX_TURNS):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                parallel_tool_calls=False,
            )
        except Exception as e:
            import traceback
            err = f"API error on turn {turn}: {e}\n{traceback.format_exc()}"
            print(err, file=sys.stderr)
            with open("/app/agent_error.log", "w") as _f:
                _f.write(err)
            sys.exit(1)

        choice = response.choices[0]
        assistant_msg = choice.message

        msg_dict = {
            "role": "assistant",
            "content": assistant_msg.content,
        }
        if assistant_msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ]
        messages.append(msg_dict)

        if not assistant_msg.tool_calls:
            if assistant_msg.content:
                print(assistant_msg.content)
            break

        for tool_call in assistant_msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            handler = TOOL_DISPATCH.get(fn_name)
            if handler is None:
                result = f"Unknown tool: {fn_name}"
            else:
                try:
                    result = handler(fn_args)
                except Exception as e:
                    result = f"Error executing {fn_name}: {e}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )
    else:
        print("Agent reached maximum number of turns.")


if __name__ == "__main__":
    main()
'''


def load_environment(
    dataset_path: str | Path = Path(__file__).parent / "tasks",
    tasks: list[str] | None = None,
    agent_workdir: str = "/app",
    docker_image: str = DEFAULT_DOCKER_IMAGE,
    timeout_seconds: float = 900.0,
    cpu_cores: int = 2,
    memory_gb: int = 4,
    disk_size_gb: int = 10,
    timeout_minutes: int = 60,
    max_turns: int = 60,
) -> DataTasksEnv:
    return DataTasksEnv(
        dataset_path=dataset_path,
        tasks=tasks,
        agent_workdir=agent_workdir,
        docker_image=docker_image,
        timeout_seconds=timeout_seconds,
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        disk_size_gb=disk_size_gb,
        timeout_minutes=timeout_minutes,
        max_turns=max_turns,
    )
