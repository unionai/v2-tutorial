"""The judge: an independent LLM verdict on whether a step worked.

Given the worker's transcript for one step plus a few deterministic signals
(did it call the Flyte MCP? did an execution URL appear? any error text?), the
judge returns a strict JSON verdict on two axes: did the customer get a
*working result*, and (where relevant) a *clear answer*.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .spec import Step
from .worker import Turn

EXEC_URL_RE = re.compile(r"https?://[^\s)\"']*unionai\.cloud[^\s)\"']*")
ERROR_RE = re.compile(r"\b(Traceback|FAILED|Error:|Exception|non-zero exit)\b", re.IGNORECASE)

JUDGE_SYSTEM = (
    "You are a strict QA reviewer for a Flyte tutorial. You judge whether a "
    "customer following the tutorial got real, working results from their coding "
    "agent — not whether the code looks a certain way. Be skeptical: a claim of "
    "success without evidence (an execution URL, a succeeded status, or tool "
    "output) is NOT a working result. Reply with JSON only."
)


def _signals(turns: list[Turn]) -> dict[str, Any]:
    all_tool_names = [t["name"] for turn in turns for t in turn.tool_calls]
    blob = "\n".join(turn.text for turn in turns) + "\n".join(
        r for turn in turns for r in turn.tool_results
    )
    return {
        "called_flyte_mcp": any(n.startswith("mcp__flyte__") for n in all_tool_names),
        "ran_bash": any(n == "Bash" for n in all_tool_names),
        "execution_urls": sorted(set(EXEC_URL_RE.findall(blob)))[:5],
        "error_text_present": bool(ERROR_RE.search(blob)),
        "tool_names": all_tool_names,
    }


def _render(step: Step, turns: list[Turn], signals: dict[str, Any]) -> str:
    lines = [f"# Step {step.number}: {step.title}", ""]
    lines.append(f"Working result means: {step.working_result}")
    if step.clear_answer:
        lines.append(f"Clear answer means: {step.clear_answer}")
    lines += ["", "## Deterministic signals", json.dumps(signals, indent=2), "", "## Transcript"]
    for turn in turns:
        lines.append(f"\n### Customer said:\n{turn.prompt}")
        if turn.tool_calls:
            lines.append("Worker tools: " + ", ".join(t["name"] for t in turn.tool_calls))
        for r in turn.tool_results[:8]:
            lines.append("Tool output (truncated):\n" + r[:1500])
        lines.append(f"Worker answered:\n{turn.text[:4000]}")
    return "\n".join(lines)


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {"working_result": False, "clear_answer": None, "summary": "judge returned no JSON", "raw": text[:500]}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {"working_result": False, "clear_answer": None, "summary": "judge JSON parse error", "raw": text[:500]}


async def judge_step(step: Step, turns: list[Turn], model: str = "sonnet") -> dict[str, Any]:
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    signals = _signals(turns)
    needs_answer = step.clear_answer is not None
    clear_field = "true/false" if needs_answer else "null"
    answer_note = (
        "'clear_answer' judges the explanation quality (true/false)."
        if needs_answer
        else "This step has no explanation to grade; set clear_answer to null."
    )
    instruction = (
        _render(step, turns, signals)
        + "\n\n## Your verdict\n"
        + "Return JSON exactly like:\n"
        + "{\n"
        + '  "working_result": true/false,\n'
        + '  "clear_answer": ' + clear_field + ",\n"
        + '  "evidence": "the execution URL / status / tool output that proves it (or what was missing)",\n'
        + '  "summary": "one sentence"\n'
        + "}\n"
        + "'working_result' is true ONLY if there is concrete evidence the described outcome happened.\n"
        + answer_note
    )

    options = ClaudeAgentOptions(model=model, system_prompt=JUDGE_SYSTEM, allowed_tools=[], max_turns=1)
    out: list[str] = []
    async for msg in query(prompt=instruction, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    out.append(block.text)

    verdict = _parse_json("".join(out))
    verdict["signals"] = signals
    return verdict
