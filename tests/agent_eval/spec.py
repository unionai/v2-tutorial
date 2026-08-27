"""The test spec: the exact README prompts, in order, plus what 'success' means.

Each prompt marked ``from_readme=True`` is checked against ../../README.md at
runtime (see ``verify_prompts_against_readme``) so the eval can never silently
drift from what the tutorial actually tells people to paste. A couple of turns
are marked ``from_readme=False``: those stand in for the human walking to their
terminal and running a command — in an automated run the worker does it instead.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re

README = pathlib.Path(__file__).resolve().parents[2] / "README.md"


@dataclasses.dataclass
class Prompt:
    kind: str  # "build" | "explain" | "verify" | "checkpoint" | "run"
    text: str
    from_readme: bool = True


@dataclasses.dataclass
class Step:
    number: int
    title: str
    prompts: list[Prompt]
    working_result: str  # what the judge should look for as a working outcome
    clear_answer: str | None = None  # what a clear explanation must contain (if any)


# A standard "now run it" turn for the steps where the README hands the command
# to the human. The worker performs it because there is no human in the loop.
def _run_it(target: str) -> Prompt:
    return Prompt(
        kind="run",
        from_readme=False,
        text=(
            f"Go ahead and run that command now using your shell to {target}. "
            "Flyte may build a container image first, so allow several minutes "
            "(set your Bash timeout to the maximum). When it finishes, paste the "
            "execution URL and tell me the final status (did it Succeed?)."
        ),
    )


STEPS: list[Step] = [
    Step(
        number=1,
        title="Connect the Flyte MCP",
        prompts=[
            Prompt(
                kind="checkpoint",
                text=(
                    "Using the Flyte MCP server, search the Flyte docs and tell me "
                    "what a `TaskEnvironment` is and what `@env.task` does. Quote "
                    "where you found it."
                ),
            ),
        ],
        working_result="The agent actually called a Flyte MCP tool (mcp__flyte__*) to look this up.",
        clear_answer="A correct, specific explanation of TaskEnvironment and @env.task, with a citation/quote from the docs.",
    ),
    Step(
        number=3,
        title="Run your Python in the cloud",
        prompts=[
            Prompt(
                kind="build",
                text=(
                    "Using the Flyte MCP for reference, create a file `hello.py` with "
                    "a single Flyte task that takes a `name` string and returns a "
                    "greeting, plus a `main` task that calls it. Set up a "
                    "`TaskEnvironment` with a Debian-based image. Don't run it — just "
                    "write the file and tell me the exact `flyte run` command to "
                    "execute `main` with a name."
                ),
            ),
            _run_it("execute the hello.py main task"),
            Prompt(
                kind="explain",
                text=(
                    'Explain, using the Flyte MCP, what `TaskEnvironment` and '
                    '`@env.task` did here. Why did my plain Python function need an '
                    '"environment" and an "image" to run in the cloud? Keep it to a '
                    "few sentences."
                ),
            ),
        ],
        working_result="hello.py was written and a real execution of `main` ran on the backend and Succeeded.",
        clear_answer="A concise, correct explanation of what TaskEnvironment and @env.task do and why an image/environment is needed.",
    ),
    Step(
        number=4,
        title="Scale it out with flyte.map",
        prompts=[
            Prompt(
                kind="build",
                text=(
                    "Now add a task to `hello.py` that uses `flyte.map` to run my "
                    "greeting task in parallel across a list of at least 8 names and "
                    "returns all the greetings. Give me the `flyte run` command for "
                    "it — I'll run it."
                ),
            ),
            _run_it("execute the new map task"),
            Prompt(
                kind="explain",
                text=(
                    "Using the Flyte MCP, explain why `flyte.map` is better here than "
                    "a plain Python `for` loop. What does Flyte give me — scaling, "
                    "retries, visibility — that the loop wouldn't?"
                ),
            ),
        ],
        working_result="A map execution ran and Succeeded, producing one greeting per input name (fan-out).",
        clear_answer="A correct explanation of why flyte.map beats a for loop (parallelism, per-item retries, visibility).",
    ),
    Step(
        number=5,
        title="Survive failure and control cost",
        prompts=[
            Prompt(
                kind="build",
                text=(
                    "Using the Flyte MCP, create `resilient.py` with a task that "
                    "fails on its first attempt and then succeeds when Flyte retries "
                    "it — detect the current retry attempt from what Flyte exposes to "
                    "the task (ask the MCP how), so it works even though each retry "
                    "runs in a fresh pod. Set `retries` so the task recovers. Add a "
                    "second task that requests extra memory for just itself via a "
                    "resource override. Give me the `flyte run` command."
                ),
            ),
            Prompt(
                kind="verify",
                text=(
                    "Run that `flyte run` command for me, then tell me how many "
                    "attempts the flaky task made and whether the run ultimately "
                    "succeeded."
                ),
            ),
            Prompt(
                kind="explain",
                text=(
                    "Briefly: how do `retries` and resource overrides help me run "
                    "cheaply and reliably? When would I override resources for one "
                    "task instead of raising them everywhere?"
                ),
            ),
        ],
        working_result="The flaky task failed its first attempt but the run ultimately Succeeded via retries.",
        clear_answer="A correct explanation of retries + per-task resource overrides and when to use them.",
    ),
    Step(
        number=6,
        title="See inside your pipeline (reports)",
        prompts=[
            Prompt(
                kind="build",
                text=(
                    "Using the Flyte MCP, create `report.py` with a task that "
                    "generates an interactive HTML report (a chart or live-updating "
                    "dashboard) with `flyte.report`. Then run it for me and tell me "
                    "where to view the report in the UI."
                ),
            ),
        ],
        working_result="report.py ran and Succeeded, and the agent points to where the HTML report is viewable.",
    ),
    Step(
        number=7,
        title="Deploy it",
        prompts=[
            Prompt(
                kind="build",
                text=(
                    "Using the Flyte MCP, explain the difference between `flyte run` "
                    "and `flyte deploy`. Then deploy the environment from `hello.py` "
                    "for me and confirm it registered, and show me where to find the "
                    "deployed task in the UI."
                ),
            ),
        ],
        working_result="A `flyte deploy` of hello.py's environment succeeded / registered on the backend.",
        clear_answer="A correct explanation of the difference between flyte run and flyte deploy.",
    ),
    Step(
        number=8,
        title="Now you drive (open-ended)",
        prompts=[
            Prompt(
                kind="build",
                text=(
                    "Build a small multi-step pipeline where one task's output feeds "
                    "the next, and the steps that can run in parallel do."
                ),
            ),
            _run_it("run the multi-step pipeline"),
        ],
        working_result="A multi-step pipeline with a real data dependency was built and ran to Succeeded on the backend.",
    ),
]


def _normalize(text: str) -> str:
    """Strip blockquote markers and collapse whitespace for robust matching."""
    text = re.sub(r"(?m)^\s*>\s?", "", text)  # drop '> ' blockquote prefixes
    return re.sub(r"\s+", " ", text).strip()


def verify_prompts_against_readme() -> list[str]:
    """Return a list of prompts (from_readme=True) NOT found verbatim in README."""
    readme_norm = _normalize(README.read_text(encoding="utf-8"))
    missing = []
    for step in STEPS:
        for p in step.prompts:
            if p.from_readme and _normalize(p.text) not in readme_norm:
                missing.append(f"Step {step.number} [{p.kind}]: {p.text[:70]}…")
    return missing
