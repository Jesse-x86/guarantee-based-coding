## Working under GBC (recommended)

What follows is a **recommended** way of working, not a hard rule. **You and your human decide
which changes need their sign-off and how autonomous you can be** — this is just a sensible
default. This project's test executor is named **`{{EXECUTOR_NAME}}`**.

**Two layers of contract**

- **Intent (gbc.md)** — architectural truth, usually owned by your human. When you change it, go
  through the `gbc-doc` entry so the structure and parent/child consistency are kept by a program,
  not by hand.
- **Guarantee** — a named behavior a file currently provides and others depend on. It may evolve;
  the moment you intend to break one, tell every dependent so they can fix in step.

**The rhythm: settle intent first, then implement**

1. Before writing code, work out the intent (gbc.md) this change touches and align with your human;
   once it's settled, it *is* the spec you implement against.
2. Then implement in dependency order: read the settled intent + interfaces → write the
   implementation → work out which of the other side's *behaviors* you rely on, and register the
   dependency/guarantee with GBC's tools (see each tool's own description for how) → run the
   affected guarantees. If you discover the intent itself needs to change mid-way, go back to
   step 1 and re-align rather than silently drifting.

**Reference files with `[[project-relative-path]]`.** When gbc.md prose points at a code file or
symbol, write it as `[[app/core/models/game.py]]` or `[[app/core/models/game.py:GameSpec]]` — a
path from the repo root, wrapped in `[[ ]]`. Don't use `../` relative paths: a relative ref breaks
when either side moves and reads differently from each referrer, whereas a `[[ ]]` ref is one
canonical string per target that the refactor tools rewrite automatically when the target moves.
(Data directories, HTTP routes, and ADR links don't need `[[ ]]`.)

**Moving or renaming? Use the refactor tools — never hand-fix the graph.** Relocating a file or
renaming a symbol desyncs every path-addressed reference (dependency edges, reverse `dependents`,
`[[ ]]` prose refs). `refactor_file(old, new)` moves a file/dir + its `.gbc` metadata and rewrites
all of them in one shot (and auto-disables the moved file's guarantees until you fix their tests);
`refactor_func` / `rename_guarantee` do the same for symbol / id renames. After a refactor: fix
imports, move the test files and `update_guarantee(test=...)`, then `enable_guarantee` each disabled
id. `refactor_file` is idempotent — if you already moved the file by hand, it just reconciles the
stale references.

**Stuck mid-refactor or on a circular dependency? `disable_guarantee` is the escape hatch.** It
keeps a guarantee's id and edges while suspending born-green for it, so you don't have to tear down
dependencies to make a multi-step change. `enable_guarantee` re-runs born-green and refuses if it
still fails. Disabled guarantees stay **loud** — `check_consistency` reports them until you enable
them back, so they can't rot silently.

**One small habit.** Narrow tests assert the **promise**, not the **implementation** —
`assert r is not None` usually beats `== some exact value`. Lean narrow; a false alarm costs more
trust than a missed one.

For the fuller picture, see the GBC tool repo's `docs/manual_EN.md`.
