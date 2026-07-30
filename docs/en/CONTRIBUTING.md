# Contributing

> Language: [简体中文](../../CONTRIBUTING.md) | **English**

Thanks for your interest! This guide covers how to safely change code in this project.

## Two install modes: contributing vs just using

This project *is* the GBC tool implementation, and also its first user. Pick the install mode
that matches your goal:

| Goal | Command | Notes |
|------|---------|-------|
| **Contribute code / run tests** | `pip install -e .` | Editable install; `import gbc` hits the source directly — no reinstall needed after edits |
| **Just use the tool** | `pipx install .` | No `-e`; installs a frozen package, unaffected by your local source tree |

## Setting up (contributors)

```bash
# 1. Test dependencies (your existing conda/venv)
pip install -r requirements.txt

# 2. GBC tool itself, editable
pip install -e .
```

> **Note:** If the project directory lives on some special mounted filesystem (e.g. a WSL 9p
> share), `pip install -e .` may fail because `chmod` isn't supported there (setuptools calls
> `chmod` while generating egg-info). If you hit this, copy the repo to a regular local
> filesystem path (e.g. under `/tmp` or your home directory) and install from there.

## Running tests

With `pip install -e .`, `import gbc` should already resolve to source (editable installs map
via a `.pth`/finder), so **running pytest from inside the project root is fine**:

```bash
cd /path/to/guarantee-based-coding
pytest tests/
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
