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
   only through the gbc doc entry point (MCP doc tools / CLI), and change dependency / guarantee JSON only through
   GBC's MCP or CLI tools. Parent-child projection, bidirectional edges, and
   born-green checks are deterministic constraints; bypassing the tools makes them drift.
   The implementer maintains any language/project-specific interface artifact and guarantee tests
   with the code.

2. **Implementation subagents own the local contracts introduced by their work.**
   They do more than write implementation: query existing guarantees, register the
   dependencies they actually use, and prefer reusing an existing guarantee. When
   required behavior has no guarantee, they write a narrow test that can genuinely go
   red, create the guarantee, and self-prove with `verify_*`. An unregistered behavioral
   dependency or an unmaintained guarantee test means the task is not done.

3. **Intent and cross-scope destructive changes remain under top-level coordination, but intent is evolvable.**
   Subagents read `gbc.md` but do not commit changes themselves. Unless the brief
   explicitly authorizes it, they escalate operations that affect other tasks—retiring
   or disabling guarantees, cross-file renames, and refactors—to the top-level agent.
   But `gbc.md` is only a **snapshot of the current state, not a sacred text**: if it
   seems wrong or starts blocking reasonable architectural evolution, draft the delta →
   get human sign-off → commit it through gbc doc. That is legitimate evolution, not
   a violation. Don't pile responsibilities into an existing file just because you're
   afraid to change `gbc.md`—a god file is the drift-guard mechanism turned upside down.

4. **Use framework enforcement for "local maintenance allowed, overreach blocked."**
   Hooks should block hand-edits to `gbc.md` / graph metadata, intent changes by
   subagents, and unauthorized cross-scope destructive operations. Do not blanket-block
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

7. **Communicate with the human often and report as you go.** Report after each step;
   ask when unsure. Don't hold everything back until it feels "perfect"—that usually
   means things that should have been said earlier weren't, and it tends to produce
   plenty of tests nobody cares about. When it comes to GBC matters, more communication
   is better.
