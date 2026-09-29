# Reference

> Language: [简体中文](../zh/reference.md) | **English**

Command / tool cheat sheet, executor config, cross-platform wiring. For getting started see
[quick-start.md](./quick-start.md); for the workflow see [workflow.md](./workflow.md).

GBC abilities are available through **CLI** (`gbc ...`) and **MCP tools**. The **gbc-cli** skill
adapts those abilities to shell commands; **gbc-workflow** guides intent, behavior tests, and
vocabulary/decision reuse with either transport. See [workflow.md](./workflow.md). The tables
below lead with CLI and note the matching MCP tool name.

If `gbc` is not on PATH, any `gbc` can be replaced with `python -m gbc.entry`.

---

## Top-level commands

| Command | What it does |
|---------|--------------|
| `gbc mcp up [project-root]` | Start the stdio MCP server (long-running). Omit the root to use `GBC_PROJECT_ROOT`, then the current working directory. |
| `gbc editor up` | Start the intent-editor web service (long-running, for humans). `--port` / `--host` / `--root`. |
| `gbc lang [zh\|en\|auto]` | View or set the persistent user language preference. With no argument, shows the preference and effective language; `auto` clears the explicit preference and restores automatic selection. |
| `gbc setup` | Print a localized wiring guide: how to connect MCP / skills to your agent. A trailing `--lang zh/en` overrides the language for this invocation only. |
| `gbc rules` | Print the author's recommended guardrails (recommended defaults, not an enforced sandbox). A trailing `--lang zh/en` overrides the language for this invocation only. |
| `gbc tree` | Show browsing-command help and exit successfully. |
| `gbc tree show [folder]` | Render the whole `.gbc` dependency tree when the folder is omitted, or browse a selected subtree. Supports `--depth N`; `--detail` expands guarantee details, and `--gaps` appends registration gaps. |
| `gbc tree folders [folder]` | Show only folder intent and internal constraints; supports `--depth N`. Fall back to the parent's entry when a child has no document, and deduplicate parent/child projections of the same folder. |
| `gbc tree for <file>...` | Combine modification context for target files: file entries, all ancestor intent and constraints, direct dependency symbols and named guarantees, and guarantees provided by the targets with their consumers. |
| `gbc doctor check` | Global consistency lint: dangling refs + two-way edge drift + disabled guarantees (reported loudly). |

For normal use, run `gbc lang zh` or `gbc lang en` once; use the trailing `--lang` on `setup` or
`rules` or a `doc` leaf command for a temporary override.

By default, GBC selects the project root in this order: `GBC_PROJECT_ROOT` > current working
directory (cwd). It does **not** search parent directories. Where supported, append
`--project <project-root>` or `-C <project-root>` to an engine leaf command to override it, for
example `gbc doctor check -C /path/to/project`.

### Tree browsing and modification context

Migrate the old CLI tree-rendering call to `gbc tree show`; group-level `gbc tree --detail` / `--gaps` now fail with a migration hint, so use `gbc tree show --detail` / `--gaps`. The MCP `tree` tool still returns the tree with no arguments.

Folder and file paths are relative to the project root; paths outside the project are rejected.
The selected folder is depth 0, and `--depth 1` shows its immediate children. Omit the depth
for an unlimited view; collapse markers indicate content hidden by the depth limit.

```sh
gbc tree show gbc --depth 1 --detail -C /path/to/project
gbc tree folders gbc --depth 2 -C /path/to/project
gbc tree for gbc/entry.py gbc/app/interface/cli.py -C /path/to/project
```

`tree for` requires file targets and does not accept browsing options such as `--depth`,
`--detail`, or `--gaps`. It deduplicates shared context while retaining target associations,
including guarantee test references and disabled status. Dependencies expand only one hop;
it does not read source code, test contents, or `AGENTS.md`, and does not run tests.

MCP equivalents: `tree(detail=False, gaps=False, folder="", depth=None, folders_only=False)`
for browsing (`folders_only=True` corresponds to `tree folders`), and `tree_for(files=[...])`
for modification context.

---

