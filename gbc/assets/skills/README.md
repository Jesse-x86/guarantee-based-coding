# GBC pre-authored skills

This directory ships complementary skills for GBC reasoning and command use.
They are resources to adopt in an agent's skill system, not automatically
installed instructions or changes to global agent policy.

`gbc setup` points users here by absolute path; copying the skill files into
wherever their agent discovers skills is up to them (every framework reads skills
from a different place). Preserve each skill's supporting files; keep these two
folders as siblings when using their cross-links.

## What's here

- **[gbc-workflow](gbc-workflow/SKILL.md)** — guides intent planning, behavior
  guarantees, test evidence, vocabulary and consequential design decisions.
  Works with either MCP or CLI. Supporting references are loaded only as needed.
- **[gbc-cli](gbc-cli/SKILL.md)** — maps operations to `gbc ...` commands when
  MCP is unavailable or the agent prefers CLI. This is a command adapter, not a
  second copy of the workflow.

Use the workflow with the project's adopted authority and verification rules.
Neither skill grants permission to install tools, change hooks or take external
actions. Available command syntax remains in the CLI skill and `--help`;
the shipped manual is available through `gbc doc` or MCP documentation tools.
