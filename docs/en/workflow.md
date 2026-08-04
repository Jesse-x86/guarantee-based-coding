# Working under GBC

> Language: [简体中文](../zh/workflow.md) | **English**

This page covers **how to change code safely once GBC is integrated**: the recommended workflow,
how to write intent docs, and a few traps that fail silently. For concepts see
[concepts.md](./concepts.md); for a command lookup see [reference.md](./reference.md).

It's written in an agent-facing voice; humans can read it too, or hand it to a trusted agent. It's
based on the "recommended / standard" scenario — adjust what the agent handles vs. what's left to
human decision according to your actual authority split.

---

## Role default: you are the top-level agent

This workflow assumes **you are the top-level agent**. Recommended flow:

**Plan → align intent → dispatch → final acceptance.**

- **Plan**: work out which folders the change touches; read the **relevant**
  `.gbc/<path>/gbc.md` (the current folder, an ancestor when needed). Use `gbc tree` once at the
  start of a large task for an architecture overview — not as the entry ritual for every edit.
- **Dispatch**: prefer subagents for implementation, in dependency order (providers before
  dependents).
- **Final acceptance**: after a subagent returns, **you** re-run the affected guarantees through
  GBC tools.

Planning and implementation in one agent is fine for small changes; day-to-day coding is not the
top-level agent's default role.

---

## Two layers of contract

- **Intent (gbc.md)** — the single source of truth for the architecture, the highest contract,
  **held and approved by the human**; the agent drafts it. Change it through `gbc doc` (MCP doc
  tools / CLI), never by hand.
- **Guarantee** — a **named behavioral promise** a module currently provides and others depend on.
  It may evolve, but the moment you intend to break one, tell every dependent so they fix in step.

---

## Two phases, and the order matters

**Never jump to code before the architecture is clear.**

### Phase 1: architecture (draft first; default requires explicit human approval before landing)

On a new demand, take the **whole** `gbc.md` delta as a **draft** and check it with your human;
land it through `gbc doc` only after **explicit approval**, then run `gbc doc check` for
consistency. **The landed `gbc.md` is the spec you implement against.**

> The default install writes "intent needs confirmation" into the operating rules. If your human
> asks you to delete that line from the instruction file, the rule simply disappears from your
> context and you may act more autonomously — with a higher risk of silent architectural drift.
> While the rule is still there, don't invent a private "bypass."

### Phase 2: implementation (machine-gated)

Prefer "one subtask, one target file" (the brief names the writable file, everything else
**read-only**). Follow dependency topology (providers first). The implementer:

1. Reads the approved scope (brief / gbc.md) + interfaces → writes the implementation.
2. Depended-on / newly-exposed behavior: signature-level uses `add_dependency`; concrete behavior
   means **proactively write a narrow test and register it with `create_guarantee`** (prefer
   reusing an existing guarantee). **A silent unregistered behavioral dep = not done.**
3. **Self-verify** in scope, through GBC tools only (`verify_provider` / `verify_guarantee`) —
   **never** hand-run `pytest` (hand-running makes it too easy to "fix" a test to green and hollow
   out the gate).
4. On red: restore the behavior, or escalate to the top-level agent so dependents adapt. **Never**
   loosen or retire a test just to turn red green.
5. If intent is wrong mid-flight → stop, return to Phase 1; no silent drift.
6. Moves / renames go through `refactor_file` / `refactor_func` / `rename_guarantee`.

### Phase 3: final acceptance (top-level agent)

After the implementer returns, the top-level re-verifies the affected guarantees through GBC tools.
**Do not skip this even if the implementer reports all green.** On green, don't pull the graph; on
red, use `who_depends_on` / `list_provides` / `list_depends_on` to see what broke and who cares.

---

## Writing intent docs

Each folder's intent lives in `.gbc/<path>/gbc.md`, in three sections:

- **`# 意图` (Intent)** = what this folder/file **is and why it exists** (role / purpose). Explain
  concepts inline or link them; leave no undefined terms.
- **`# 内部约束` (Internal constraints)** = what it **needs and must / must not do** (obligations
  and rules: what state it holds, what it consumes, what must precede what, what it must never
  touch). Local only; does not bubble up to the parent.
- **`# 文件` (Files)** = subfolders (name ends in `/`) + this folder's code files, one line of
  role each.

**The three sections are visibility scopes.** When intent-vs-constraints is unclear, ask per
sentence "who needs to know this?": intent = what an outsider needs (public contract); constraints
= what all internal files coordinate on and outsiders don't (package-private); a file entry = what
only that file needs (private). Use it mainly as a **sniffer for internal detail leaking up into
intent** — impl base (Pydantic vs dataclass), disk layout, internal mechanism belong in
constraints / file entries, not intent.

**Write the current state + prohibitions, never a diff against the past.** gbc.md is the *current*
contract. Cut these three drift baits:

- **Stage / version words** (`MVP` / `v0` / `for now`): project stage is a global fact, kept in the
  project instruction file, not repeated per folder.
- **Roadmap / wishes** (`will grow into X` / `leaves room to swap the backend`): delete, or move to
  an ADR / roadmap doc.
- **Migration narration** (`no longer uses X` / `changed to Y`): either a ghost → delete; or a
  regression guard → rewrite as a positive `never X` constraint. The only legitimate past-reference
  is an **explicitly labeled historical note** (`historical fact` / `legacy-compat`).

