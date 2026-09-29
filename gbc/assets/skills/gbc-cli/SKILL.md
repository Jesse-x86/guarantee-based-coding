---
name: gbc-cli
description: Drive GBC (Guarantee-Based Coding) through its `gbc` command-line interface. Use this whenever you need to register/verify/inspect guarantees, dependencies, or intent docs and MCP is not available to you (or you prefer the CLI). This is the CLI-side equivalent of GBC's MCP tools — every ability is a `gbc ...` subcommand. Assumes the `gbc` command is already installed and on PATH.
---

# gbc-cli: using GBC from the command line

GBC turns implicit inter-module dependencies into **named, executable guarantees**: a guarantee
is a named behavior a file promises, backed by a test. Change code → re-run the affected
guarantees → green means no executed guarantee failed; skipped or disabled guarantees remain unverified. This skill tells you which `gbc`
commands realize those abilities, so you can use GBC without an MCP connection.

For intent planning, guarantee quality or domain terminology decisions, use the
sibling [gbc-workflow skill](../gbc-workflow/SKILL.md). It works with both MCP and
CLI; this skill provides the command mapping.

Everything here is a plain shell command. If `gbc` is not on PATH, substitute
`python -m gbc.entry` for `gbc` (same subcommands).

> **Which project am I acting on?** Commands act on the current GBC target project, which
> defaults to the directory you run `gbc` from (its cwd) — no environment variable needed. Just
> `cd` into the project root before running commands. All paths you pass to commands are
> **project-relative** (e.g. `gbc/app/core/config.py`).

---

## The core loop (register once, verify forever)

1. **Register an executor** (how tests run) — once per project, by name.
2. **Create a guarantee** on a provider file — born-green: the test runs immediately, and
   creation is refused if it fails.
3. **Register dependencies** — record that a consumer relies on a provider's symbol/guarantee.
4. **Verify** after changes — run a provider's guarantees; green iff nothing failed.

Development tests may run directly in the project's correct environment before registration,
including observing a failure and implementing to green. Normal enabled registration remains
born-green, and final acceptance still runs through GBC. Do not use a disabled placeholder for
ordinary TDD. GBC runs your tests; reviewing their assertions remains necessary.

---

## Guarantees — `gbc guarantee`

| Command | What it does |
|---------|--------------|
| `gbc guarantee create <provider> <id> <test> <executor> <desc>` | Create a named guarantee. **Born-green**: runs the test now, refuses if it fails. Add `--heavy N` (cost rank; `>=1` is skipped in batch verify), `--timeout S`, or `--disabled` (placeholder that skips born-green — only to break a circular dependency; enable it later). |
| `gbc guarantee update <provider> <id>` | Change fields: `--desc`, `--test`, `--executor`, `--heavy`, `--timeout`. Changing the test/executor re-runs born-green for enabled guarantees; disabled guarantees require a passing enable before their protection is restored. |
| `gbc guarantee retire <provider> <id>` | Delete a guarantee. **Refused if it still has dependents** — migrate them first. |
| `gbc guarantee disable <provider> <id>` | Suspend born-green/batch verify for it while keeping its id and all edges. Escape hatch for refactors; **not** a delete. |
| `gbc guarantee enable <provider> <id>` | Re-run born-green now; clears disabled only if the test passes. |
| `gbc guarantee list <provider>` | List every guarantee a provider offers, with state and dependent count. |

**Id convention**: `<symbol>.<behavior>`, e.g. `get_config.never_none`. Do **not** encode the
provider path in the id — the path is carried by the `<provider>` argument. Ids need only be
unique per provider.

---

## Dependencies — `gbc dep`

