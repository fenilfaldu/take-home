# SWE Harbor Take-Home Assignment

## What Is This?

[Verifiers](https://github.com/PrimeIntellect-ai/verifiers) is a framework for training and evaluating AI coding agents — models that can read code, run commands, and write solutions inside a terminal. To measure how good these agents are, we need **benchmarks**: coding challenges that an AI agent attempts to solve inside a Docker container.

That's where **Harbor tasks** come in. Each Harbor task is a self-contained coding challenge with:

- A problem statement (what the agent sees)
- A Docker environment (where the agent works)
- Automated tests (how we check the answer)
- A reference solution (proof the task is solvable)

The framework loads a task, spins up a Docker container, hands the agent the problem statement, and once the agent finishes, runs the tests. The result is a reward: **1** for pass, **0** for fail.

**Your job is to design the challenges and write the tests.** You're building the evaluation, not the agent. The tasks you create will be used to measure how good AI agents are at real software engineering work.

## Your Deliverables

Create **1-2 original software engineering tasks** in Harbor format. Place each task in its own directory under `tasks/`.

Each task directory must contain these five files:

| File | Purpose |
|------|---------|
| `task.toml` | Task metadata — difficulty level, timeouts, which Docker image to use |
| `instruction.md` | The problem statement the agent sees — what to build, fix, or implement |
| `environment/Dockerfile` | Sets up the Docker container with any starter code or dependencies |
| `solution/solve.sh` | Your reference solution — a bash script that produces the correct answer |
| `tests/test_solution.py` | Pytest test cases that verify the solution is correct |
| `tests/test.sh` | Test runner that executes the tests and writes the reward file |

You may also include a brief `NOTES.md` explaining your design choices.

**Requirements:**

1. The reference solution (`solve.sh`) must pass all tests (reward = 1)
2. Tests must **fail** without the solution applied (reward = 0) — if tests pass on the bare environment, they aren't testing anything useful
3. Tests should catch incorrect or incomplete solutions, not just verify the happy path
4. At least one task should involve **multiple files** (e.g., fixing a bug across modules, implementing a small system with interacting components)

## What Makes a Good Task

### Good Task Types

| Type | Example | Why It's Good |
|------|---------|---------------|
| **Debug existing code** | Plant realistic bugs in a working Flask app — a wrong query, an off-by-one in pagination, a missing error handler | Tests code reading + reasoning, not just writing from scratch |
| **Implement from a spec** | Give a detailed interface spec for a caching layer, agent writes the implementation | Tests whether the agent can translate requirements to working code |
| **Build a small tool** | Write a CLI tool that processes CSV files and outputs summary statistics | Tests end-to-end engineering: argument parsing, file I/O, output formatting |
| **Fix a broken config/setup** | A Dockerfile with wrong dependency versions, a misconfigured server, a broken build script | Tests practical devops and troubleshooting skills |
| **Refactor for correctness** | Code that works for common cases but has subtle bugs under edge cases (concurrency, large input, special characters) | Tests careful code analysis and attention to detail |

### What Makes Tasks Good for AI Evaluation

- **Solvable entirely in a terminal** — no GUI, no browser, no human interaction needed
- **Clear pass/fail** — tests can deterministically verify the answer
- **Requires reading and understanding existing code**, not just greenfield writing
- **Has a single correct behavior** — not subjective or style-based
- **Multiple files encouraged** — real code lives across files, and navigating a codebase is a key skill to evaluate
- **Scope**: A skilled engineer should be able to solve each task in **15–45 minutes**

### Anti-Patterns to Avoid

- **Leetcode / competitive programming puzzles** — these test algorithm knowledge, not software engineering
- **Tasks requiring internet access or external APIs** — the Docker container is isolated
- **Subjective tasks** (e.g., "make this code more readable") — no deterministic pass/fail
- **Trivially passable tests** — if the tests can pass without actually solving the problem, the task is useless for evaluation
- **Overly broad tasks** — "build a web app" is too vague; scope it down to something specific and testable

## Getting Started

1. **Study the examples**: Look at `tasks/implement-linked-list/` and `tasks/fix-flask-api/` to understand the format
2. **Copy the template**: `cp -r tasks/_template tasks/your-task-name`
3. **Fill in each file**: Follow the TODO comments in the template
4. **Test locally**: Use Docker to verify your task works end-to-end (see [Testing Locally](#testing-locally))

## Testing Locally

You need to verify two things: (1) your solution passes the tests, and (2) the tests fail without your solution.

**Step 1: Build the Docker image**

```bash
docker build -t my-task tasks/my-task-name/environment/
```

**Step 2: Run with your solution and verify tests pass (reward should be `1`)**

```bash
docker run --rm \
    -v $(pwd)/tasks/my-task-name/solution:/solution \
    -v $(pwd)/tasks/my-task-name/tests:/tests \
    my-task \
    bash -c "mkdir -p /logs/verifier && cd /app && bash /solution/solve.sh && bash /tests/test.sh && cat /logs/verifier/reward.txt"
```

**Step 3: Run without your solution and verify tests fail (reward should be `0`)**

```bash
docker run --rm \
    -v $(pwd)/tasks/my-task-name/tests:/tests \
    my-task \
    bash -c "mkdir -p /logs/verifier && bash /tests/test.sh && cat /logs/verifier/reward.txt"
```

If Step 2 prints `1` and Step 3 prints `0`, your task is working correctly. If both print `1`, your tests aren't actually checking the solution — go back and strengthen them.

## Harbor Format Reference

### `task.toml`

Metadata about the task:

```toml
version = "1.0"

[metadata]
author_name = "Your Name"
author_email = "you@example.com"
difficulty = "easy"        # easy | medium | hard
category = "programming"
tags = ["python", "data-structures"]

[verifier]
timeout_sec = 120.0        # Max time for test execution

[agent]
timeout_sec = 300.0        # Max time for the agent to work

[environment]
docker_image = "python:3.11-slim"
```

### `instruction.md`

The problem statement the agent receives. Be specific about:

- What files to create or modify
- Expected function signatures, class interfaces, or CLI behavior
- Input/output examples where helpful
- Constraints or requirements

### `environment/Dockerfile`

Sets up the Docker container. For simple tasks:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
```

For tasks with pre-existing code, COPY files into the image:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install flask
COPY app/ /app/
```

### `solution/solve.sh`

A bash script that produces the correct solution. This runs inside the container at `/app`. It can:

- Write files directly (using heredocs or `cat`)
- Apply patches with `sed` or `patch`
- Run commands to generate output

The solution must be deterministic and pass all tests.

### `tests/test.sh`

Entry point for test execution. Standard pattern:

```bash
#!/bin/bash
cd /app

pip install pytest > /dev/null 2>&1

pytest /tests/test_solution.py -v 2>&1

if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
```

The script must write `1` (pass) or `0` (fail) to `/logs/verifier/reward.txt`.

### `tests/test_solution.py`

Standard pytest test file. Tips:

- Use descriptive test names and assertion messages
- Test the happy path, edge cases, and error conditions
- Keep tests independent (no shared mutable state)

Good luck!
