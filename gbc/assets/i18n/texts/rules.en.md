# GBC Recommended Guardrails (author's suggestions)

> What follows is only **one recommended orchestration shaped by the author's personal
> development philosophy**. It is neither GBC's only valid use nor permission for an agent
> to make governance decisions on its owner's behalf. Agents should first fit the owner's
> existing development philosophy and authority model; humans are equally welcome to design,
> adapt, or explore other divisions of work and agent orchestration.
>
> At heart, GBC is only a tool for turning behavioral dependencies into repeatable automated
> tests. It does not prescribe who must write code, maintain tests, or invoke tools. Treat it
> as a foundation and develop the workflow that fits your project. The rules below are
> recommended defaults, not an enforced sandbox; actual enforcement still belongs to your
> agent framework (e.g. Claude Code's `pre-tool-use` hook).
> **Installing GBC does NOT make you automatically safe, nor does it adopt the author's workflow.**

If this philosophy fits your project, adopt the following rules in your agent instructions
(or enforce them through your framework):

1. **No agent hand-edits GBC-managed graph or intent files.** Change `gbc.md`
   only through the gbc intent entry point (MCP intent tools / CLI), and change dependency / guarantee JSON only through
   GBC's MCP or CLI tools. Parent-child projection, bidirectional edges, and
   born-green checks are deterministic constraints; bypassing the tools makes them drift.
   The implementer maintains any language/project-specific interface artifact and guarantee tests
   with the code.

2. **Implementers own the local contracts introduced by their work.**
   They do more than write implementation: query existing guarantees, register the
   dependencies they actually use, and prefer reusing an existing guarantee. When
   required behavior has no guarantee, they write a narrow test that can genuinely go
   red, create the guarantee, and self-prove with `verify_*`. An unregistered behavioral
   dependency or an unmaintained guarantee test means the task is not done.

3. **Coordinate intent and cross-scope destructive changes within granted authority.**
   Subagents read `gbc.md`; changing it requires delegated authority. Unless the brief
   explicitly authorizes it, they escalate operations that affect other tasks—retiring
   or disabling guarantees, renames, and refactors outside their scope—to the top-level agent.
   But `gbc.md` is only a **snapshot of the current state, not a sacred text**: if it
   needs updating, draft the delta and land it through gbc intent. Routine implementation,
   helper-file splits, and file-entry maintenance within an authorized goal and responsibility
   need no repeated architectural approval. Changes to purpose, responsibilities, compatibility,
   authority, or important constraints need corresponding authorization; obtain missing authority
   and respect additional project approval rules. Don't pile responsibilities into an existing file just because you're
   afraid to change `gbc.md`—a god file is the drift-guard mechanism turned upside down.

4. **Use framework enforcement for "local maintenance allowed, overreach blocked."**
   Hooks should block hand-edits to `gbc.md` / graph metadata, unauthorized intent changes,
   and unauthorized cross-scope destructive operations. Do not blanket-block
   dependency registration, guarantee creation, or verification for subagents; that
   prevents the agent closest to the implementation from closing the contract loop.

5. **Remember the nature of the boundary.** GBC provides rule text and guidance,
   not a security guarantee. What actually prevents overreach is your framework
   configuration—set it up accordingly.

6. **Register only guarantees you care about; a guarantee is not full test coverage.**
   A guarantee is a named behavioral promise guarded by a narrow test—register it only
   for behaviors downstream actually relies on; prefer reusing an existing guarantee.
   A guarantee nobody cares about is a liability: breaking it means notifying every
   dependent, verify gets slower, and the graph bloats. Before registering, ask:
   **"If the behavior I care about broke right now, would a test actually go red?"**
   If not, write a test that can go red—or don't register.

7. **Investigate first and communicate consequential findings.** Read existing intent,
   terminology, decisions, and relevant code/tests before drafting a change. Ask when an
   unresolved choice materially affects behavior, scope, compatibility, authority, or a
   costly-to-reverse decision and evidence cannot settle it. Reuse existing authorization;
   apply the authority boundary above and any additional project approval rules. Report meaningful
   progress and actual blockers rather than every tool step.

8. **Choose delegation for its benefit, not for ceremony.** Consider independence and complexity;
   delegate complete, verifiable behavior slices that may span related files. Name all writable
   paths in the brief; other paths remain read-only. One agent may plan and implement when
   delegation adds little value. The responsible agent still performs final overall GBC acceptance.

9. **Separate development testing from formal acceptance.** In the correct environment, direct
   runs of unregistered tests and targeted debugging are allowed; red-first is optional, with no
   mandatory replay. Born-green still gates formal creation and test/executor updates for normally
   enabled guarantees. Do not
   use disabling as a TDD step. Final acceptance uses GBC and reviews contract/test changes:
   GBC runs user-maintained tests and cannot detect weakened assertions just by centralizing runs.
   Green means no failures, not full acceptance; report heavy skips, disabled guarantees, and
   zero-execution results as unverified scope.

Use the bundled **gbc-workflow** skill with MCP or CLI for the detailed workflow; **gbc-cli**
is the CLI command adapter. A meaningful test protects the consumer's actual promise,
with focused scope, sufficient assertions, and no incidental implementation coupling. Assert exact
values, ordering, and error codes when contractual; born-green alone does not establish defect
sensitivity. Reuse vocabulary and preserve material decision reasons in existing project
documents, without requiring a new context file or copying history into `gbc.md`.
