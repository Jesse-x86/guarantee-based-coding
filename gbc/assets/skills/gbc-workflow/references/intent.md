# Intent and consequential questions

Read the affected folder's intent and, when needed, its ancestors. Compare it with current code, tests and the user's request before proposing changes. Code is evidence of implementation, not automatic authority to rewrite the intended architecture. Label a discrepancy explicitly and determine whether the task calls for correcting implementation or changing intent.

Give a recommendation when the facts support one. Explain the outcome, relevant evidence, tradeoff and scope boundary. Missing facts may come from investigation; missing product priorities or authority may require the user. Do not send the user a list of implementation choices that the agent can reasonably resolve.

Ask a consequential question when different answers materially change observable behavior, responsibility, compatibility or an important constraint. First settle the facts that make that choice meaningful. For example, determine whether existing consumers depend on ordering before asking whether the contract may drop it. Continue work that does not depend on the answer. Do not repeatedly ask about accepted decisions, every module seam or hypothetical future branches of the design.

## Drafting an architecture change

When architecture changes, prepare a coherent delta covering the affected purpose, internal constraints and file responsibilities. State the proposed resulting behavior and any consequential unresolved decision. Include necessary parent/child alignment, but avoid unrelated tree cleanup. The draft should be complete enough for the user to review the actual change, rather than asking permission to begin discovering it.

Keep these distinctions explicit:

- Current implementation: what the evidence shows today.
- Target intent: what the accepted architecture should require.
- This implementation scope: which part will be delivered now.

Follow the host project's rule for human approval before writing intent. A draft or analysis request alone is not approval; an already approved concrete delta does not need repeated approval. If new evidence requires a materially different architecture choice, explain that change and resolve it before writing the expanded delta.

Use GBC intent tools for `gbc.md` mutations, never hand-edit those files. Use project-relative `[[path/to/file.py]]` references. Keep `gbc.md` as the current purpose, constraints and file responsibilities; put substantial decision history in the project's existing decision-record convention. If the work fits current intent, implement and verify without creating documentation churn.
