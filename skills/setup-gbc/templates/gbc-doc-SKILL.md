---
name: gbc-doc
description: Recommended entry point for editing this project's .gbc intent docs (gbc.md). Use it to view / create / change / lint gbc.md — going through it keeps gbc.md's structure and parent/child consistency for you, so you don't have to track them by hand.
---

# gbc-doc: the entry point for editing gbc.md

Change `gbc.md` through this entry and its three-section structure + parent/child sync are kept by
a program — you don't maintain them by hand. **Whether to treat it as the only entry, and which
changes need your human's review, is for you and your human to settle** — this just makes "safe
editing" available.

## Invocation

```bash
bash {{WRAPPER_PATH}} <command> [args...]
```

`<folder>` is a project-relative path (e.g. `app/core/maker`); use `""` or `.` for the root.

## Commands

| Command | What it does |
|---------|--------------|
| `show <folder>` | View intent / constraints / entries |
| `set-intent <folder> "<text>"` | Set intent; auto-projects (single source) to the parent entry |
| `set-constraints <folder> "<text>"` / `set-file <folder> <name> "<desc>"` | Set internal constraints / add or change a file entry |
| `rm-entry <folder> <name>` | Remove a doc entry (does not delete the file on disk) |
| `check` / `sync` | Consistency lint / deterministically repair parent-child drift |

## How to write gbc.md (three sections)

- **`# 意图` (Intent)** = what this folder/file is and why it exists (role / purpose). Explain
  concepts inline or link them; don't leave undefined terms.
- **`# 内部约束` (Internal constraints)** = what it needs and what it must / must not do
  (obligations and rules). The test is "is this identity (→ intent) or a rule (→ constraints)".
- **`# 文件` (Files)** = subfolders (name ends in `/`) and code files, one line of role each.

**Reference code with `[[project-relative-path]]`.** When prose points at a code file or symbol,
write `[[app/core/models/game.py]]` or `[[app/core/models/game.py:GameSpec]]` — a path from the
repo root, in `[[ ]]`. Don't use `../` relative paths: they break when either side moves and read
differently from each referrer, whereas a `[[ ]]` ref is one canonical string per target that the
`refactor_file` / `refactor_func` tools rewrite automatically when the target moves. (Data dirs,
HTTP routes, and ADR links don't need `[[ ]]`.)

Settle the intent and align with your human first, then implement against it. Fuller guidance is in
the GBC tool repo's `docs/intent-editor-and-skills.md`.
