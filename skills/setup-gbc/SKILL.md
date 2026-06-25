---
name: setup-gbc
description: Set up GBC in the project you're working in — make the gbc MCP server available, register a test executor, set up a gbc-doc intent skill, and add GBC's operating rules to the project's instruction file. Run once per project you onboard, and again whenever the interpreter, environment, language, or test runner changes. Assumes GBC the tool is already installed (see the GBC tool repo's docs/for-agents.md, step ①).
disable-model-invocation: true
---

# Set up GBC in the working project

Nice — you're wiring GBC into a project. This walks you through it; it should take only a few minutes.

Two things stay distinct throughout:

- **The working project** — the project you're in right now. Everything here is set up for it.
- **The GBC tool repo** — `guarantee-based-coding` (its `serve.py`, the interpreter that runs it, and the
  templates next to this skill). You read from it and point at it.

**You know your own environment** — how you register an MCP server, how you install a skill, which Python
environment is the right one. This skill gives you the GBC-specific facts and the goals; you reach them
your own way. It won't tell you to drop a particular config file or run a particular command, because that
depends on your setup, not on GBC.

This is prompt-driven, not a script: look at the project, show your human what you found, agree on the
details, then set things up — taking the decisions one at a time, each opened with a sentence of plain
context (your human may not know the terms).

## 1. Look at the working project

- **What runs its tests** — `pyproject.toml` / `pytest.ini` (pytest), `package.json` (jest/vitest),
  `go.mod`, `Cargo.toml`, and so on.
- **Which instruction file** it uses for agent guidance (e.g. `CLAUDE.md`, `AGENTS.md`), and whether GBC
  rules are already in it.
- **Whether a `gbc-doc` skill** is already set up for it.
- **Where the GBC tool repo lives**, and which interpreter runs it — ask your human if you're unsure.

## 2. Agree on the details, one at a time

**A — How this project's tests are run.** GBC backs every guarantee with a test, so it needs the command
that runs them, with `{file}` standing in for a test selector (e.g. `pytest {file}`). If you can't infer
it, ask your human. Note the working directory and anything the tests need in their environment (e.g.
`PYTHONPATH`). Give this a **project-scoped name** like `pytest-<project>`, since GBC keeps executors
together by name across projects — a bare `pytest` would collide with another project's.

**B — Which instruction file** the operating rules go into, and **how much you do on your own vs. run past
your human** (see step 3) — that balance is theirs to set.

## 3. Set things up

Each item below says *what to achieve* for the working project. *How* you achieve it is yours.

- **Make the gbc MCP server available to yourself**, pointed at the working project. The server starts as:
  ```
  <interpreter>  <gbc-tool-repo>/serve.py  <working-project-root>
  ```
  Register it whatever way you add MCP servers. (The working-project root is passed as that argument, not
  through an environment variable. If your interpreter is a Windows Python called from WSL, the two paths
  are handed to a Windows process, so write them in Windows form.) Once the server is available, GBC's
  tools show up — **read their descriptions**; they tell you how to create guarantees, register executors,
  verify, and look up dependencies. This skill won't restate them.
- **Register the test executor** from step 2A, using GBC's own tooling (its description has the exact
  shape). `templates/executor-pytest.jsonc` is an example config to adapt.
- **Set up a `gbc-doc` intent skill** for the working project, so edits to its `gbc.md` intent files have
  one place to go through. Build it from the templates here (`templates/gbc-doc-wrapper.sh` points the GBC
  intent CLI at the working project; `templates/gbc-doc-SKILL.md` is its description) and install it the
  way you install skills.
- **Add GBC's operating rules** to the instruction file from step 2B (`templates/operating-rules.md`).
  These are a **recommended** way of working — treat them as a sensible default, and let you and your human
  settle the actual granularity.

## 4. You're set

Let your human know GBC is ready for the project. If your MCP setup needs a reload or restart to pick up
the new server, say so. Re-run this skill whenever the interpreter, environment, language, or test runner
changes.

## Good to know

Executors are shared across projects in the GBC tool repo, keyed by name — which is exactly why a
project-scoped name matters.
