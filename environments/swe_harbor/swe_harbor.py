import logging
from pathlib import Path

from verifiers.envs.experimental.harbor_env import HarborEnv

logger = logging.getLogger("verifiers.envs.SweHarborEnv")


class SweHarborEnv(HarborEnv):
    """Harbor environment for SWE intern take-home tasks.

    This environment reuses all Harbor task loading, test execution, and reward
    computation from the base HarborEnv class.  The run_command simply prints
    the task instruction so candidates can focus on authoring tasks and tests
    rather than building agent scaffolding.
    """

    def __init__(
        self,
        dataset_path: str | Path,
        tasks: list[str] | None = None,
        agent_workdir: str = "/app",
        docker_image: str = "python:3.11-slim",
        **kwargs,
    ):
        run_command = "cat /task/instruction.md"

        super().__init__(
            run_command=run_command,
            dataset_path=dataset_path,
            tasks=tasks,
            agent_workdir=agent_workdir,
            docker_image=docker_image,
            **kwargs,
        )


def load_environment(
    dataset_path: str | Path = Path(__file__).parent / "tasks",
    tasks: list[str] | None = None,
    agent_workdir: str = "/app",
    docker_image: str = "python:3.11-slim",
    timeout_seconds: float = 600.0,
    cpu_cores: int = 2,
    memory_gb: int = 4,
    disk_size_gb: int = 10,
    timeout_minutes: int = 60,
    max_turns: int = 1,
) -> SweHarborEnv:
    return SweHarborEnv(
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