| Command | What it does |
|---------|--------------|
| `gbc dep add <consumer> <provider> <symbol>` | Register a **free** symbol-level dependency (depends on the symbol existing, not on a specific behavior; no test, no reverse edge). |
| `gbc dep add <consumer> <provider> <symbol> -g <guarantee_id>` | Register a **behavior** dependency on an existing guarantee. The reverse edge (provider's dependents) is written automatically. Multiple consumers may share one guarantee. |
| `gbc dep remove <consumer> <provider> <symbol> [-g <id>]` | Remove one guarantee from the edge (`-g`), or the whole symbol edge (no `-g`). |
| `gbc dep of <consumer>` | List every dependency edge a file declares. |
| `gbc dep who <provider> [-s <symbol>] [-g <id>]` | Reverse lookup: who depends on this provider. Replaces ad-hoc grep. |

---

## Verify — `gbc verify`

| Command | What it does |
|---------|--------------|
| `gbc verify all` | Strict whole-project release gate. Scans every provider and runs every enabled guarantee regardless of heavy rank. Any failure, disabled guarantee, missing execution result, or zero executions fails the command. Reports `provider:id` locations. |
| `gbc verify provider <provider>` | Run all of a provider's guarantees. Heavy guarantees above the threshold are skipped and reported (not failed). Add `--max-heavy N` to run heavier ones. **GREEN iff nothing failed.** |
| `gbc verify single <provider> <id>` | Run one guarantee by id — always runs, ignoring the heavy threshold. Add `-v` for full stdout/stderr. |

**Gate semantics**: use `verify all` for strict project release acceptance. `verify provider`
retains its scoped behavior: guarantees skipped for heavy or disabled state are reported but do
**not** turn that provider gate red. Its GREEN means no failures, not completed acceptance.

---

## Inspect — `gbc tree` / `gbc doctor`

| Command | What it does |
|---------|--------------|
| `gbc tree` | Show browsing-command help and exit successfully. |
| `gbc tree show [folder]` | Omit the folder to render the whole `.gbc` tree as one AI-readable dependency document (intent backbone + dependency edges + provided guarantees). Add `--detail` for guarantee desc/test/heavy, `--gaps` for registration gaps. Provide a folder to browse a subtree; add `--depth N` to limit depth. **Start here for a whole-project overview.** |
| `gbc tree folders [folder]` | Browse only folder intent and internal constraints; supports `--depth N`. |
| `gbc tree for <file>...` | Combine each target file's entries, ancestor intent/constraints, direct dependencies and provided guarantees with consumers. |
| `gbc doctor check` | Global consistency lint: dangling references, two-way edge drift, and disabled guarantees (reported loudly, not as errors). |

Use `gbc tree show` for the old CLI tree-rendering call. Group-level `gbc tree --detail` / `--gaps` now fail with a migration hint; use `gbc tree show --detail` / `--gaps`. The MCP `tree` tool still returns the tree with no arguments.

---

## Executors — `gbc executor`

An executor is a named recipe for running tests, stored per project. Register it once, then
guarantees reference it by name.

```bash
gbc executor upsert <name> --json '{"command": ["pytest", "{file}", "-x", "-q"], "cwd": "/abs/project", "timeout": 30, "env_ops": [{"key": "PYTHONPATH", "action": "prepend", "value": "/abs/project"}]}'
```

- `command`: argv parts; `{file}` is substituted with the test selector.
- Or pass a JSON file with `--file <path>` instead of `--json`.
- Give it a **project-scoped name** (e.g. `pytest-<project>`) so it won't collide with another
  project's executor.

---

## Move / rename — `gbc refactor` (never hand-fix the graph)

Relocating a file or renaming a symbol desyncs every path-addressed reference. Use these instead
of editing `.gbc` by hand:

| Command | What it does |
|---------|--------------|
| `gbc refactor file <old> <new>` | Move a file/dir + its `.gbc` metadata, rewrite all references graph-wide, auto-disable the moved file's guarantees (their tests break until you fix imports). Ids are unchanged (path-free). Idempotent. |
| `gbc refactor func <provider> <old_symbol> <new_symbol>` | Rename a symbol: rewrite consumers' edges + the guarantee ids under that symbol, auto-disable them. You rename `def`/call sites in source, then `enable`. |
| `gbc refactor rename-id <provider> <old_id> <new_id>` | Rename a guarantee id, keeping both directions consistent. |

After any refactor: fix imports, move the test files and `gbc guarantee update <p> <id> --test ...`,
then `gbc guarantee enable <p> <id>` for each disabled id.

---

## Offline manual — `gbc doc`

Use `gbc doc list [--lang en|zh]`, `gbc doc read <topic> [--lang en|zh]`, or
`gbc doc search "<query>" [--lang en|zh] [--limit 20]` to query the manual shipped with GBC.
These work offline and do not require a target project. The fixed topics are `quick-start`,
`concepts`, `workflow`, `reference`, and `onboarding-agent`. Search is a case-insensitive literal
substring search, with topic IDs, one-based line numbers, bounded text snippets, and a
`truncated` flag. The result limit is 1–100 (default 20); empty queries and unknown topics fail.
For command syntax alone, use `--help`.

## Intent docs — `gbc intent`

Since 0.3.0, replace all former intent `gbc doc ...` calls with `gbc intent ...`; no compatibility
aliases remain. MCP intent tools similarly use `intent_*`; `doc_list`, `doc_read`, and
`doc_search` query the GBC manual.

`gbc.md` files hold the project's architectural intent. `gbc intent` is the compliant read/write
entry — it keeps each doc's three-section structure and parent/child consistency for you.

| Command | What it does |
|---------|--------------|
| `gbc intent show <folder>` | View a folder's intent / constraints / entries. Root folder is `""` or `.`. |
| `gbc intent check` | Whole-tree intent consistency lint (DRIFT/ORPHAN are errors, STUB is a note). |
| `gbc intent set-intent <folder> "<text>"` | Set a folder's intent (auto-projected into the parent entry). |
| `gbc intent set-constraints <folder> "<text>"` | Set internal constraints (local only). |
| `gbc intent set-file <folder> <name> "<desc>"` | Add/update a file entry (name without `/`). |
| `gbc intent rm-entry <folder> <name>` | Remove a doc entry (does not delete the file on disk). |
| `gbc intent sync` | Deterministically repair parent/child drift. |
| `gbc intent migrate` | Upgrade all gbc.md files to the latest format. |

> If a `<text>` argument begins with `-`, put `--` before it so it isn't parsed as an option:
> `gbc intent set-intent app -- "- a line starting with a dash"`.

**Intent records human-held architecture truth.** Follow your framework's authority rules;
existing authorization covers ordinary implementation and file-entry maintenance within approved
responsibilities. Material changes outside that authority need the corresponding approval.
Never hand-edit `gbc.md`.

---

## The boundary (read `gbc rules`)

GBC gives abilities, not restraint. Who may edit `.gbc/`, when intent needs human sign-off — those
rules are printed by `gbc rules`, and their **enforcement** must come from your agent framework
(e.g. a pre-tool-use hook). The same enforcement applies whether you reach GBC via CLI or MCP.
Run `gbc rules` and follow what your human has adopted.
