# v2-tutorial
A tutorial to introduce users to Flyte v2 features through examples

## Quick start

Prereqs: Python 3.10+.

### Option A: uv (recommended)

If you don't have `uv`:

```
curl -fsSL https://astral.sh/uv/install.sh | sh
```

Then install dependencies declared in `pyproject.toml`:

```
uv sync
```

### Option B: pip

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Running examples:
- Use `flyte run ...` from your venv, or prefix with `uv run` if using uv.
- Ensure your Flyte CLI is configured for your project/domain. You can pass `-p <project> -d <domain>` to the command if needed.

## Exercises

### 1) Hello Polyglot

Command:

```
flyte run 1_hello_world/hello_polyglot.py main --letter e
```

What it does:
- Fans out dynamically across languages from `polyglot-hello` whose primary/alias code starts with the given letter.
- Runs `hello_for_code` in parallel via `flyte.map`, returning a mapping of language code → greeting.
- Validates `letter` (requires a single alphabetic character).

Tip: change `--letter` (e.g., `p`, `s`, `f`) to see different sets.

### 2) Failure handling and resource overrides

Command:

```
flyte run 2_failure_handling/oomer.py failure_recovery
```

What it does:
- Intentionally triggers an OOM in `oomer` (allocates a very large list) with small default memory.
- Catches `flyte.errors.OOMError` and retries the same task with higher memory via `.override(resources=...)`.
- Always runs `always_succeeds()` in a `finally` block and returns its result to demonstrate cleanup and recovery.

### 3) Dependency-aware agents (toy sandwich planner)

Command:

```
flyte run 3_agents/smolagent.py main --goal "Make a peanut butter and jelly sandwich"
```

What it does:
- Builds a simple plan (steps with `deps`) in `get_plan`, then executes it in `execute_plan` respecting dependencies.
- Runs ready steps concurrently, grouping iterations with `flyte.group`, and aggregates results by step id.
- Uses a reusable task environment (single warm replica) and a preinstalled image dependency for faster iteration.

Try changing `--goal` to explore different prints/flow; the toy plan remains the same to showcase orchestration.

### 4) Reports bundle (interactive HTML reports)

Command:

```
flyte run 4_reports/run_all.py main
```

What it does:
- Orchestrates all report generators concurrently: globe visualization (Three.js), interactive dashboard (Chart.js/D3), 3D scatter (Plotly), satellite images gallery, protein 3D viewer, and a YouTube embed page.
- Each task emits a rich HTML report via `flyte.report`; `run_all` simply gathers them so you can open each artifact from the Union UI.

