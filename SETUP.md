# Fedora 43 + Python 3.14 Setup Guide

This document details the fixes applied to make the Flyte v2 tutorial work seamlessly on Fedora 43 with Python 3.14+.

## What Was Fixed

### 1. Python 3.14 Compatibility - Traversable Import Error

**Issue**: Python 3.14 moved `Traversable` from `importlib.abc` to `collections.abc`. The `polyglot-hello` package (v0.1.3) still uses the old import location, causing:
```
ImportError: cannot import name 'Traversable' from 'importlib.abc'
```

**Solution**: Created a compatibility patch that monkey-patches the import before polyglot-hello is loaded.

**Files**:
- `_polyglot_patch.py` - Patches `importlib.abc.Traversable` by importing from `collections.abc`
- `.venv/lib/python3.14/site-packages/_flyte_py314_compat.pth` - Auto-loads the patch on interpreter startup

**How it works**:
1. The `.pth` file tells Python to import `_polyglot_patch` at startup
2. `_polyglot_patch` checks if `Traversable` is missing from `importlib.abc`
3. If missing, it imports from `collections.abc` and injects it
4. All downstream imports of `Traversable` work transparently

### 2. Missing Dependencies for Report Examples

**Issue**: The `4_reports/` examples require `numpy`, `plotly`, and `requests`, which weren't listed in dependencies.

**Fix**: Added to `pyproject.toml`:
```toml
dependencies = [
  "flyte>=2.0.0b14",
  "polyglot-hello>=0.1.3",
  "numpy",
  "plotly",
  "requests",
]
```

Then ran: `uv sync`

### 3. Local Testing Support

**Issue**: README didn't explain how to test without a Flyte cluster.

**Fix**: Updated README and all commands to use `--local` flag:
```bash
uv run flyte run --local <example> <task> [args...]
```

This runs tasks in the local Python environment without needing remote Flyte infrastructure.

## Quick Start

### Install Dependencies
```bash
uv sync
```

### Run Individual Examples
```bash
# Example 1: Hello Polyglot
uv run flyte run --local 1_hello_world/hello_polyglot.py main --letter e

# Example 2: Failure Handling
uv run flyte run --local 2_failure_handling/oomer.py failure_recovery

# Example 3: Agents
uv run flyte run --local 3_agents/smolagent.py main --goal "Make a peanut butter and jelly sandwich"

# Example 4: Reports
uv run flyte run --local 4_reports/run_all.py main
```

### Test All Examples
```bash
uv run python test_all_examples.py
```

This runs all 4 examples and provides a summary report.

## Environment Details

- **OS**: Fedora 43
- **Python**: 3.14.4
- **uv**: 0.10.12
- **Flyte**: 2.1.9

## Troubleshooting

### "No module named '_polyglot_patch'"
The patch wasn't copied to site-packages. Run:
```bash
cp _polyglot_patch.py .venv/lib/python3.14/site-packages/
```

### "cannot import name 'Traversable' from 'importlib.abc'"
The `.pth` file isn't being loaded. Check:
```bash
cat .venv/lib/python3.14/site-packages/_flyte_py314_compat.pth
```

Should contain: `import _polyglot_patch`

### "No module named 'numpy/plotly/requests'"
Re-run dependencies:
```bash
uv sync
```

## Fish Shell Compatibility

All commands work with fish shell. The main differences from bash:
- `&&` works the same
- Pipes `|` work the same  
- String quoting with `"` works the same

No fish-specific syntax is required for these examples.

## Demo Readiness

Run before your demo:
```bash
uv run python test_all_examples.py
```

If all tests pass (4/4 ✅), you're ready to present!

## Files Changed/Created

**Modified**:
- `pyproject.toml` - Added numpy, plotly, requests
- `README.md` - Updated to use `--local` flag and added Python 3.14 docs

**Created**:
- `_polyglot_patch.py` - Python 3.14 compatibility patch
- `test_all_examples.py` - Validation script for all examples
- `SETUP.md` (this file)

**Auto-Generated**:
- `.venv/lib/python3.14/site-packages/_flyte_py314_compat.pth` - Auto-load mechanism
- `.venv/lib/python3.14/site-packages/_polyglot_patch.py` - Copied from root
