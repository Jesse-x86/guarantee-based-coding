# GBC Interactive Demo (for Agents, English)

English parallel of the Chinese walkthrough in [`EXAMPLE.md`](./EXAMPLE.md).
Uses project `config-service-en` and scenarios `config-service-*-en`.

**You are human** → hand this doc to your coding agent and say: "Walk through this step by step; pause and explain after each step."

**You are an agent** → Hi. Your job is an interactive GBC demo so your human can see how it works.
Three scenes: strong test catches a break → weak test misses it → a bad test is refused at
born-green. Pause after each step, explain, wait for confirmation before continuing.

## Prep: make sure GBC is available

Confirm the GBC MCP server is wired in. If not:

1. Your human has cloned the `guarantee-based-coding` repo. Find it.
2. `pip install -r requirements.txt` into a suitable Python environment.
3. Start the MCP server with `gbc mcp up <project-root>` (interpreter from step 2), then register it in `.mcp.json`.

> Details: [docs/for-agents.md](../docs/for-agents.md).

Tools you need: `create_guarantee`, `add_dependency`, `verify_provider`, `upsert_executor`.

Demo assets:
- Project source (read-only — do not edit): `demo/projects/config-service-en/`
- Tests (read-only): `demo/scenarios/<name>/tests/`

## Workspace management

The demo **never** edits files under `demo/` directly — those are read-only templates. Every step
runs in a separate workspace.

Pick a workspace location (e.g. this repo's `demo/workspace/` or a temp dir) and follow:

- **Round 1 (step 2)**: create the workspace; **copy** `config_loader.py` and `server.py` from
  `demo/projects/config-service-en/` to the workspace root. **Copy**
  `demo/scenarios/config-service-strong-en/tests/test_never_none.py` into `workspace/tests/` (create the dir).
- **Round 2 (step 3)**: **wipe** the workspace, re-copy the source, but take the test from
  `demo/scenarios/config-service-weak-en/tests/`.
- **Round 3 (step 4)**: **wipe** again, re-copy source, test from
  `demo/scenarios/config-service-bad-test-en/tests/`.

> All sources are **copied**, never moved — templates under `demo/` must stay untouched.

---

## Step 1: show the code

Open `config_loader.py` and explain:

> `get_config(key)` always returns str — missing keys yield `""`, not `None`.
> The `.get(key, "")` line is that promise.

Open `server.py`:

> Downstream `int(get_config("port"))` trusts it never to be None. If it ever returned None,
> `int(None)` → TypeError.

**Wait until your human follows.**

---

## Step 2: strong test — the gate catches (core demo)

Use `demo/scenarios/config-service-strong-en/tests/test_never_none.py`.

Open the test and explain:

> Two asserts: `get_config("port")` is not None **and** `get_config("nonexistent")` is not None.
> The second covers the edge path — that is what makes it "strong".

Then:

1. **Register executor**: `upsert_executor`, config_name=`demo-pytest`. command = current Python
   `-m pytest {file} -x -q`, cwd and PYTHONPATH point at the workspace.
2. **Register guarantee**: `create_guarantee`, provider=`config_loader.py`,
   id=`config_loader.get_config.never_none`, with the copied test. **This runs the test on the spot —
   show PASS and explain born-green.**
3. **Register dependency**: `add_dependency`, consumer=`server.py`, provider=`config_loader.py`,
   symbol=`get_config`, guarantee_id=`config_loader.get_config.never_none`.
4. **Baseline verify**: `verify_provider config_loader.py` → should be **GREEN**.
   "All guarantees pass; the code is healthy."
5. **Simulate the break**: change `config_loader.py` `.get(key, "")` → `.get(key)` (drop the default).
   **Show the diff** — "missing keys now return None — a "harmless" simplify."
6. **Re-verify**: `verify_provider config_loader.py` → should be **RED**.

Explain:
> `get_config("nonexistent")` is now None; the strong test's second assert catches it. The gate
> goes red — in a real project the agent would be blocked from landing this change.

**That is the core of GBC. Let it sink in.**

---

## Step 3: weak test — contrast, the gate misses

Wipe the workspace and re-copy source. This time use
`demo/scenarios/config-service-weak-en/tests/test_never_none.py`.

Open the test:

> One assert only: `get_config("port")` is not None. No `get_config("nonexistent")`.
> The missing-key branch is outside coverage.

Repeat all of step 2 (executor → guarantee → dependency → baseline → same edit → re-verify).

The last step should stay **GREEN** — the edit helped over the gate.

Explain:
> The weak test only covers the productive path. `get_config("port")` always returns `"8080"`, so
> the test always passes. Meanwhile `get_config("nonexistent")` quietly went from `""` to `None` —
> the test never looked.
>
> **Takeaway: the gate is only as strong as the test coverage.**

---

## Step 4 (optional): bad test — born-green refuses

Wipe the workspace. Use `demo/scenarios/config-service-bad-test-en/tests/test_never_none.py`
(deliberately wrong — asserts `get_config("nonexistent") == "default"`, code returns `""`).

Call `create_guarantee` directly — it should **fail** with a pytest assertion error.

Explain:
> GBC does not only catch breaks after edits — it requires the test itself to be honest at
> **registration**. A guarantee that cannot register never enters the system. First line of defense.

---

## Wrap-up

Three points for your human:
1. **GBC turns tests into a gate**: edit → run guarantees → land only when green
2. **Gate strength = test strength**: untested edges are blind to the gate
3. **Born-green**: the test runs the moment a guarantee is registered — bad tests never enter

Then: want GBC in your own project → hand them [docs/for-agents.md](../docs/for-agents.md).