## Guarantees — `gbc guarantee` / MCP

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc guarantee create <provider> <id> <test> <executor> <desc>` | `create_guarantee` | Create a named guarantee. **Born-green for normal enabled creation**: runs the test now, refuses if it fails. `--heavy N` / `--timeout S` / `--disabled` (placeholder skipping the gate, only to break a circular dependency). |
| `gbc guarantee update <provider> <id>` | `update_guarantee` | Change fields: `--desc` / `--test` / `--executor` / `--heavy` / `--timeout`. Changing the test / executor re-runs the gate for enabled guarantees; disabled updates stay suspended until enable. |
| `gbc guarantee retire <provider> <id>` | `retire_guarantee` | Retire. **Refused** if it still has dependents (retirement protection). |
| `gbc guarantee disable <provider> <id>` | `disable_guarantee` | Disable: keep id and all edges, suspend the gate / batch verify. Disable ≠ retire. |
| `gbc guarantee enable <provider> <id>` | `enable_guarantee` | Re-enable: re-run born-green now, promote only if it passes, else stay disabled. |
| `gbc guarantee list <provider>` | `list_provides` | List all of a provider's guarantees and their dependents. |

**Id convention**: `<symbol>.<behavior>` (e.g. `get_config.never_none`), path-free, unique within
the provider.

---

## Dependencies — `gbc dep` / MCP

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc dep add <consumer> <provider> <symbol>` | `add_dependency` (no guarantee_id) | Free symbol dependency: depends on the symbol existing; no test, no reverse edge. |
| `gbc dep add <consumer> <provider> <symbol> -g <id>` | `add_dependency` (with guarantee_id) | Behavior dependency: attach to an existing guarantee, reverse edge written automatically. Multiple consumers may share one guarantee. |
| `gbc dep remove <consumer> <provider> <symbol> [-g <id>]` | `remove_dependency` | Detach one guarantee (`-g`) or remove the whole symbol edge (no `-g`). |
| `gbc dep of <consumer>` | `list_depends_on` | List every dependency edge a file declares. |
| `gbc dep who <provider> [-s <symbol>] [-g <id>]` | `who_depends_on` | Reverse lookup: who depends on this provider (replaces ad-hoc grep). |

---

## Verify — `gbc verify` / MCP

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc verify all` | `verify_all` | Strict project release gate. Groups enabled guarantees by equivalent execution plans, ignores heavy rank, runs each distinct check once per call and attributes its result to every referencing guarantee. Any failure, disabled guarantee, missing execution result, or zero executions makes the gate fail. Reports provider + guarantee id locations. |
| `gbc verify provider <provider>` | `verify_provider` | Run all of a provider's guarantees. Heavy ones above the threshold are skipped and reported (not failed). `--max-heavy N`. **GREEN iff no failures.** |
| `gbc verify single <provider> <id>` | `verify_guarantee` | Run one by id, ignoring the heavy threshold — always runs. `-v` shows full stdout/stderr. |

**Gate semantics**: `verify all` is the strict whole-project release gate. In contrast,
`verify provider` retains its scoped semantics: a skipped heavy or disabled guarantee is reported
but does not turn that provider gate red, and GREEN only means no executed guarantee failed.

Project-wide sharing requires the same executor name, full test selector, expanded command,
working directory, effective environment and resolved timeout (call override, guarantee override,
executor default, then built-in default). Different providers/IDs or heavy ranks do not require
another run. Sharing is limited to one call; a later call always runs checks again.
`executed` counts guarantees with results, while `test_runs` counts distinct execution attempts.
All references to a failing check fail. Checks that cannot produce a result leave their references
in `missing`; `execution_errors` records error types without exposing private command arguments.

All executor output is decoded as UTF-8, independently of the host locale. Invalid
bytes are displayed as `\xNN` escapes (`backslashreplace`), preserving their values
and surrounding diagnostics instead of dropping a stream. Exit codes are unchanged.
These strings are diagnostic text, not a byte-for-byte archive: newline conversion
still applies and a literal `\xNN` in the output is indistinguishable from an escape.
Configure legacy tools to emit UTF-8 if their text must be readable without escapes.

Development may run unregistered tests directly in the correct
environment; formal creation and test/executor updates for normally enabled guarantees retain born-green. Disabling is not a
TDD step, and final acceptance runs through GBC with review of contract and test changes.

---

## Refactor — `gbc refactor` / MCP (never hand-fix the graph)

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc refactor file <old> <new>` | `refactor_file` | Move a file / dir + its `.gbc` metadata, rewrite all path references graph-wide (dependency edges, reverse dependents, `[[ ]]` refs in gbc.md), auto-disable the moved file's guarantees. Ids unchanged (path-free). Idempotent. |
| `gbc refactor func <provider> <old_symbol> <new_symbol>` | `refactor_func` | Rename a symbol: rewrite consumers' symbol field + guarantee ids under that symbol + `[[path:symbol]]`, auto-disable. You rename `def` / call sites in source. |
| `gbc refactor rename-id <provider> <old_id> <new_id>` | `rename_guarantee` | Rename a guarantee id, both directions (provider key + every consumer). |

After a refactor: fix imports, move tests and `gbc guarantee update <p> <id> --test ...`, then
`gbc guarantee enable` each disabled id.

---

## Offline GBC manual — `gbc doc` / MCP

The manual ships with the installed GBC version and works offline, from any directory, without
a target project. It does not inspect or modify `.gbc`. `--help` remains short command syntax.

| CLI | MCP tool | Result |
|-----|----------|--------|
| `gbc doc list [--lang en\|zh]` | `doc_list(lang=None)` | Selected language and fixed topic IDs with titles. |
| `gbc doc read <topic> [--lang en\|zh]` | `doc_read(topic, lang=None)` | The complete Markdown topic. |
| `gbc doc search "<query>" [--lang en\|zh] [--limit 20]` | `doc_search(query, lang=None, limit=20)` | Case-insensitive literal line matches, with topic ID, one-based line number and text. |

