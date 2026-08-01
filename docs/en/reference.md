# Reference

> Language: [简体中文](../zh/reference.md) | **English**

Command / tool cheat sheet, executor config, cross-platform wiring. For getting started see
[quick-start.md](./quick-start.md); for the workflow see [workflow.md](./workflow.md).

Every GBC ability has three equivalent forms: **CLI** (`gbc ...`), **MCP tool** (agent-called), and
the **gbc-cli skill**. The tables below lead with the CLI and note the matching
MCP tool name.

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
| `gbc tree` | Render the whole `.gbc` dependency tree. `--detail` expands guarantee details, `--gaps` appends registration gaps. |
| `gbc doctor check` | Global consistency lint: dangling refs + two-way edge drift + disabled guarantees (reported loudly). |

For normal use, run `gbc lang zh` or `gbc lang en` once; use the trailing `--lang` on `setup` or
`rules` only for a temporary override.

By default, GBC selects the project root in this order: `GBC_PROJECT_ROOT` > current working
directory (cwd). It does **not** search parent directories. Where supported, append
`--project <project-root>` or `-C <project-root>` to an engine leaf command to override it, for
example `gbc doctor check -C /path/to/project`.

---

## Guarantees — `gbc guarantee` / MCP

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc guarantee create <provider> <id> <test> <executor> <desc>` | `create_guarantee` | Create a named guarantee. **Born-green**: runs the test now, refuses if it fails. `--heavy N` / `--timeout S` / `--disabled` (placeholder skipping the gate, only to break a circular dependency). |
| `gbc guarantee update <provider> <id>` | `update_guarantee` | Change fields: `--desc` / `--test` / `--executor` / `--heavy` / `--timeout`. Changing the test / executor re-runs the gate. |
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
| `gbc verify provider <provider>` | `verify_provider` | Run all of a provider's guarantees. Heavy ones above the threshold are skipped and reported (not failed). `--max-heavy N`. **GREEN iff no failures.** |
| `gbc verify single <provider> <id>` | `verify_guarantee` | Run one by id, ignoring the heavy threshold — always runs. `-v` shows full stdout/stderr. |

**Gate semantics**: a test that ran is pass or fail; a skipped (heavy) one is reported loudly but
never turns the gate red. Green = no failures.

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

## Intent docs — `gbc doc` / MCP

| CLI | MCP tool | What it does |
|-----|----------|--------------|
| `gbc doc show <folder>` | `doc_show` | View a folder's intent / constraints / entries. Root is `""` or `.`. |
| `gbc doc check` | `doc_check` | Whole-tree consistency lint (DRIFT/ORPHAN are errors, STUB is a note). |
| `gbc doc set-intent <folder> "<text>"` | `doc_set_intent` | Set intent (auto single-source projection into the parent entry). |
| `gbc doc set-constraints <folder> "<text>"` | `doc_set_constraints` | Set internal constraints (local only). |
| `gbc doc set-file <folder> <name> "<desc>"` | `doc_set_file` | Add / update a file entry (name without `/`). |
| `gbc doc rm-entry <folder> <name>` | `doc_rm_entry` | Remove an entry (doesn't delete the on-disk file; left for git review). |
| `gbc doc sync` | `doc_sync` | Deterministically repair parent/child drift. |
| `gbc doc migrate` | `doc_migrate` | Upgrade all gbc.md to the latest format. |

> When a `<text>` argument begins with `-`, put `--` before it so it isn't parsed as an option:
> `gbc doc set-intent app -- "- a line starting with a dash"`.

**Writing intent changes human-held architecture truth.** Whether it needs human sign-off is set by
your framework's rules / hooks, not gated by the tool. Never hand-edit gbc.md.

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
- MCP now exposes **both subsystems**: the guarantee engine + intent documents (doc tools). The
  human-confirmation gate for writing intent is carried by your framework, not by hiding the
  channel.
- Path arguments are always **project-root-relative** posix paths (`gbc/app/core/maker.py`), not
  absolute.
