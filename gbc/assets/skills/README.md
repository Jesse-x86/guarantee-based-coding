# GBC pre-authored skills (for CLI-only agents)

This directory ships **pre-authored skills** that teach an agent how to drive GBC
through its plain `gbc ...` commands — the CLI-side equivalent of the MCP tool
descriptions. They exist for agents that don't speak MCP, or where MCP is
inconvenient.

`gbc setup` points users here by absolute path; copying the skill files into
wherever their agent discovers skills is up to them (every framework reads skills
from a different place — GBC materializes the files, the user places them).

## What's here

- **`gbc-cli/`** — teaches an agent to drive GBC through its `gbc ...` commands
  (the CLI-side equivalent of the MCP tool descriptions). Point your agent at
  `gbc-cli/SKILL.md`.
