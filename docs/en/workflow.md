# Working under GBC

> Language: [简体中文](../zh/workflow.md) | **English**

This page covers **how to change code safely once GBC is integrated**: the recommended workflow,
how to write intent docs, and a few traps that fail silently. For concepts see
[concepts.md](./concepts.md); for a command lookup see [reference.md](./reference.md).

It's written in an agent-facing voice; humans can read it too, or hand it to a trusted agent. It's
based on the "recommended / standard" scenario — adjust what the agent handles vs. what's left to
human decision according to your actual authority split.

The bundled **gbc-workflow** skill applies this workflow with either MCP or CLI. Use
**gbc-cli** for command syntax when choosing CLI; the transport does not change authority or
acceptance. `gbc setup` prints the bundled skill directory. Read the skill there, or integrate
it using the client's project-level convention when needed; no global installation is required.

---

## Role default: you are the top-level agent

This workflow assumes **you are the top-level agent**. Recommended flow:

**Plan → align intent → dispatch → final acceptance.**

- **Plan**: work out which folders the change touches; read the **relevant**
  `.gbc/<path>/gbc.md` (the current folder, an ancestor when needed). Use `gbc tree show` once at the
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
  **held and approved by the human**; the agent drafts it. Change it through `gbc intent` (MCP intent
  tools / CLI), never by hand.
- **Guarantee** — a **named behavioral promise** a module currently provides and others depend on.
  It may evolve, but the moment you intend to break one, tell every dependent so they fix in step.

---

## Two phases, and the order matters

**Never jump to code before the architecture is clear.**

### Phase 1: architecture (draft first; default requires explicit human approval before landing)

Start with evidence: read the relevant intent, existing terminology and decisions, then inspect
the affected interfaces, consumers, tests, and observed failure. Separate confirmed facts,
inferences, and unresolved choices. State the intended outcome and scope, explain your recommended
approach, and identify which evidence supports it. A bug covered by the current intent may need
no intent delta; do not manufacture one or ask the human to approve the same decision again.

Ask only when an unresolved choice materially changes behavior, scope, compatibility, authority,
or a costly-to-reverse decision, and available evidence cannot settle it. Resolve discoverable
facts yourself; handle routine implementation choices within scope. When choices depend on each
other, resolve the consequential upstream choice first. Present a recommendation and its tradeoff,
not a questionnaire about every implementation detail. Existing authorization continues to apply.

When intent must change, draft the **whole relevant delta** with its reasons and remaining choices
before writing it. Under the default approval rule, land a new delta through `gbc intent` only after
**explicit human approval**, then run `gbc intent check`. **The landed `gbc.md` is the spec you
implement against.** Tool consistency does not approve a design. Preparing a draft does not require
writing managed intent files.

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

**Spec-first**: before dispatching a subagent / writing code, establish whether the existing intent
already covers the work. If it changes, draft it, obtain required approval, and land it through
`gbc intent` before implementation. When creating a folder / file, **register
its intent / `# 文件` entry first**, don't backfill after the code.

### Reuse vocabulary and preserve reasons

Look first in existing intent, concepts, glossaries, and decision records. Use the same name for
the same concept; explain different meanings by context instead of imposing one global meaning.
Define an ambiguous term with a concrete example and a boundary case. In GBC, a free symbol
dependency records a signature/existence dependency; a named guarantee protects behavior. Neither
the word "dependency" nor a successful import tells you which promise a consumer needs.

For a material decision, preserve the chosen boundary and why it was chosen in the project's
existing documentation convention. Keep rejected alternatives and proposals distinguishable from
adopted decisions. Reuse a glossary or ADR if one exists; do not require a new CONTEXT file, ADR,
or vocabulary document for every task. Keep `gbc.md` about current roles and constraints; link to
decision history where useful rather than copying the discussion into it. For example, GBC's
intent subsystem keeps disk operations in `base` and treats CLI, MCP, and the editor as thin
surfaces; a new editor feature should use that existing boundary unless a change is approved.

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
- **Top-level agent**: maintains human-held intent through GBC intent tools, bounds task scope, reviews
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

Start with the **consumer's behavioral promise**: who relies on which provider interface, under
what input or state, and what observable outcome they need. Query and reuse a suitable existing
guarantee before creating another. Signature/existence alone still uses a free symbol dependency.
Select the smallest test that distinguishes a realistic violation from correct behavior, exercising
the actual boundary that carries the promise. Narrow means focused scope, not weak assertions.

Assert exact values, ordering, errors, or output structure when the consumer relies on them. Use
non-null/type-only checks only when those are the whole promise; avoid incidental implementation
details. GBC's editor file-meta contract, for example, distinguishes an invalid path (**HTTP 400**)
from missing metadata (**HTTP 200 with `meta: null`**). A non-null response alone cannot protect the
frontend's distinction. These values are contract evidence, not a claim of a new editor test run.

A real repository example is removing dependencies when two symbols in one consumer share a
provider's guarantee (`tests/test_guarantee_deps.py`). After removing the first symbol's dependency,
retirement must still be refused; after removing the last, retirement is allowed. The outcome
protects the consumer, whereas merely asserting that a metadata object exists would miss the bug.
Other consumers and same-named guarantees on other providers must remain independent.

Explain which plausible defect the test would detect. When useful and authorized, demonstrate
that sensitivity with a controlled regression or mutation, verify through GBC, restore the code,
and verify again. It is not a universal red-first requirement. An import error, broken environment,
or a mock directly returning the asserted bad value does not by itself demonstrate detection of
the target defect. Mocks may isolate external boundaries, but must not replace the behavior the
guarantee claims to protect. Report actual checks and limitations separately from test design.

**Born-green remains unchanged**: creation and runner changes must pass the existing gate. It
checks the current implementation; it does not prove the test is sensitive to a future defect.
Do not disable guarantees or weaken assertions just to register a failing test.

---

## A few traps that fail silently

These are worth carrying in your head from day one, because they fail **silently**:

- **A guarantee test must detect its target defect.** Choose a meaningful input/state and observe
  the real promise. A happy-path test can be sufficient for that promise; adding an artificial bad
  fixture is not proof of sensitivity. Use the narrow-test rule above to justify what it catches.
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
broke right now, would this test detect that defect?"* If no, improve the behavioral test before
treating it as protection. A passing test and a registered edge alone do not establish sensitivity.

### Selected design inspiration

This workflow selectively adapts Matt Pocock's [grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md),
[tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md), and
[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md):
investigate facts before consequential questions; test behavior through meaningful interfaces;
reuse vocabulary, scenarios, and decision reasons. GBC adapts these ideas to its existing authority
rules and born-green gate. It does not require an exhaustive interview, approval for every test
boundary, universal red-first, or a new context document. These are design references, not runtime
dependencies or a requirement to install the source skills.

---

## Common pitfalls

| Easy to hit | Do this instead |
|---|---|
| Hand-editing gbc.md or json under `.gbc/**` | gbc.md through `gbc intent`; deps / guarantees through GBC tools |
| Jumping to code once the architecture is clear | Draft gbc.md → human approves (default) → then implement in topology order |
| A subagent rewriting half the tree "while it's here" | The brief names the writable target file; everything else read-only |
| Skipping the top-level verify because the subagent said green | Subagent self-verifies; the top-level still does final acceptance |
| An assertion that is weaker or stricter than the consumer's promise | Assert the required behavior, including exact values when contractual |
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