The fixed topics are `quick-start`, `concepts`, `workflow`, `reference`, and `onboarding-agent`.
Language selection follows the same preference chain as other GBC output; `--lang` overrides
one invocation. Search uses a literal substring, not regular expressions, and defaults to 20
matches (valid range 1–100). Matching text is a snippet of at most 240 characters centered on
the match, rather than an unlimited line. Empty queries and unknown topics are errors. Results include `truncated`
when more matches exist, so a limited result is distinguishable from a complete search.

MCP list returns `{language, topics: [{id, title}]}`; read returns Markdown text; search returns
`{language, query, matches: [{topic, line, text}], truncated}`. It searches only the selected
language. The Markdown sources in `docs/en/` and `docs/zh/` are canonical; packaging copies
these ten topics into package resources without keeping a second source copy.

```sh
gbc doc list --lang en
gbc doc read workflow --lang en
gbc doc search "guarantee" --lang en --limit 10
```

## Intent docs — `gbc intent` / MCP

**0.3.0 breaking migration:** all former intent `gbc doc ...` commands are now
`gbc intent ...`; the eight former `doc_*` MCP tools are now `intent_*`. There are no compatibility
aliases. Update scripts and agent instructions; `doc` now queries this GBC manual.

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc intent show <folder>` | `intent_show` | View a folder's intent / constraints / entries. Root is `""` or `.`. |
| `gbc intent check` | `intent_check` | Whole-tree consistency lint (DRIFT/ORPHAN are errors, STUB is a note). |
| `gbc intent set-intent <folder> "<text>"` | `intent_set_intent` | Set intent (auto single-source projection into the parent entry). |
| `gbc intent set-constraints <folder> "<text>"` | `intent_set_constraints` | Set internal constraints (local only). |
| `gbc intent set-file <folder> <name> "<desc>"` | `intent_set_file` | Add / update a file entry (name without `/`). |
| `gbc intent rm-entry <folder> <name>` | `intent_rm_entry` | Remove an entry (doesn't delete the on-disk file; left for git review). |
| `gbc intent sync` | `intent_sync` | Deterministically repair parent/child drift. |
| `gbc intent migrate` | `intent_migrate` | Upgrade all gbc.md to the latest format. |

> When a `<text>` argument begins with `-`, put `--` before it so it isn't parsed as an option:
> `gbc intent set-intent app -- "- a line starting with a dash"`.

**Writing intent changes human-held architecture truth.** Whether it needs human sign-off is set by
your framework's rules / hooks, not gated by the tool. Never hand-edit gbc.md.
Under the recommended workflow, routine implementation, helper-file splits, and file-entry
maintenance within an authorized goal and responsibility need no repeated architectural approval;
changes to purpose, responsibilities, compatibility, authority, or important constraints need
corresponding authorization. Existing authorization continues to apply.

---

## Executor config

An executor defines "how to run tests," stored per project by name.

```bash
gbc executor upsert <name> --json '<JSON>'
# or
gbc executor upsert <name> --file <path.json>
```

Config shape:

```jsonc
{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],  // {file} → the test selector
  "cwd": "/abs/path/to/your-project",
  "timeout": 30,
  "env_ops": [
    {"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your-project"}
  ]
}
```

- Switch languages by swapping `command` (e.g. `["npx", "jest", "{file}"]`).
- `env_ops` actions: `set` / `append` / `prepend` / `remove`.
- Give it a **project-scoped name** (`pytest-<project>`) — executors are shared across projects by
  name, so a bare name would collide.

> ⚠️ **Security note**: an executor config essentially permits running arbitrary shell commands.
> Audit the executor configs an agent writes and keep them under control.

---

## Cross-platform wiring: WSL calling Windows Python

If the agent runs in WSL while GBC's Python is on Windows (e.g. a conda env), `gbc mcp up` has
already shouldered two pitfalls (env vars not passed through, cwd import hijacking) — just follow
the start contract:

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/mnt/c/Users/<you>/miniconda3/envs/<env>/Scripts/gbc.exe",
      "args": ["mcp", "up", "D:/path/to/your-project"]
    }
  }
}
```

- `command` uses the path WSL can see (`/mnt/c/...`); the project root in `args` is in **Windows
  form** (`D:/...`) because it's argv handed to a Windows process.
- Same-platform (pure Linux / pure Windows) needs none of this — use native absolute paths.
- If locating the console-script entry is awkward, use `<python.exe> -m gbc.entry mcp up
  <project-root>`.

---

## Mental model

- One MCP server instance = one project root. Multiple projects = multiple entries (different
  project-root args).
- MCP exposes the guarantee engine, project intent (`intent_*`), and the offline GBC manual
  (`doc_list`, `doc_read`, `doc_search`). The
  human-confirmation gate for writing intent is carried by your framework, not by hiding the
  channel.
- Path arguments are always **project-root-relative** posix paths (`gbc/app/core/maker.py`), not
  absolute.
