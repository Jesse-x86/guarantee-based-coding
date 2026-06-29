# The intent-tree editor, the CLI, and wrapping the CLI as your own skill

> Entry points: [for-agents.md](./for-agents.md) (for agents) / [for-humans.md](./for-humans.md) (for humans). This page expands the "wrap the intent CLI as a skill" step from the [manual.md](./manual.md) (web editor, full command surface, SKILL.md example).

GBC has two tracks with different permissions:

- **Guarantees** — agents self-serve CRUD through MCP, machine-gated. See [integrate-mcp.md](./integrate-mcp.md).
- **Intent** — architectural truth held by humans, stored in each folder's `gbc.md`. Agents may only "draft"; humans approve.

This page covers the second track: how intent docs are edited (web editor / CLI), and how to **wrap a skill around the CLI** so your agent has a single compliant entry for changing intent instead of hand-editing `gbc.md`.

## Why not let agents hand-edit gbc.md

`gbc.md` has structure (`## entries` under `# 意图` / `# 内部约束` / `# 文件`) and one layer of **deliberate duplication**: a subfolder's intent is written both in its own `gbc.md`'s `# 意图` and in the **parent** folder's `gbc.md` `## sub/` entry. The duplication serves the context locality of the agents writing code, but **maintaining two copies by hand inevitably drifts**.

Whether the structure is correct and whether parent and child stay in sync is a class of deterministic, recurring constraint — safest handed to a program, rather than relying on the agent to remember every time. The tool treats the tree as the **single source of truth**: you write a node's intent once, and on save the tool projects it to both places.

Humans make the architectural judgments, the tool handles the mechanical maintenance — consistent with GBC's philosophy.

## How to write gbc.md (three sections + spec-first)

Each `gbc.md` has three sections, each with one job:

- **`# 意图` (Intent)** = what this folder/file **is and why it exists** (role / purpose). **Explain concepts inline or leave a link** (see ADR-0001) — don't leave undefined terms.

  **Reference code with `[[project-relative-path]]`.** When prose points at a code file or symbol, write it as `[[app/core/models/game.py]]` or `[[app/core/models/game.py:GameSpec]]` — a path from the repo root, wrapped in `[[ ]]`. Don't use `../` relative paths: a relative ref breaks when either side moves and reads differently from each referrer, whereas a `[[ ]]` ref is one canonical string per target that the `refactor_file` / `refactor_func` tools rewrite automatically when the target moves. (Data directories, HTTP routes, and ADR links don't need `[[ ]]`.)
- **`# 内部约束` (Internal constraints)** = what it **needs, and what it must / must not do** (obligations and rules: what state it holds, what it consumes, what must happen before what, what it must never touch). "What it needs, what it should do" goes here — don't pile it into intent.
  > Constraints **live only locally and don't bubble up to the parent**, but that's ≠ "kept secret from outsiders": the test is "**identity (→ intent) or a rule (→ constraints)**". A rule still belongs in constraints even if outsiders must obey it (e.g. "outsiders may only depend on this module's interface"), as long as it's a rule and not a reason for existing.
- **`# 文件` (Files)** = subfolders (name ends in `/`) plus this folder's code files, each with a one-line role description (same rule: explain the concept or leave a link).

**spec-first**: before dispatching a subagent / writing code, use the skill to write the above first, self-review or send for review, and implement against the already-written gbc.md — **intent always precedes code**. When creating/moving a folder or file, **register its `# 文件` / intent entry here first** too; don't backfill it after the code is written.

## Usage 1: the web intent-tree editor

Pure standard library, zero dependencies. Good for humans doing architecture who want to edit the whole tree visually.

```bash
cd tools/intent-editor/backend
python3 app.py                          # 127.0.0.1:8765, path box left blank
python3 app.py --root /path/to/.gbc     # prefilled and auto-loaded
# also --port / --host
```

Open http://localhost:8765 in a browser.

- **Load**: type a `.gbc` directory in the path box and click "Load". The path need not exist — you get an empty tree, and "Save" creates the directories and files from scratch.
- **Editing children**: a name ending in `/` is a subfolder (toggles live), otherwise it's a file. A blank grey child row sits at the bottom permanently; start typing and it becomes real; clear both the name and description of a row and blur to delete it.
- **Save only writes, never deletes**: removing an entry = it's no longer generated, but the old file on disk must be cleaned up by hand / via git. Use `git diff` to review what was written back.

## Usage 2: the intent CLI (`gbc_doc.py`)

For agents / scripts to call. Located at `tools/intent-editor/backend/gbc_doc.py`.

```
python gbc_doc.py --root <project dir or its .gbc dir> <command> [args...]
```

`<folder>` is a **project-relative path** (e.g. `app/core/maker`); use `""` or `.` for the root.

