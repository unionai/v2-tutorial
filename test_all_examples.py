#!/usr/bin/env python
"""
Test script to validate all Flyte v2 tutorial examples.
Runs on Fedora 43 with Python 3.14+ support.
"""
import subprocess
import sys
from pathlib import Path

# Auto-apply Python 3.14 compatibility patch
import _polyglot_patch  # noqa: F401

def run_example(name: str, file: str, task: str, args: list = None) -> bool:
    """Run a single example and report results."""
    args = args or []
    cmd = ["uv", "run", "flyte", "run", "--local", file, task] + args
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=False, timeout=120)
        success = result.returncode == 0
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status}: {name}")
        return success
    except subprocess.TimeoutExpired:
        print(f"\n⏱️ TIMEOUT: {name}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {name} - {e}")
        return False


def main():
    """Run all tutorial examples."""
    print("\n" + "🚀" * 30)
    print("Flyte v2 Tutorial - All Examples Test")
    print("🚀" * 30)
    
    examples = [
        ("Hello Polyglot", "1_hello_world/hello_polyglot.py", "main", ["--letter", "e"]),
        ("Failure Handling", "2_failure_handling/oomer.py", "failure_recovery", []),
        ("Agents/Sandwich", "3_agents/smolagent.py", "main", ["--goal", "Make a peanut butter and jelly sandwich"]),
        ("Reports Bundle", "4_reports/run_all.py", "main", []),
    ]
    
    results = {}
    for name, file, task, args in examples:
        results[name] = run_example(name, file, task, args)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for demo.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