**Spec-first**: before dispatching a subagent / writing code, use `gbc doc` to write the intent and
get it reviewed, then implement against the landed gbc.md. When creating a folder / file, **register
its intent / `# 文件` entry first**, don't backfill after the code.

---

## Reference code with `[[project-relative-path]]`

When gbc.md prose points at a code file or symbol, write `[[gbc/app/core/models/game.py]]` or
`[[gbc/app/core/models/game.py:GameSpec]]` — a path from the repo root, wrapped in `[[ ]]`. **Don't use
`../` relative paths**: they break when either side moves and read differently from each referrer,
whereas a `[[ ]]` ref is one canonical string per target that `refactor_file` / `refactor_func`
rewrite automatically when the target moves. (Data dirs, HTTP routes, and ADR links don't need
`[[ ]]`.)

Guarantee ids follow a similar principle but are **path-free**: `<symbol>.<behavior>` (e.g.
`make_game.returns_html`), unique within the provider.

---

## Agent authority constraints (a safety recommendation)

Prevent architectural drift and "editing tests to green" without stopping the agent closest to an
implementation from closing its contract loop. Configure framework enforcement (e.g. Claude Code's
`pre-tool-use` hook) by **operation type**, not with a blanket "no GBC mutation" rule:

- **Every agent**: never hand-edit `gbc.md` or graph JSON; use GBC tools. Language/project-specific
  interface artifacts (a Python project may use `.pyi`) and guarantee tests are not mechanical graph
  metadata and stay with the implementer.
- **Top-level agent**: maintains human-held intent through GBC doc tools, bounds task scope, reviews
  new dependencies/guarantees, coordinates cross-scope breakage, and does final acceptance.
- **Subagent**: reads intent without editing it, maintains required interface artifacts with the code,
  and owns the local contracts introduced by the implementation—register actual dependencies, reuse or create required guarantees, maintain
  narrow tests that can genuinely go red, and run `verify_*`. By default it may not retire/disable
  guarantees, change intent, or refactor outside its brief; escalate or obtain explicit authority.
- Hooks block hand-edited metadata, intent changes, and unauthorized overreach; **do not block
  dependency registration, guarantee creation, or verification for subagents.** Enforcement is
  independent of MCP vs CLI.

---

## Narrow-test rule

Assert the **behavioral promise**, not the **implementation**: `assert r is not None` beats a
hard-coded value; `with pytest.raises(X)` beats checking an exact error message. **Lean narrow** —
an occasional missed alarm is acceptable, but a false alarm from an over-tight test during a
refactor rapidly erodes trust in the verification system.

---

## A few traps that fail silently

These are worth carrying in your head from day one, because they fail **silently**:

- **A guarantee test must be able to go red.** The deadliest failure isn't a missing test — it's a
  fixture that only walks the happy path, staying green even after the behavior breaks. A
  "non-empty" guarantee whose fixture can never produce empty is guarding nothing. Give the fixture
  a way to produce the bad value (empty / None / exception / duplicate) and confirm the test really
  goes red when the promise is violated. **Narrow ≠ soft.**
- **Promote the behavior you actually depend on.** Non-null, non-empty, raises-on-X, ordering,
  idempotence — these are behavior, not signature, and a free symbol dependency has no test
  guarding them. The classic silent crash: an upstream weakens "non-null" to "maybe null" and a
  downstream hits a NoneType, because non-null was never named. (Still default to free symbol deps;
  just don't leave a *behavioral* one unnamed.)
- **When a guarantee goes red, restore it or announce it — never loosen the test.** Relaxing or
  retiring a test to turn red green silently downgrades a real guarantee into fake safety. Breaking
  is allowed; breaking quietly is not — a red means either put the behavior back, or make every
  dependent adapt.

Smell test, every time you register a dependency or a guarantee: *"If the behavior I care about
broke right now, would a test actually go red?"* If no, you have a symbol dependency pretending to
be a guarantee, or a happy-path fixture pretending to be a test. Fix that first.

---

## Common pitfalls

| Easy to hit | Do this instead |
|---|---|
| Hand-editing gbc.md or json under `.gbc/**` | gbc.md through `gbc doc`; deps / guarantees through GBC tools |
| Jumping to code once the architecture is clear | Draft gbc.md → human approves (default) → then implement in topology order |
| A subagent rewriting half the tree "while it's here" | The brief names the writable target file; everything else read-only |
| Skipping the top-level verify because the subagent said green | Subagent self-verifies; the top-level still does final acceptance |
| A test asserting an exact return value (`== "<html>..."`) | Assert the promise: non-null / type / raises |
| Naming a guarantee for every dependency | Default to free symbol deps; upgrade behavioral ones lazily |
| Retiring a guarantee that still has dependents | Migrate / fix the dependents first (`retire` refuses) |
| Calling tools with absolute paths | Always use project-root-relative posix paths |
| Changing a big batch of files at once | Topology order, one file per step, run guarantees each step |
| Hand-fixing references after a move / rename | Use `refactor_file` / `refactor_func` (idempotent, rewrites `[[ ]]` too) |

---

## Stuck? `disable_guarantee` is the escape hatch

Stuck mid-refactor / on a circular dependency? `disable_guarantee` keeps a guarantee's id and edges
while suspending its born-green, so you don't have to tear down dependencies to make a multi-step
change. `enable_guarantee` re-runs born-green and refuses if it still fails. Disabled guarantees
stay **loud** — `gbc doctor check` reports them until you enable them back, so they can't rot
silently.
