"""The worker: a coding agent under test, driven one prompt at a time.

`Worker` is a tiny protocol so the worker is swappable — the default
implementation uses the Claude Agent SDK, but a Cursor/Codex/etc. driver could
implement the same `run_turn` interface and the rest of the harness wouldn't
change.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Protocol, runtime_checkable

FLYTE_MCP_URL = "https://flyte-mcp.apps.demo.hosted.unionai.cloud/flyte-mcp/mcp"

WORKER_SYSTEM_PROMPT = """\
You are a software developer following a hands-on Flyte tutorial inside a fresh \
project directory. A Flyte backend is already configured (verify with \
`flyte get config`) and the `flyte` CLI is on your PATH.

Rules:
- You have a Flyte MCP server named "flyte". ALWAYS use it to look up Flyte APIs \
and examples before writing Flyte code — do not guess at the API.
- When the user asks you to run something (or to confirm a run succeeded), \
actually run it with the Bash tool, wait for it to finish, and report the \
execution URL and final status.
- Flyte runs may build a container image and take several minutes. When you run \
`flyte` commands, set the Bash tool timeout to its maximum and be patient.
- Run each pipeline AT MOST TWICE. Never re-run a command repeatedly to chase a \
different (random/nondeterministic) outcome — if it ran, report what actually \
happened, even if it isn't what you expected.
- Keep prose answers concise and concrete.
"""


@dataclasses.dataclass
class Turn:
    prompt: str
    text: str
    tool_calls: list[dict[str, Any]]
    tool_results: list[str]
    cost_usd: float | None = None


@runtime_checkable
class Worker(Protocol):
    async def __aenter__(self) -> "Worker": ...
    async def __aexit__(self, *exc: Any) -> None: ...
    async def run_turn(self, prompt: str) -> Turn: ...


def _stringify(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(getattr(item, "text", str(item)))
        return "\n".join(parts)
    return str(content)


class ClaudeAgentSDKWorker:
    """Worker backed by claude-agent-sdk, holding one session across all turns."""

    def __init__(self, cwd: str, model: str = "sonnet", max_turns: int = 60):
        from claude_agent_sdk import ClaudeAgentOptions

        self._options = ClaudeAgentOptions(
            cwd=cwd,
            model=model,
            system_prompt=WORKER_SYSTEM_PROMPT,
            mcp_servers={"flyte": {"type": "http", "url": FLYTE_MCP_URL}},
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "mcp__flyte__*"],
            permission_mode="bypassPermissions",
            max_turns=max_turns,
        )
        self._client = None

    async def __aenter__(self) -> "ClaudeAgentSDKWorker":
        from claude_agent_sdk import ClaudeSDKClient

        self._client = ClaudeSDKClient(options=self._options)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client is not None:
            await self._client.__aexit__(*exc)

    async def run_turn(self, prompt: str) -> Turn:
        from claude_agent_sdk import (
            AssistantMessage,
            ResultMessage,
            TextBlock,
            ToolUseBlock,
        )

        assert self._client is not None
        await self._client.query(prompt)

        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        tool_results: list[str] = []
        cost_usd: float | None = None

        async for msg in self._client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_calls.append({"name": block.name, "input": block.input})
            else:
                # User/tool-result messages carry tool outputs as blocks with .content
                content = getattr(msg, "content", None)
                if isinstance(content, list):
                    for block in content:
                        result = getattr(block, "content", None)
                        if result is not None and not isinstance(block, TextBlock):
                            tool_results.append(_stringify(result))
            if isinstance(msg, ResultMessage):
                cost_usd = getattr(msg, "total_cost_usd", None)
                break

        return Turn(
            prompt=prompt,
            text="".join(text_parts),
            tool_calls=tool_calls,
            tool_results=tool_results,
            cost_usd=cost_usd,
        )
