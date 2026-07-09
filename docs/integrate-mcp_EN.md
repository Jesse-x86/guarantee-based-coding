# Connecting GBC to Your Own Agent (MCP)

**中文版: [integrate-mcp.md](./integrate-mcp.md)**

> For entry points see [for-agents.md](./for-agents.md) (for agents) / [for-humans_EN.md](./for-humans_EN.md) (for humans). This document expands the "connect MCP" step of the manual [manual_EN.md](./manual_EN.md) (cross-platform, custom clients, tool inventory).

GBC's guarantee capabilities (creating/verifying guarantees, registering/reverse-looking-up dependencies, consistency check-ups) are exposed through an **MCP server**.
Any agent that supports [MCP](https://modelcontextprotocol.io) (Claude Code, Cursor, a custom agent, ...)
can invoke it as a set of tools. This document only covers **how to connect**, not the concrete code-change workflow.

## Which tools it exposes

Server name `gbc`, stdio transport. Tool surface (corresponds to `app/interface/mcp.py`):

| Group | Tools |
|------|------|
| Guarantee lifecycle | `create_guarantee` (born-green, runs the test on the spot, refuses on failure), `update_guarantee`, `retire_guarantee` (refuses if there are still dependents) |
| Dependency edges (bidirectional write) | `add_dependency` (with `guarantee_id` = behavior dependency, auto-writes the reverse edge; without = free symbol dependency), `remove_dependency` |
| Read / reverse lookup | `list_provides`, `list_depends_on`, `who_depends_on` (replaces grep), `check_consistency` |
| Verification | `verify_provider` (three-bucket summary by the heavy threshold), `verify_guarantee` (names a single guarantee, ignores heavy) |
| Executor | `upsert_executor` (defines "how to run tests": command template + cwd + timeout + environment-variable operations) |

All tools return a JSON string; on error they uniformly return `{"error": ...}` rather than throwing an exception into the MCP runtime.

## Prerequisite: which Python environment to run in

GBC is a standalone tool, **run it in its own environment** (separate from your target project's environment). Install dependencies in the tool repo:

```bash
pip install -r requirements.txt   # typer[all] / pydantic / mcp
```

> Metadata is stored under the target project's `.gbc/`, so it doesn't pollute the target code; but the **process** is launched with GBC's own interpreter.

## Startup contract (key)

```
python <tool-repo>/serve.py <absolute path to the target project root>
```

There are two things you must do; the reasons are written in the comments at the top of `serve.py`:

1. **The target project root is passed via argv[1], don't rely on environment variables.** Cross-platform invocation (see below) can't pass env through; and the server
   needs to locate `.gbc/` relative to this project root. One server instance is locked to one project root.
2. **Invoke `serve.py` by absolute path.** This way `sys.path[0]` is the tool-repo directory, and the import always resolves to GBC's own
   `app/` package, and won't get hijacked by a same-named `app/` in the target project based on cwd.

The server uses stdio + JSON-RPC, with output forced to UTF-8.

## Connecting Claude Code

Put a `.mcp.json` (project-level MCP config) at the project root:

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/path/to/python",
      "args": [
        "/abs/path/to/guarantee-based-coding/serve.py",
        "/abs/path/to/your-project"
      ]
    }
  }
}
```

- `command` = the interpreter that runs GBC (the one with requirements installed).
- `args[0]` = the absolute path to `serve.py`; `args[1]` = the absolute path to your project root.
- After reopening Claude Code, the tools appear as `mcp__gbc__*` (e.g. `mcp__gbc__list_provides`).

## Connecting any MCP client

The same stdio startup contract. Most clients' config is just a `command` + `args` array, the same shape as above.
As long as the client can spawn a process and speak stdio MCP, it can connect to GBC. A custom agent can directly use the MCP SDK for the corresponding language
to connect to a stdio server; fill in command/args as above.

## Cross-platform: WSL calling Windows Python (common pitfall)

If the agent runs in WSL while GBC's Python is on Windows (e.g. a conda env), `serve.py` has already shouldered
two pitfalls for you (env variables not passing through, cwd import hijacking), so **you only need to follow the startup contract above**, no extra setup needed.
Configuration example (real-world):

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/mnt/c/Users/<you>/miniconda3/envs/<env>/python.exe",
      "args": [
        "D:/path/to/guarantee-based-coding/serve.py",
        "D:/path/to/your-project"
      ]
    }
  }
}
```

Note: `command` uses the `.exe` path visible to WSL (`/mnt/c/...`), while the paths in `args` use the **Windows form**
(`D:/...`), because they are the argv passed to the Windows process. On the same platform (pure Linux / pure Windows) you don't need to worry about this,
just use each platform's native absolute paths.

## Verifying the connection

Once connected, have the agent call a read-only tool to confirm the link works:

- `check_consistency()` → returns `[]` means the `.gbc` graph is consistent (an empty project also returns `[]`).
- `list_provides("<relative path to some source file>")` → returns the guarantees registered for that file (an empty object if none).

> Path arguments always use **project-root-relative** posix paths (e.g. `app/core/maker/maker.py`), not absolute paths.

## Mental model

- One server instance = one project root. For multiple projects, configure multiple server entries (with different `args[1]`).
- MCP only exposes the **guarantee-side** capabilities. The human-held **intent documents** (`gbc.md`) go through another channel — the intent-tree editor / its CLI,
  see [intent-editor-and-skills_EN.md](./intent-editor-and-skills_EN.md).
