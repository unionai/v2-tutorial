#!/usr/bin/env python
"""
Wrapper to run flyte examples with Python 3.14+ compatibility.
Applies the Traversable import patch before running examples.
"""
import sys
import _polyglot_patch  # noqa: F401
import subprocess

# Re-run the original command without this wrapper
if __name__ == "__main__":
    # Skip the first argument (the script name) and pass remaining args to flyte
    exit_code = subprocess.run([sys.executable, "-m", "flyte.cli"] + sys.argv[1:]).returncode
    sys.exit(exit_code)
