# GBC Recommended Guardrails (author's suggestions)

> These are **recommended defaults, not an enforced sandbox.** GBC only provides
> the rule text and guidance; the actual enforcement boundary must be established
> by your agent framework (e.g. Claude Code's `pre-tool-use` hook).
> **Installing GBC does NOT make you automatically safe.**

Adopting the following rules in your agent instructions (or enforcing them via your
framework) will markedly improve the GBC experience:

1. **The top-level agent never edits files inside `.gbc/` directly.** Intent
   documents are changed only through the gbc doc entry point (MCP doc tools / CLI); the guarantee graph
   is touched only through GBC's tools (MCP / CLI). Never hand-edit anything under
   `.gbc` — its parent/child consistency is a deterministic constraint that stays
   correct only when maintained through the tools.

2. **Subagents touch neither `.gbc/` files nor any mutating GBC tool / gbc doc.**
   A subagent only implements and self-proves via `verify_*`; making commitments
   (registering guarantees, changing intent) is reserved for the top-level agent.

3. **The top-level agent focuses on planning and aligning intent**, delegating
   concrete coding to subagents (small changes may be done inline by the top agent).

4. **Enforce the above via your framework.** For example, Claude Code's
   `pre-tool-use` hook can intercept a subagent's writes to `.gbc/`, or block
   unauthorized tool calls.

5. **Remember the nature of the boundary.** GBC provides rule text and guidance,
   not a security guarantee. What actually prevents overreach is your framework
   configuration — set it up accordingly.
