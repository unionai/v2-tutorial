# Learn Flyte by driving your coding agent

This is a hands-on tutorial for people who already work with a coding agent
(Claude Code, Cursor, Copilot, Windsurf, Cline, Codex…). Instead of copying code
out of a README, **you'll paste prompts to your agent and watch it build real
Flyte pipelines for you** — grounded by the official Flyte MCP server so it
writes correct, current code. You'll run the pipelines yourself from the
terminal, so you learn the moving parts, not just the magic.

Two things you'll walk away with:

1. **The fundamentals.** The agent types the code, but *you* run the CLI and ask
   the agent to explain what it built — so you actually understand tasks,
   environments, parallelism, retries, reports, and deployment.
2. **A feel for the value.** You'll see Flyte run your Python in the cloud, fan
   it out in parallel, recover from failures, stream live reports, and deploy —
   and understand *why* each one matters.

⏱️ **Budget about an hour.** The first cloud run spends a few minutes building a
container image; later steps reuse it and are quick.

> **The one rule that makes this work:** your agent's exact output will differ
> every time — that's fine. We never check that your code looks a certain way.
> We check that *the right thing happened* (a run succeeded, work ran in
> parallel, a failure recovered). Each step ends with a **Checkpoint** you use
> to confirm you landed in the right place.

> **Who runs what:** the agent always writes the code. In the early steps **you**
> run the Flyte CLI yourself — that muscle memory matters. Once you've got it,
> you'll hand command-running back to the agent and let it run and verify things
> for you.

---

## Before you start

You need:

- **Python 3.10+** and a coding agent you're comfortable using.
- **Docker running** (only if you'll use the local devbox in Step 2).
- **This repo, cloned locally.** It ships the Flyte MCP configuration for every
  supported agent, so connecting in Step 1 is mostly done for you.

```bash
git clone <this-repo-url> v2-tutorial
cd v2-tutorial
```

Then install Flyte. Use whichever tool you prefer — pick one and stick with it:

**Option A — uv** (fast, no manual venv):

```bash
uv sync
```

**Option B — pip** (in a virtual environment):

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install flyte
```

> 🔧 **Running `flyte` commands in this tutorial.** Every `flyte ...` command
> below assumes Flyte is on your path. If you used **pip**, that means your venv
> is **activated** (`source .venv/bin/activate`). If you used **uv**, prefix each
> command with `uv run` — e.g. `uv run flyte get config`. Pick one habit and use
> it for every command in the tutorial.

---

## Step 1 — Connect the Flyte MCP (do this first)

The Flyte **MCP server** gives your agent live access to Flyte's docs and code
examples. This is what keeps the agent's output correct and consistent — without
it, agents guess at APIs. **Get this working before anything else.**

The server is remote and needs no login:

```
https://flyte-mcp.apps.demo.hosted.unionai.cloud/flyte-mcp/mcp
```

Find your agent below. For the agents that read repo-committed config
(Claude Code, Cursor, VS Code, Codex), the file is **already in this repo** —
you just open the project and approve it.

<details>
<summary><b>Claude Code</b></summary>

Already configured via [`.mcp.json`](.mcp.json) in this repo. Open the project
and Claude Code will prompt you to approve the `flyte` server. Or add it yourself:

```bash
claude mcp add --transport http --scope project flyte https://flyte-mcp.apps.demo.hosted.unionai.cloud/flyte-mcp/mcp
```
</details>

<details>
<summary><b>Cursor</b></summary>

Already configured via [`.cursor/mcp.json`](.cursor/mcp.json). Open the project,
then go to **Settings → Tools & Integrations / MCP** and enable **flyte**.
</details>

<details>
<summary><b>VS Code + GitHub Copilot</b></summary>

Already configured via [`.vscode/mcp.json`](.vscode/mcp.json). Open the project,
switch Copilot Chat to **Agent mode**, and start the **flyte** server when
prompted (or via the MCP servers list).
</details>

<details>
<summary><b>Codex CLI</b></summary>

A project-local [`.codex/config.toml`](.codex/config.toml) is included. If your
Codex setup doesn't pick it up, add it to `~/.codex/config.toml`:

```toml
[mcp_servers.flyte]
url = "https://flyte-mcp.apps.demo.hosted.unionai.cloud/flyte-mcp/mcp"
```
</details>

<details>
<summary><b>Windsurf</b></summary>

Windsurf only reads a global config, so add this to
`~/.codeium/windsurf/mcp_config.json` yourself (note the key is `serverUrl`):

```json
{
  "mcpServers": {
    "flyte": {
      "serverUrl": "https://flyte-mcp.apps.demo.hosted.unionai.cloud/flyte-mcp/mcp"
    }
  }
}
```
</details>

<details>
<summary><b>Cline</b></summary>

Cline stores MCP config globally. Open the Cline panel → **MCP Servers** →
**Configure**, and add (the `type` must be exactly `streamableHttp`):

```json
{
  "mcpServers": {
    "flyte": {
      "url": "https://flyte-mcp.apps.demo.hosted.unionai.cloud/flyte-mcp/mcp",
      "type": "streamableHttp"
    }
  }
}
```
</details>

### ✅ Checkpoint: prove the MCP is live

Paste this to your agent:

> Using the Flyte MCP server, search the Flyte docs and tell me what a
> `TaskEnvironment` is and what `@env.task` does. Quote where you found it.

If it answers with specifics pulled from Flyte's docs (not a vague guess),
**you're connected** and ready to build. If it can't reach the server, revisit
the config for your agent above.

---

## Step 2 — Connect to a backend

Your code runs on a Flyte backend. Pick one and create a config — **you** run
these commands.

**Option A — local devbox (fastest, no account):** a Flyte cluster on your own
machine. Make sure Docker is running, then:

```bash
flyte start devbox
flyte create config \
  --endpoint localhost:30080 \
  --project flytesnacks \
  --domain development \
  --builder local \
  --insecure \
  --output ~/.union/config.yaml
```

The devbox UI comes up at <http://localhost:30080>. Details:
<https://www.union.ai/docs/v2/flyte/user-guide/run-modes/running-devbox/>

**Option B — a remote Union cluster** (if you have one):

```bash
flyte create config \
  --endpoint <org>.hosted.unionai.cloud \
  --builder remote \
  --domain development \
  --org <org> \
  --project <project> \
  --output ~/.union/config.yaml
```

### ✅ Checkpoint: see what you're connected to

```bash
flyte get config
flyte whoami
```

`flyte get config` prints your active endpoint, org, project, and domain — read
it and make sure it points where you expect. If both commands answer cleanly,
your CLI is wired up.

---

## Step 3 — Run your Python in the cloud, unchanged

The core Flyte idea: write normal Python functions, mark them as tasks, and run
them on real infrastructure without rewriting anything.

**Prompt your agent:**

> Using the Flyte MCP for reference, create a file `hello.py` with a single
> Flyte task that takes a `name` string and returns a greeting, plus a `main`
> task that calls it. Set up a `TaskEnvironment` with a Debian-based image.
> Don't run it — just write the file and tell me the exact `flyte run` command
> to execute `main` with a name.

**Now you run it** (the agent gives you the exact line; it looks like this):

```bash
flyte run hello.py main --name World
```

The first run builds a container image — give it a few minutes. When it finishes,
the CLI prints an **execution URL**. Open it: that's your function running as a
tracked execution on the cluster.

### ✅ Checkpoint

The command should finish without error and print a URL. Open it and confirm the
execution shows **Succeeded**.

### 💡 Understand what just happened

> Explain, using the Flyte MCP, what `TaskEnvironment` and `@env.task` did here.
> Why did my plain Python function need an "environment" and an "image" to run
> in the cloud? Keep it to a few sentences.

---

## Step 4 — Scale it out, for free

You rarely run one thing. Flyte makes running the *same* task across many inputs
in parallel a one-liner — and each one is its own tracked, retryable unit.

**Prompt your agent:**

> Now add a task to `hello.py` that uses `flyte.map` to run my greeting task in
> parallel across a list of at least 8 names and returns all the greetings. Give
> me the `flyte run` command for it — I'll run it.

**You run it**, then open the execution URL it prints.

### ✅ Checkpoint

In the UI you should see **one child action per name**, not a single task looping.
Spot-check: did they run side by side?

### 💡 Understand what just happened

> Using the Flyte MCP, explain why `flyte.map` is better here than a plain Python
> `for` loop. What does Flyte give me — scaling, retries, visibility — that the
> loop wouldn't?

---

## Step 5 — Survive failure and control cost

Real pipelines hit transient errors and resource limits. Flyte treats retries
and resource sizing as first-class settings, and lets a task ask for *more*
resources only when it needs them.

**Prompt your agent:**

> Using the Flyte MCP, create `resilient.py` with a task that fails on its first
> attempt and then succeeds when Flyte retries it — detect the current retry
> attempt from what Flyte exposes to the task (ask the MCP how), so it works even
> though each retry runs in a fresh pod. Set `retries` so the task recovers. Add a
> second task that requests extra memory for just itself via a resource override.
> Give me the `flyte run` command.

> ℹ️ Reading the attempt number is the trick: a plain in-process counter resets
> on every retry because each attempt is a brand-new pod, so the task has to read
> the attempt number Flyte hands it.

**You run it.** This time, **let your agent help you verify** — paste:

> Run that `flyte run` command for me, then tell me how many attempts the flaky
> task made and whether the run ultimately succeeded.

### ✅ Checkpoint

The run succeeds *despite* early failed attempts. In the UI, the flaky task shows
multiple attempts ending in Succeeded.

### 💡 Understand what just happened

> Briefly: how do `retries` and resource overrides help me run cheaply and
> reliably? When would I override resources for one task instead of raising them
> everywhere?

---

## Step 6 — See inside your pipeline

Flyte tasks can emit rich, interactive **HTML reports** — charts, tables, live
progress — attached right to the execution. This is the observability story.

**Prompt your agent (and let it drive now):**

> Using the Flyte MCP, create `report.py` with a task that generates an
> interactive HTML report (a chart or live-updating dashboard) with
> `flyte.report`. Then run it for me and tell me where to view the report in the
> UI.

### ✅ Checkpoint

Open the execution and find the **report** tab — that visualization was produced
by your task and travels with the run.

---

## Step 7 — Deploy it

So far each `flyte run` uploaded your code on the spot. **`flyte deploy`**
registers your task environment on the backend as a named, reusable entity — the
foundation for running it on a schedule, triggering it from other systems, or
sharing it with teammates.

**Prompt your agent:**

> Using the Flyte MCP, explain the difference between `flyte run` and
> `flyte deploy`. Then deploy the environment from `hello.py` for me and confirm
> it registered, and show me where to find the deployed task in the UI.

### ✅ Checkpoint

Your agent reports a successful deploy, and you can find the deployed task/environment
in the UI without re-running from source.

---

## Step 8 — Now you drive

You've seen the whole arc: cloud execution, effortless parallelism, resilience,
observability, and deployment — and you've run the CLI yourself. Time to fish on
your own. Pick any of these and hand it to your agent, leaning on the Flyte MCP
and the checkpoint habit (*"prove it actually worked"*) you've built:

- *"Build a small multi-step pipeline where one task's output feeds the next,
  and the steps that can run in parallel do."*
- *"Take the map example and fan it out across 100 inputs, limiting how many run
  at once."*
- *"Write a pipeline that processes a public dataset and produces a report
  summarizing it."*
- *"Add a task that only runs on a larger machine, and prove from the UI it got
  the resources it asked for."*
- *"Recreate something from my own work as a Flyte pipeline, run it, and deploy
  it."*

For each: ask the agent to build it, run it (or run it yourself), **confirm from
the execution that it worked**, and when something surprises you, ask the agent
to explain it using the Flyte MCP.

---

## What's next?

- Browse real examples: https://github.com/flyteorg/flyte-sdk/tree/main/examples
- Latest from Union: https://www.union.ai/resources
- Ask questions on Slack: https://slack.flyte.org/
