# Data Tasks Environment

A [Harbor-format](https://github.com/PrimeIntellect-ai/verifiers) environment for evaluating and training LLMs on real-world data science and analytics tasks.

Built on the [Prime Intellect Verifiers](https://github.com/PrimeIntellect-ai/verifiers) framework.

## Overview

Each task drops a model into a sandboxed Python environment with synthetic datasets and asks it to produce analytical outputs — charts, JSON reports, notebooks — using a set of bash and file tools. A verifier checks the outputs for correctness and writes a binary reward (1 = pass, 0 = fail).

The agent has four tools available inside the sandbox:

| Tool | Description |
|------|-------------|
| `bash` | Run shell commands, Python scripts, install packages |
| `read_file` | Read any file by path |
| `write_file` | Create or overwrite a file |
| `str_replace` | Make a targeted single-occurrence edit to a file |

## Tasks

### 1. `analyze-company-data` — Investigate Product Engagement Regression

**Difficulty:** Medium  
**Category:** Product Analytics

The agent receives two messy CSVs (`users.csv`, `events.csv`) spanning 28 days of product events and must investigate a user engagement regression. It needs to clean the data, identify the affected platform segment, pinpoint when the regression started, and produce:

- `submission/results.json` — structured findings (segment, funnel drop, engagement changes by platform and country)
- 5 visualizations (engagement trend, funnel comparison, geographic breakdown, mobile event volume, platform gap)
- `submission/summary.md` — executive summary with key findings and funnel breakdown table

**Verifier:** Checks JSON schema and value correctness, plot file existence.

---

### 2. `customers-spending-behavior` — Customer Value Analysis Notebook

**Difficulty:** Medium  
**Category:** Business Intelligence / Data Storytelling

The agent receives a customer spending CSV (~3,900 rows) and must produce an `analysis.ipynb` notebook with three specific visualizations using matplotlib/seaborn:

1. **True Value Scatter** — Age vs. Annual Value (frequency-adjusted purchase amount), colored by subscription status, filtered to customers with >10 purchases
2. **Category Performance Matrix** — Bubble chart of avg rating vs. total revenue per category, with a dashed average-revenue reference line
3. **Drivers of Value Heatmap** — Annotated correlation matrix of Age, Previous Purchases, Review Rating, and Annual Value

**Verifier:** Executes the notebook, inspects plot data against ground-truth calculations.

---

### 3. `pandas-memory-optimization-colab` — Memory-Efficient Data Processing

**Difficulty:** Hard  
**Category:** Performance Engineering / Data Engineering

The agent receives a Jupyter notebook (`process_data.ipynb`) that loads an entire CSV into memory and crashes with `MemoryError` on large files. The notebook's main function call is commented out. The agent must:

- Rewrite the notebook to use chunked reading (`pd.read_csv(chunksize=...)`) or streaming
- Uncomment/add the function call so the notebook executes end-to-end
- Keep peak memory under 400 MB while processing a ~250 MB CSV
- Produce the same output files: `daily_summary.csv`, `monthly_summary.csv`, `category_summary.csv`, `pivot_daily.csv`, `pivot_monthly.csv`, `data_YYYY.csv`

**Verifier:** Generates a fresh 500K-row test CSV, executes the notebook via `jupyter nbconvert`, monitors peak memory usage, and validates all output files and schemas.

---

## Eval Results (haiku-4.5)

| Task | Avg Reward | Avg Turns | Notes |
|------|-----------|-----------|-------|
| `analyze-company-data` | 1.0 | 23 | Passes consistently |
| `customers-spending-behavior` | 1.0 | 16 | Passes consistently |
| `pandas-memory-optimization-colab` | — | — | Requires chunking implementation |

## Quick Start

```bash
prime env install fenil/data-tasks
```

Run a single task:
```bash
prime eval run data-tasks -m haiku -r 1 --env-args '{"tasks": ["analyze-company-data"]}'
prime eval run data-tasks -m haiku -r 1 --env-args '{"tasks": ["customers-spending-behavior"]}'
prime eval run data-tasks -m haiku -r 1 --env-args '{"tasks": ["pandas-memory-optimization-colab"]}'
```

Run all tasks:
```bash
prime eval run data-tasks -m haiku
```

## Environment Design

### How It Works

1. A `python:3.11-slim` Prime Sandbox starts
2. Base deps are installed (`openai`, `pandas`, `numpy`, `matplotlib`)
3. Task-specific `prepare_data.py` runs to generate synthetic datasets and install any extra deps
4. The agent script (`agent.py`) is uploaded and executed
5. The agent reads `/task/instruction.md` and uses its tools to produce outputs
6. `tests/test.sh` runs the verifier, writing `1` or `0` to `/logs/verifier/reward.txt`

### Task Structure

```
tasks/<task-name>/
├── task.toml              # Metadata (difficulty, timeouts, docker image)
├── instruction.md         # Problem statement the agent sees
├── environment/
│   └── prepare_data.py    # Generates synthetic data + installs extra deps
├── solution/
│   └── solve.sh           # Reference solution (reward = 1)
└── tests/
    ├── test.sh            # Verifier runner (writes reward.txt)
    └── test_*.py          # Pytest test logic
```

### Per-Task Docker Images

Each task can specify its own Docker image in `task.toml`:

```toml
[environment]
docker_image = "python:3.11-slim"
```

This is resolved at runtime — no Docker-in-Docker required.

## Dependencies

```toml
[project]
dependencies = [
    "verifiers>=0.1.10.dev4",
    "prime-sandboxes>=0.2.10",
    "tomli>=2.3.0",
]
```
