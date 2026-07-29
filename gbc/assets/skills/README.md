# GBC pre-authored skills (for CLI-only agents)

This directory ships **pre-authored skills** that teach an agent how to drive GBC
through its plain `gbc ...` commands — the CLI-side equivalent of the MCP tool
descriptions. They exist for agents that don't speak MCP, or where MCP is
inconvenient.

`gbc setup` points users here by absolute path; copying the skill files into
wherever their agent discovers skills is up to them (every framework reads skills
from a different place — GBC materializes the files, the user places them).

> The skill files themselves are added in a later batch. This README keeps the
> directory present so it ships in the wheel and `gbc setup` always has a real path
> to hand out.
