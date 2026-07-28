## Working under GBC (recommended)

What follows is a **recommended** way of working, not a hard rule. **You and your human decide
which changes need their sign-off and how autonomous you can be** — this is just a sensible
default. This project's test executor is named **`{{EXECUTOR_NAME}}`**.

**Audience: the top-level agent.** Default recommended usage is **planner-only** (plan, align
intent, dispatch, gate). Planning and implementation in one agent is allowed when the change is
small or your human prefers it, but it is not the recommended default. Day-to-day coding is
handed to subagents.

### Two layers of contract

- **Intent (gbc.md)** — architectural truth, usually owned by your human. When you change it, go
  through the `gbc-doc` entry so the structure and parent/child consistency are kept by a program,
  not by hand. Each folder's `gbc.md` has **intent**, **internal constraints**, and **file
  entries** — all three are part of the contract you plan against and ship in briefs.
- **Guarantee** — a named behavior a file currently provides and others depend on. It may evolve;
  the moment you intend to break one, tell every dependent so they can fix in step.

### What the top-level agent does (planning)

1. **Work out which folders/files this change touches.** Read the **relevant**
   `.gbc/<path>/gbc.md` files (the folder you will change, plus an ancestor when you need to
   check whether the change belongs there). Prefer plain file reads of those docs. Use `tree`
   only when you need a one-shot architecture overview at the start of a large task — not as the
   entry ritual for every edit. Context should stay scoped to the change, not the whole project.
2. **New human demand → align intent before code.** If the change needs new or updated gbc.md,
   draft the delta and **check it with your human**; land it through `gbc-doc` only after they
   **explicitly approve**. **Shipped default: this confirmation line is present.** If your human
   dislikes the friction, they may ask you to **remove this requirement from the instruction
   file** — then you simply will not see a rule that forces intent confirmation, and you may act
   more autonomously. That is allowed; understand that with no human watching intent landings,
   **silent architectural drift risk goes up**. You should not re-invent a private "bypass flag"
   while the line is still here: either the rule is in your instructions (confirm) or the human
   deleted it (absent).
3. **Dispatch in dependency order** (providers before dependents). Prefer subagents for
   implementation.
4. **Every subagent brief must carry the duty scope** (this is the token-saving move — do not
   send the whole `.gbc` tree):
   - **target path(s) it may write** — prefer **one primary file** per subagent task
   - that **other files are read-only** unless the brief explicitly lists them as writable
   - the **sliced** intent **and** internal constraints (and file-entry lines that apply) from the
     relevant gbc.md — paste them into the prompt; do not say only “go read `.gbc`”
   - what it may change / must not cross
   - this project's executor name (`{{EXECUTOR_NAME}}`) and that **all guarantee runs go through
     GBC tools (MCP by default; or the project's skill/CLI entry if that is how GBC was wired) —
     never `pytest` / the test runner by hand**
   - that when it writes behavior worth depending on, it must **author a narrow test and register
     the guarantee** (and any behavioral dep) before the task is “done”
5. **Final acceptance after they return.** Subagents should self-verify their scope; **you** run
   affected guarantees again **via GBC tools only** as the architecture-level acceptance. On red,
   use `who_depends_on` / `list_provides` / `list_depends_on` to see what broke and who cares —
   on green, do not burn tokens pulling the graph. If intent itself was wrong, re-align; do not
   let implementation quietly rewrite architecture.

### What to hand a subagent (implementation contract)

Subagents should **not** re-pull the architecture graph; the brief already carries their scope.
They:

1. **Focus on the target file** (single-file edit by default). Paths outside the writable list are
   **read-only** — you may read them for context; do not "while I'm here" rewrite them.
2. Implement inside the brief's paths and constraints.
3. When the code you write exposes a **behavior others will rely on** (or you rely on another
   module's behavior, not only its signature): **proactively write a narrow test and register it
   with GBC** (`create_guarantee` / `add_dependency` as appropriate) before calling the task done.
   Free symbol deps for signature-only; named guarantee + test for real behavior. Prefer reusing an
   existing guarantee when it already covers the need. **Silent unregistered behavioral deps = not
   done.**
4. **Self-verify** affected guarantees in scope **only through GBC tools** (MCP default; skill/CLI
   if that is the install). Do **not** invoke the underlying test runner yourself — hand-running
   makes it too easy to “fix” a test to green and hollow out the gate.
5. On red: restore the behavior or escalate to the top-level agent so dependents can adapt.
   **Never loosen or retire a test just to turn red green.**
6. If the **intent** is wrong mid-flight: stop and return to the top-level agent; no silent drift.
7. Moves/renames go through `refactor_file` / `refactor_func` / `rename_guarantee`. Afterward:
   fix imports, move tests + `update_guarantee(test=...)`, then `enable_guarantee` each disabled
   id.

**Acceptance split.** Subagent: verify own scope before returning. Top-level (architecture) agent:
final gate on the change after dispatch returns. Do not skip the top-level pass just because the
subagent reported green.

If the top-level agent implements without a subagent, the same implementation contract applies
to it — only the dispatch step is skipped; it still self-verifies, and intentional multi-step
work still ends with a conscious final verify.

### Convenience rules (both roles)

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

**Tool roles (token model)**

| Tool | Who / when |
|------|------------|
| Read relevant `gbc.md` | Top-level while planning; subagent only if the brief is incomplete for its folder |
| `tree` | Top-level architecture overview — not every edit |
| `who_depends_on` / `list_provides` / `list_depends_on` | After a red gate (or when deliberately breaking a guarantee) |
| `gbc-doc` | Only compliant write path for gbc.md; land only after human approval while that rule is in your instructions |
| Guarantee CRUD + `verify_*` (MCP default) | Register and run gates — never the bare test runner |

**One small habit.** Narrow tests assert the **promise**, not the **implementation** —
`assert r is not None` usually beats `== some exact value`. Lean narrow; a false alarm costs more
trust than a missed one.

For the fuller picture, see the GBC tool repo's `docs/manual_EN.md`.
