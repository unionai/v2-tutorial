# Agent-vs-agent tutorial eval

This is the test for the tutorial. It doesn't check that any particular code was
written — it checks that **following the README actually works**: a *customer*
(the harness) drives a *worker* coding agent through the exact prompts in
[`../../README.md`](../../README.md), with the Flyte MCP connected and a real
backend, and a *judge* decides per step whether we got a **working result** and a
**clear answer**.

```
customer (this harness)  ──prompts──▶  worker agent (Flyte MCP + shell + backend)
                                              │
                                       transcript
                                              ▼
                                         judge (LLM verdict: working? clear?)
```

The worker runs in a throwaway scratch directory, so it generates `hello.py`,
`resilient.py`, etc. fresh every time — there are **no example pipelines
committed to this repo**, by design.

## Layout

| File | Role |
|------|------|
| `spec.py` | The exact README prompts (verified against README.md at runtime) + what "success" means per step. |
| `worker.py` | The worker. `Worker` is a swappable protocol; the default is a `claude-agent-sdk` driver. |
| `judge.py` | Independent LLM verdict per step, backed by deterministic signals (MCP used? execution URL? errors?). |
| `run_eval.py` | The customer/orchestrator: runs the steps, prints a report, writes verdicts to `runs/`. |

## Running it

Prerequisites:
- A Flyte backend configured (`flyte get config` must succeed). The eval uses
  whatever you're pointed at — a devbox is cheapest.
- Credentials for the agent runtime (the Claude Agent SDK uses your Claude
  Code login / `ANTHROPIC_API_KEY`).

```bash
uv sync                                              # installs claude-agent-sdk
uv run python -m tests.agent_eval.run_eval --steps 1 # smoke: just prove MCP connects
uv run python -m tests.agent_eval.run_eval           # full pass (real cloud runs; slow)
```

A full pass triggers several real executions (and a first-time image build), so
expect it to take a while and to cost both agent tokens and compute. Start with
`--steps 1`, then `--steps 1,3,4`, then the full run.

## Swapping the worker

The harness only needs an object implementing `worker.Worker`
(`async run_turn(prompt) -> Turn`). To validate the tutorial against a different
coding agent (Cursor, Codex, …), implement that protocol around its CLI/SDK and
pass it into `run_eval` — nothing else changes. The tutorial is agent-agnostic;
this keeps the test agent-agnostic too.

## Notes

- Most steps assign the `flyte run` command to *the human*. With no human in the
  loop, the harness adds a "now run it" turn so the worker executes it — the one
  necessary automation divergence from the printed tutorial.
- `runs/` (verdict transcripts) is git-ignored.
