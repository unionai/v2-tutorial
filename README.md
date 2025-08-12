# v2-tutorial
A tutorial to introduce users to Flyte v2 features through examples

## Quick start

Prereqs: Python 3.10+.

### Option A: uv (recommended)

If you don't have `uv`:

```
curl -fsSL https://astral.sh/uv/install.sh | sh
```

Then create a virtualenv and install deps with `uv`:

```
uv venv .venv
source .venv/bin/activate
uv pip install "flyte>=2.0.0b6" "polyglot-hello>=0.1.2"

# Run via Flyte CLI
flyte run 1_hello_world/hello_polyglot.py main --letter p
```

### Option B: pip

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install "flyte>=2.0.0b6" "polyglot-hello>=0.1.2"

# Run the dynamic hello example via Flyte CLI
flyte run 1_hello_world/hello_polyglot.py main --letter p
```

Notes:
- The example fans out one task per language code whose code starts with the provided letter, using `polyglot-hello`.
- Adjust the letter as desired (e.g., `e`, `s`, `f`).
- Ensure your Flyte CLI is configured for your project/domain. You can pass `-p <project> -d <domain>` to the command if needed.

