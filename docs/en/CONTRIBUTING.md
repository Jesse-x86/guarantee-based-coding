# Contributing

> Language: [简体中文](../../CONTRIBUTING.md) | **English**

Thanks for your interest! This guide covers how to safely change code in this project.

## What makes this project different: dogfooding

This project *is* the GBC tool implementation, and also its first user. Your dev setup needs
**two isolated Python environments**:

| Purpose | Environment | Notes |
|---------|------------|-------|
| **Run tests / write code** | conda / venv (yours) | Install deps from `requirements.txt` |
| **Use GBC tools** | pipx | `pipx install .` freezes the tool itself |

**Why separate?** While hacking on the source, the `gbc` command you're using must come from the
installed version — breaking the source won't cut the ladder from under your feet.

## Setting up

```bash
# 1. Test environment (your existing conda/venv)
pip install -r requirements.txt

# 2. GBC tool itself (isolated via pipx)
pipx install -e .    # editable from source, still through pipx venv
```

## Running tests

**Critical: do not run from the project root.** Otherwise `import gbc` resolves to the source
directory, not the installed package — you're not testing what you think you are.

```bash
# Correct: run from outside the project root
cd /tmp
pytest /path/to/guarantee-based-coding/tests/
```

> GBC's current project root defaults to the process's cwd — no environment variable needed.
> This repo's own tests inject a temp directory directly via `set_current_project()`, so they
> don't depend on cwd or any env var.

## Workflow

Follow this project's `.gbc` intent docs.

Core rhythm:
1. **Plan** — read relevant `.gbc/**/gbc.md` to understand the change's impact radius
2. **Intent first** — requirement → draft gbc.md changes → human approval → `gbc doc` commit
3. **Implement** — write code → write narrow tests → `gbc guarantee create` → `gbc verify`
4. **Verify** — top-level `gbc verify` on all affected guarantees

Never hand-edit `.gbc/**/*.json` or `.gbc/**/gbc.md`.

## Guarantee conventions

- id format: `<symbol>.<behavior>` (e.g. `get_config.never_none`)
- Write narrow tests: assert behavioral promises (non-null / type / raises), not implementation details
- Born-green: `create_guarantee` runs the test on the spot and refuses to register if it fails

## Commits

- Chinese or English commit messages are both fine
- Large refactors in steps, keeping each step independently revertible
- Commits touching the guarantee graph or intent docs: explain the blast radius in the body