| Command | What it does |
|------|------|
| `show <folder>` | View a folder's intent / constraints / entries |
| `set-intent <folder> "<text>"` | Set intent; **auto single-source projects** to the parent doc's `## <name>/` entry |
| `set-constraints <folder> "<text>"` | Set `# 内部约束` (lives only locally, doesn't bubble up to the parent) |
| `set-file <folder> <name> "<desc>"` | Add/change a **file** entry (name has no `/`) |
| `rm-entry <folder> <name>` | Remove an entry from the doc (only edits the doc, doesn't delete the file on disk — left for git review) |
| `check` | Whole-tree consistency lint: `DRIFT`/`ORPHAN` = errors (exit code 1); `STUB` = hint (normal for leaf folders) |
| `sync` | Deterministically repair `DRIFT`/`ORPHAN`: re-project child intent into the parent entry (touches only the parent, not the child) |
| `migrate` | Parse→serialize-rewrite every gbc.md, upgrading to the new format with the `# 文件` section |

Key points:

- **Creating a subfolder** only needs `set-intent` on it; the parent entry is **auto-registered** — don't manually add `## xxx/` to the parent doc.
- A subfolder's intent is the **single source of truth**; the description in the parent doc is a projection, so don't edit it separately in the parent doc (it gets overwritten by `sync`).
- After editing, run `check` to confirm it's clean (no errors). All changes **still need human approval** (review `git diff`): the CLI only guarantees "the edit is structurally correct and parent/child are in sync" — it doesn't replace review.

## Wrap the CLI as your own skill

If your agent framework supports "skills / custom commands" (like Claude Code's skills), the best practice is to **wrap this CLI as a skill** as the agent's **single entry** for changing intent, and hard-code "NEVER hand-edit gbc.md" in the skill description. That way, when the agent wants to change intent it only ever goes through this deterministic program.

A skill = two things: **a thin wrapper script** + **a SKILL.md** (when to use it, the command surface).

### 1) The thin wrapper script

The wrapper does just three things: **pin the interpreter, pin `--root`, and pass the rest through**. Here is a real, working example (WSL calling a Windows conda python to change intent for some project):

```bash
#!/usr/bin/env bash
# gbc-doc — the only compliant edit entry for gbc.md. Wraps the intent-editor CLI (gbc_doc.py).
# gbc.md's structure and parent/child consistency are a deterministic constraint that must be
# kept by this program — never hand-edit gbc.md.
exec /mnt/c/Users/<you>/miniconda3/envs/<env>/python.exe \
  D:/path/to/guarantee-based-coding/tools/intent-editor/backend/gbc_doc.py \
  --root D:/path/to/your-project \
  "$@"
```

- The interpreter + `--root` are hard-coded in the wrapper → when the agent calls it, it only supplies the command and args, and can't pick the wrong environment or project root.
- `"$@"` passes through → all of `gbc_doc.py`'s subcommands (`show`/`set-intent`/`check`/…) are usable as-is.
- On a single platform (pure Linux / Windows), just swap the interpreter and paths for native absolute paths — the logic is unchanged.

### 2) SKILL.md

The "when to use it + how to use it" for the agent to read. Claude Code's skills use YAML frontmatter to declare `name`/`description` (the description decides when the agent auto-selects it); the body gives the invocation + command table + rules. Skeleton:

```markdown
---
name: gbc-doc
description: The only compliant entry for reading/writing .gbc intent docs (gbc.md). Use this skill
  whenever you view/create/change/lint gbc.md — NEVER hand-edit gbc.md (its structure and
  parent/child consistency are a deterministic constraint, only kept through this program).
---

# gbc-doc: the compliant edit entry for gbc.md

## Invocation
\`\`\`bash
bash /abs/path/to/gbc-doc.sh <command> [args...]
\`\`\`

## Commands
(copy the command table from "Usage 2" above)

## When to use / rules
- Use it before and after changing architecture (intent/constraints/adding/removing folders & files); run `check` to confirm it's clean.
- A subfolder's intent is the single source of truth; don't edit it separately in the parent doc (it gets overwritten by `sync`).
- All gbc.md changes still need human approval (review the diff). This skill only guarantees structural correctness and parent/child sync — it doesn't replace review.
```

### Likewise: you can wrap the "guarantee side" CLI too

Besides the intent-side `gbc_doc.py`, GBC also has a **core guarantee CLI** `app/interface/cli.py` (a typer implementation, one-to-one with the MCP tools), with subcommands: `guarantee` / `dep` / `verify` / `doctor` / `executor`. Run it as a module from the tool repo root:

```bash
python -m app.interface.cli verify provider <source file>
python -m app.interface.cli guarantee list <source file>
python -m app.interface.cli dep who <source file>
```

If your agent doesn't go through MCP and prefers the command line, you can wrap it as a skill the same way with the wrapper + SKILL.md pattern above. Whether to use MCP or the CLI on the guarantee side depends on your agent; on the intent side, always going through `gbc_doc.py` (the skill) is recommended, so there's "only one door for changing intent".
