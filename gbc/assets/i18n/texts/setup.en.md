# Wiring GBC into your agent

GBC is installed. This is the wiring guide: it tells you **where the endpoints and
files are** so your agent can reach them. It does **not** dictate *how* to wire them —
that depends on how your particular agent framework loads MCP servers and skills.
GBC only hands you the coordinates; you (or your agent) do the connecting.

There are two independent ways to give an agent GBC's abilities. Use whichever your
agent supports; you may use both.

---

## Option A — MCP (recommended when your agent speaks MCP)

GBC ships a stdio MCP server exposing both subsystems: the guarantee engine
(guarantee / dep / verify / refactor / tree / consistency / executor) **and** the
intent documents (doc show / check / set-* / sync / migrate).

**The endpoint** — start the server with:

```
gbc mcp up <ABSOLUTE_PATH_TO_YOUR_PROJECT>
```

Register that command as an MCP server wherever your framework keeps its MCP config.
A typical stdio entry looks like (adapt to your framework's schema):

```
{{
  "command": "gbc",
  "args": ["mcp", "up", "/abs/path/to/your/project"]
}}
```

Notes:
- The project root is passed as that argument; the server keeps all mutable state
  under your project's `.gbc/` (created on first write — you do not need to pre-make it).
- If `gbc` is not on PATH for your launcher, use the interpreter form:
  `<python> -m gbc.entry mcp up <project-root>`.
- After registering, reload / reconnect MCP so your agent picks up the tools.

---

## Option B — Skills (for agents that don't use MCP, or where MCP is inconvenient)

Because every GBC ability is also a plain `gbc ...` command, an agent that can run
shell commands can use GBC through a set of **pre-authored skills** that teach it
which commands to run. This is the CLI-side equivalent of MCP tool descriptions.

**The files** — the bundled skills live here:

```
{skills_dir}
```

Copy (or symlink) those skill files into wherever your agent discovers skills. GBC
does not place them for you, because every framework reads skills from a different
location — materializing the files is ours, placing them is yours.

---

## Verify it works

Once wired, have your agent run a read-only call — e.g. the `tree` tool over MCP, or
`gbc tree` on the CLI. If it returns your project's dependency tree (or an empty one
for a fresh project), GBC is reachable.

## One thing GBC does NOT do for you

GBC gives abilities, not restraint. The safety rules (who may edit `.gbc/`, when
intent changes need human sign-off) are printed by `gbc rules`, and their
**enforcement** must come from your agent framework (e.g. a pre-tool-use hook) — the
same hook applies whether the ability arrived via MCP or CLI. Installing GBC does not
make you automatically safe; read `gbc rules` and wire the enforcement yourself.
