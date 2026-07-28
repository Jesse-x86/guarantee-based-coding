# GBC Manual: Manual Setup + Working Under GBC

**中文版: [manual.md](./manual.md)**

> **This is GBC's manual / detailed reference.** If you want **automatic** setup, have your agent
> install per [for-agents.md](./for-agents.md) and run the `setup-gbc` skill — it does §1–5 below
> for you interactively. This document is the full reference for **installing by hand, step by
> step** (§1–5), and for **how to work safely under GBC once you're set up** (§6–8).
>
> The whole thing is written as if talking to an agent — a human can read it the same way, or hand
> it straight to an agent you trust. It's written for the "normal / recommended" case; adjust what
> the agent does itself versus what is left for a human to decide according to the permission split
> you and your human have agreed on.

GBC turns "will this change break something elsewhere?" from a guess into a mechanically verifiable
boolean: dependencies are explicitly registered as **guarantees**, each guarantee is backed by a
narrow test; you make your change, run the guarantees, and all-green = safe, any-red = a precise
report of who you broke.

---

## 1. Install

GBC runs in **its own** Python environment (separate from the project you're currently working on).
From the GBC repo:

```bash
pip install -r requirements.txt   # typer[all] / pydantic / mcp
```

> In the normal case, installing the environment is best left to a human; once it's installed,
> continue.

## 2. Wire up MCP (your guarantee-side tools)

Put a `.mcp.json` at the **root of the project you're working on**:

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/abs/path/to/python",
      "args": ["/abs/path/to/guarantee-based-coding/serve.py", "/abs/path/to/your-project"]
    }
  }
}
```

- `command` = the interpreter you installed the dependencies into in step 1.
- `args[0]` = absolute path to `serve.py`; `args[1]` = **absolute path to the working project root**
  (must be passed as argv, not via an environment variable).
- After restarting the agent, the tools appear as `mcp__gbc__*`.
- Calling Windows Python from WSL has cross-platform pitfalls (paths/encoding); `serve.py` already
  handles them — see [integrate-mcp_EN.md](./integrate-mcp_EN.md) for details.

## 3. Define an executor (how tests are run)

Before creating any guarantee, tell GBC what command runs tests. Call `upsert_executor`:

```jsonc
// config_name: "pytest"
// config_data:
{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],  // {file} is replaced with the test selector
  "cwd": "/abs/path/to/your-project",
  "timeout": 30,
  "env_ops": [{"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your-project"}]
}
```

To switch languages, just swap `command` (e.g. `["npx","jest","{file}"]`). `env_ops` actions:
`set` / `append` / `prepend` / `remove`.

## 4. Wrap the intent CLI as a skill (your only entry for changing intent)

Each folder's intent lives in `.gbc/<path>/gbc.md`, in three sections: **`# 意图` (Intent)** (what
it is, why), **`# 内部约束` (Internal constraints)** (obligations and rules: what it needs, what it
must or must not do), and **`# 文件` (Files)** (one line each for subfolders and files). Its
structure, and the consistency between parent and child documents, are kept by a program — so
**always edit through GBC's own intent CLI (`gbc_doc.py`); don't hand-edit gbc.md**, so the
constraint tooling guards them for you. What goes in each of the three sections, plus the spec-first
details, are in [intent-editor-and-skills_EN.md](./intent-editor-and-skills_EN.md). Below, wrap that CLI
as a thin skill:

**wrapper** (pins the interpreter + project root, passes the rest through):

```bash
#!/usr/bin/env bash
exec /abs/path/to/python \
  /abs/path/to/guarantee-based-coding/tools/intent-editor/backend/gbc_doc.py \
  --root /abs/path/to/your-project "$@"
```

**SKILL.md** (so you know when to use it):

```markdown
---
name: gbc-doc
description: The only compliant entry for reading/writing .gbc intent docs (gbc.md). Use this skill to view/create/change/lint gbc.md — NEVER hand-edit gbc.md.
---
Invoke: `bash /abs/path/to/gbc-doc.sh <command> [args...]`
Commands: show / set-intent / set-constraints / set-file / rm-entry / check / sync / migrate
(command surface in §6; for architecture work a human can also run `python gbc_doc.py`'s web editor — see intent-editor-and-skills_EN.md)
```

