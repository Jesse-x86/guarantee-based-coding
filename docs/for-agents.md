# Wiring GBC in (for Agents)

Hi. If you're reading this, you're working inside a project and your human wants to use GBC — glad
you're here to wire it up for them. It's not much: first get the GBC tool ready, then onboard each
project once.

Two roles you'll use throughout:

- **The working project** — the project you're in right now, where GBC gets wired in.
- **The GBC tool repo** — the `guarantee-based-coding` repo itself; `serve.py`, the templates, and
  the `setup-gbc` skill all live here. You read from it and point at it.

## ① First time: get the GBC tool ready

Do this once; every project reuses it. This step only touches the **GBC tool repo**.

1. **Find the GBC tool repo.** If you're not sure where it is, ask your human for the path.
2. **Install its dependencies.** It ships a `requirements.txt` — install it into a suitable Python
   environment. Which environment and how is up to you and your human's conventions.
3. **Install the `setup-gbc` skill.** It's under the GBC tool repo's `skills/setup-gbc/`; install it
   the way you install skills. You'll use it every time you onboard a project.

Once done, these three are good for all projects.

## ② Each project: run setup-gbc to onboard

Run the `setup-gbc` skill inside the **working project** and it walks you through wiring GBC in —
usually within one session. It registers the gbc MCP server, a test executor, a `gbc-doc` intent
skill, and drops GBC's operating rules into the project's instruction file (those rules cover the
conventions you'll follow, including how to write references and how to move/rename code safely).

> Why once per project? GBC points at the working project, and the test executor follows that
> project's environment and language — switch projects and it naturally needs reconfiguring. That's
> why it's a re-runnable skill rather than a one-time install.

Once onboarded, [manual.md](./manual.md) covers how to change code safely under GBC in full.
