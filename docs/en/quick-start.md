# Quick Start

> Language: [简体中文](../zh/quick-start.md) | **English**

This page takes you from zero to a working GBC setup: install → wire into your agent → smoke test.
A few minutes.

GBC is a standalone command-line tool. Install once, use it in any project; it keeps its mutable
state under the **target project's** `.gbc/` directory and never touches your source.

---

## 1. Install

**Python >=3.10 is required.**

```bash
pipx install guarantee-based-coding
```

The `gbc` command is now on your PATH:

```bash
gbc --help
```

GBC's interface output supports Simplified Chinese and English; switch anytime with `gbc lang`:

```bash
gbc lang        # show the current effective language
gbc lang zh     # force Simplified Chinese
gbc lang auto   # restore automatic selection (follows the system locale)
```

Without an explicit preference, GBC follows the system locale and falls back to English.

> **`pipx` is recommended** ([installation guide](https://pipx.pypa.io/stable/installation/)): GBC is a standalone CLI tool (like `black` / `ruff`) — you want it
> installed once and usable everywhere, not polluting the Python environment of whatever project
> you're working on. You can still use `pip install guarantee-based-coding` (into your current
> environment) or `uvx guarantee-based-coding` (ephemeral). GBC's dependencies are light (typer /
> pydantic / mcp).

---

## 2. Give your agent GBC

Have your coding agent run `gbc setup` inside the target project and follow the output:

```bash
gbc setup
```

`gbc setup` prints a complete, localized wiring guide — MCP endpoints, skill file paths, and a
smoke-test command to verify everything works. Your agent doesn't need to memorize `gbc`
subcommands; it just reads the output and does what it says.

The sections below explain what the two wiring paths look like under the hood, for reference.

### Path A — MCP (recommended when your agent speaks MCP)

GBC ships a stdio MCP server exposing **both subsystems**: the guarantee engine (guarantee / dep /
verify / refactor / tree / consistency / executor) **and** the intent documents (doc show / check /
set-* / sync / migrate).

The start command is:

```bash
gbc mcp up <ABSOLUTE_PATH_TO_YOUR_PROJECT>
```

Register it as an MCP server. For Claude Code, drop a `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "gbc": {
      "command": "gbc",
      "args": ["mcp", "up", "/abs/path/to/your/project"]
    }
  }
}
```

- One server instance is pinned to one project root (passed as the argument; when omitted it
  falls back to `GBC_PROJECT_ROOT`, then the current working directory). For
  multiple projects, register multiple entries.
- If `gbc` is not on the launcher's PATH, use the interpreter form:
  `python -m gbc.entry mcp up <project-root>`.
- After registering, reconnect / restart your agent and the tools appear (as `mcp__gbc__*` in
  Claude Code).

Cross-platform details (WSL calling Windows Python, etc.) are in [reference.md](./reference.md).

### Path B — Skills (when you don't use MCP, or MCP is inconvenient)

Because every GBC ability is also a `gbc ...` command, an agent that can run shell commands can use
GBC through a set of **bundled skills**. `gbc setup` prints the absolute path to those skill files;
copy them into wherever your agent discovers skills (every framework reads skills from a different
place — GBC materializes the files, you place them).

---

## 3. Define an executor (how tests run)

Before registering any guarantee, tell GBC what command runs your tests. Executors are stored per
project, by name — define once, reuse. Call `upsert_executor` over MCP, or via CLI:

```bash
gbc executor upsert pytest-myproject --json '{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],
  "cwd": "/abs/path/to/your/project",
  "timeout": 30,
  "env_ops": [{"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your/project"}]
}'
```

- `{file}` is a placeholder substituted at run time with the guarantee's test selector.
- Switch languages by swapping `command` (e.g. `["npx", "jest", "{file}"]`).
- Give it a **project-scoped name** (e.g. `pytest-<project>`) — executors are shared across
  projects by name, so a bare `pytest` would collide with another project's.
- Full `env_ops` fields and `action` values (`set`/`append`/`prepend`/`remove`) are in
  [reference.md](./reference.md#executor-config).

---

## 4. Smoke test: confirm it's wired

Have your agent (or you) run a read-only command:

```bash
gbc tree                 # render the whole .gbc dependency tree (empty tree for a fresh project)
gbc doctor check         # consistency lint; prints "✔ consistent" when clean
```

Over MCP, call the `tree` or `check_consistency` tool. If it returns, GBC is reachable.

---

## 5. Next steps

- Understand what GBC actually protects → [concepts.md](./concepts.md)
- Change code safely under GBC → [workflow.md](./workflow.md) (recommended workflow)
- Look up a command / tool / executor config → [reference.md](./reference.md)
- You're an agent and your human asked you to wire GBC in → [onboarding-agent.md](./onboarding-agent.md)

> **One thing GBC does NOT do for you**: GBC gives abilities, not restraint. Who may edit `.gbc/`,
> when intent changes need human sign-off — those rules are printed by `gbc rules`, and their
> **enforcement** must come from your agent framework (e.g. a pre-tool-use hook). Installing GBC
> does not make you automatically safe; read `gbc rules` and wire the enforcement yourself.