**Reference code with `[[project-relative-path]]`.** When gbc.md prose points at a code file or
symbol, write it as `[[app/core/models/game.py]]` or `[[app/core/models/game.py:GameSpec]]` — a path
from the repo root, wrapped in `[[ ]]`. Don't use `../` relative paths: a relative ref breaks when
either side moves and reads differently from each referrer, whereas a `[[ ]]` ref is one canonical
string per target that the `refactor_file` / `refactor_func` tools rewrite automatically when the
target moves. (Data directories, HTTP routes, and ADR links don't need `[[ ]]`.)

## 5. Smoke test: confirm it's connected

Call a read-only tool or two:

- `check_consistency()` → returns `[]` when the `.gbc` graph is consistent (an empty project is also
  `[]`).
- `list_provides("<relative path of some source file>")` → returns the guarantees registered for
  that file (or `{}` if none).

> Path arguments are always **project-root-relative** posix paths (`app/core/maker/maker.py`), not
> absolute paths. If it's not connecting, go back and re-check step 2.

---

## 6. Tool quick-reference

**Guarantee side (gbc MCP, `mcp__gbc__*`):**

| Tool | What it does |
|------|--------------|
| `add_dependency(provider, consumer, symbol[, guarantee_id])` | Register a dependency. Passing `guarantee_id` = a behavior dependency (auto-writes the reverse edge); omitting it = a free symbol dependency |
| `create_guarantee(provider, id, desc, test, executor[, heavy, disabled])` | Create a named guarantee. **Born-green: runs the test at creation and refuses if it fails.** Pass `disabled` to create it suspended |
| `update_guarantee` / `retire_guarantee` | Change / retire. Retiring a guarantee that still has dependents is **refused** |
| `refactor_file(old, new)` | Move a file/dir + its `.gbc` metadata; rewrite every path reference graph-wide (dependency edges, reverse `dependents`, and `[[ ]]` prose refs in gbc.md); auto-disable the moved file's guarantees. Idempotent — reconciles an already-moved file. |
| `refactor_func(provider, old_symbol, new_symbol)` | Rename a symbol: rewrite consumers' dependency symbols + the guarantee ids under it + `[[path:symbol]]` prose refs; auto-disable. You rename the symbol in source yourself. |
| `rename_guarantee(provider, old_id, new_id)` | Rename a guarantee id, both directions (provider key + every consumer). |
| `disable_guarantee(provider, id)` / `enable_guarantee(provider, id)` | Suspend / resume born-green for a guarantee while keeping its id and edges. `enable` re-runs born-green and refuses if it still fails. Disabled guarantees stay loud in `check_consistency` (`disabled_guarantee` / `depends_on_disabled`). |
| `verify_guarantee(provider, id)` / `verify_provider(provider)` | Run one / run all of a file's guarantees (the gate) |
| `who_depends_on(provider[, symbol, guarantee_id])` | Reverse-lookup who depends on me (replaces grep) |
| `list_provides(provider)` / `list_depends_on(consumer)` | See the guarantees I provide / the dependencies I declare |
| `check_consistency()` | Whole-graph lint: dangling references, two-way edge drift |

**Intent side (gbc-doc skill → `gbc_doc.py`):**

| Command | What it does |
|---------|--------------|
| `show <folder>` | View a folder's intent / constraints / entries |
| `set-intent <folder> "<text>"` | Set intent, auto single-source projected to the parent entry |
| `set-constraints <folder> "<text>"` / `set-file <folder> <name> "<desc>"` | Set internal constraints / add or change a file entry |
| `rm-entry <folder> <name>` | Remove a doc entry (does not delete the file on disk) |
| `check` / `sync` | Consistency lint / deterministically repair parent-child drift |

`<folder>` uses a project-relative path; use `""` or `.` for the root.

---

## 7. Working under GBC: the workflow

**Role default (top-level agent).** These manuals and the operating rules that `setup-gbc`
injects assume **you are the top-level agent**: preferred default is plan → align intent →
dispatch subagents (each brief carries sliced gbc.md **intent and internal constraints**, a
**writable target file**, and **read-only everywhere else**) → subagent self-verifies → **you**
run the final gate via GBC tools (MCP by default — do not hand-run the underlying test runner).
Planning and implementation in one agent is fine for small changes; day-to-day coding is not the
default role of the top-level agent. Projects onboarded via `setup-gbc` get the full write-up in
their instruction file — treat that block as the living workflow.

**Two layers of contract.** ① **Intent** (gbc.md): architectural truth, the highest contract,
**owned and approved by a human**; you can only draft it. ② **Guarantee**: a **named behavior** a
file currently provides and that has downstream dependents; you may evolve it, but breaking it =
you must make every dependent fix.

**Reference code with `[[project-relative-path]]`.** When gbc.md prose points at a code file or
symbol, write it as `[[app/core/models/game.py]]` or `[[app/core/models/game.py:GameSpec]]` — a path
from the repo root, wrapped in `[[ ]]`. Don't use `../` relative paths: a relative ref breaks when
either side moves and reads differently from each referrer, whereas a `[[ ]]` ref is one canonical
string per target that the `refactor_file` / `refactor_func` tools rewrite automatically when the
target moves. (Data directories, HTTP routes, and ADR links don't need `[[ ]]`.) Guarantee ids
follow the same spirit but are path-free: `<symbol>.<behavior>` (e.g. `make_game.returns_html`),
unique per provider.

**Each change has two phases, and the order matters — don't jump straight to code the moment you've
thought through the architecture:**

1. **Architecture phase (draft first; default install requires explicit human approval).** On a
   new human demand, take the **entire** gbc.md delta as a **draft** (text), check it with the
   human, and land it through gbc-doc **only after explicit approval**; then `check` that it is
   clean. **Landed gbc.md = the spec you implement.** Setup ships this confirmation rule **in**
   the operating rules / instruction block by default. If the human dislikes the friction, they
   may ask the agent to **delete that line** from the instruction file — afterward the agent
   simply does **not see** a rule that forces intent confirmation, and may act more on its own.
   That is allowed; with no human watching intent landings, **silent architectural drift risk rises**.
   While the line is still present, do not invent a private bypass: either the instruction contains
   the rule (confirm) or the human removed it (absent).
2. **Implementation phase (machine-gated).** Prefer one **subagent per target file** (writable
   writable list in the brief; everything else **read-only**). Topological order (depended-upon
   first). Implementing agent:
   - Read the approved scope (brief / gbc.md) + interfaces → write the implementation.
   - Behaviors you depend on or newly expose: free `add_dependency` for signature-only; for real
     behavior, **proactively write a narrow test and `create_guarantee` / attach** (reuse when
     possible). Unregistered behavioral deps = not done.
   - **Self-verify** with `verify_provider` / `verify_guarantee` via GBC tools only (not the bare
     runner).
   - Intent wrong mid-flight → stop, return to architecture phase; no silent drift.
3. **Final acceptance (top-level).** After subagents return, the top-level / architecture agent
   runs affected guarantees again via GBC tools. Do not skip this just because a subagent reported
   green.

**One small discipline for narrow tests:** assert the **promise**, not the **implementation**. Write
`assert r is not None`, not `== some exact value`; write `with pytest.raises(X)`, not a fight over
the exact error message. **Lean narrow** — an occasional missed alarm is acceptable, but a false
alarm gradually erodes trust in the whole system, and that's what you really want to avoid.

---

## 8. A few easy traps

Knowing these up front saves you some detours:

| Easy trap | Do this instead |
|---|---|
| Hand-editing `gbc.md` or `*.json` under `.gbc/**` | gbc.md goes through the gbc-doc skill; dependencies/guarantees go through gbc MCP |
| Jumping to code right after thinking through the architecture | Draft gbc.md → human approves (default) → topological implement; drop the confirm line only if the human asks to remove it from instructions |
| Subagent rewrites half the tree "while here" | Brief lists writable target file(s); all else read-only |
| Skipping top-level verify because the subagent said green | Subagent self-verifies; top-level still final-gates |
| Landing gbc.md without a human look (while confirm rule is still in instructions) | Explicit approval first; or human deleted the confirm rule on purpose |
| Tests asserting an exact return value (`== "<html>..."`) | Assert the promise: non-empty / type / raises |
| Naming a guarantee for every dependency | Default to free symbol dependencies; **only** upgrade behavior dependencies, and lazily |
| Retiring a guarantee that still has dependents | Migrate/fix the dependents first (`retire` will refuse) |
| Calling tools with absolute paths | Always project-root-relative posix paths |
| Changing a pile of files at once | Topological order, one file per step, run guarantees each step |
| Hand-fixing references after moving a file or renaming a symbol | Use `refactor_file` / `refactor_func` — they rewrite the json graph AND the `[[ ]]` prose refs in gbc.md in one shot (and `refactor_file` is idempotent) |

---

For deeper setup (cross-platform, custom clients) see [integrate-mcp_EN.md](./integrate-mcp_EN.md); for the
intent editor and skill examples see [intent-editor-and-skills_EN.md](./intent-editor-and-skills_EN.md).
