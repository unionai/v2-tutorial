"""Run the agent-vs-agent tutorial eval.

    uv run python -m tests.agent_eval.run_eval               # full pass, all steps
    uv run python -m tests.agent_eval.run_eval --steps 1     # just step 1 (smoke)
    uv run python -m tests.agent_eval.run_eval --steps 1,3,4 # a subset

The customer (this script) drives a worker coding agent through the exact
README prompts; a judge decides per step whether we got a working result and a
clear answer. Exits non-zero if any selected step's working_result is false.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import subprocess
import sys
import tempfile
import time

from .judge import judge_step
from .spec import STEPS, verify_prompts_against_readme
from .worker import ClaudeAgentSDKWorker

RUNS_DIR = pathlib.Path(__file__).resolve().parent / "runs"


def _check_backend() -> tuple[bool, str]:
    """Step 2 precondition: confirm a Flyte backend is configured."""
    try:
        out = subprocess.run(
            ["flyte", "get", "config"], capture_output=True, text=True, timeout=60
        )
        ok = out.returncode == 0 and "endpoint" in (out.stdout + out.stderr).lower()
        return ok, (out.stdout + out.stderr).strip()[:600]
    except Exception as exc:  # noqa: BLE001
        return False, f"could not run `flyte get config`: {exc}"


async def _run(selected: list[int], worker_model: str, judge_model: str) -> int:
    missing = verify_prompts_against_readme()
    if missing:
        print("✗ These prompts no longer match README.md — sync the spec:")
        for m in missing:
            print("   " + m)
        return 2
    print("✓ All README-sourced prompts match README.md verbatim.")

    backend_ok, backend_info = _check_backend()
    print(f"\n[Step 2] Backend check: {'✓' if backend_ok else '✗'}")
    print("   " + backend_info.replace("\n", "\n   "))
    if not backend_ok:
        print("✗ No Flyte backend configured. Run `flyte create config ...` first.")
        return 2

    steps = [s for s in STEPS if s.number in selected]
    workdir = tempfile.mkdtemp(prefix="flyte-tutorial-eval-")
    print(f"\nWorker scratch dir: {workdir}")
    print(f"Worker model: {worker_model} | Judge model: {judge_model}")
    print(f"Driving {len(steps)} step(s): {[s.number for s in steps]}\n")

    results = []
    started = time.time()
    async with ClaudeAgentSDKWorker(cwd=workdir, model=worker_model) as worker:
        for step in steps:
            print(f"━━━ Step {step.number}: {step.title} ━━━")
            turns = []
            for prompt in step.prompts:
                tag = "customer↦worker" if prompt.from_readme else "customer runs it"
                print(f"  • [{prompt.kind}/{tag}] {prompt.text[:72]}…")
                turn = await worker.run_turn(prompt.text)
                tools = ", ".join(t["name"] for t in turn.tool_calls) or "(no tools)"
                print(f"      tools: {tools}")
                turns.append(turn)

            verdict = await judge_step(step, turns, model=judge_model)
            wr = verdict.get("working_result")
            ca = verdict.get("clear_answer")
            mark = "✓" if wr else "✗"
            ca_str = "" if ca is None else f" | clear_answer: {'✓' if ca else '✗'}"
            print(f"  ⇒ working_result: {mark}{ca_str}")
            print(f"     {verdict.get('summary', '')}\n")
            results.append({"step": step.number, "title": step.title, "verdict": verdict})

    elapsed = time.time() - started

    # Report
    print("=" * 64)
    print("RESULTS")
    print("=" * 64)
    passed = 0
    for r in results:
        v = r["verdict"]
        wr = v.get("working_result")
        ca = v.get("clear_answer")
        passed += 1 if wr else 0
        line = f"{'PASS' if wr else 'FAIL'}  Step {r['step']:>1}  {r['title']}"
        if ca is not None:
            line += f"   (answer: {'clear' if ca else 'unclear'})"
        print(line)
    print("-" * 64)
    print(f"{passed}/{len(results)} steps produced a working result in {elapsed:.0f}s")

    RUNS_DIR.mkdir(exist_ok=True)
    out_path = RUNS_DIR / f"run-{int(started)}.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Full transcript verdicts: {out_path}")

    return 0 if passed == len(results) else 1


def main() -> None:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # flush progress live when piped to a file
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description="Agent-vs-agent tutorial eval")
    parser.add_argument("--steps", default="all", help="comma list of step numbers, or 'all'")
    parser.add_argument("--worker-model", default="sonnet")
    parser.add_argument("--judge-model", default="sonnet")
    args = parser.parse_args()

    all_nums = [s.number for s in STEPS]
    selected = all_nums if args.steps == "all" else [int(x) for x in args.steps.split(",")]

    rc = asyncio.run(_run(selected, args.worker_model, args.judge_model))
    sys.exit(rc)


if __name__ == "__main__":
    main()
