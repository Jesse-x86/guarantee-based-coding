# Vocabulary and decision reasoning

Use the project's existing glossary, context documents, accepted decisions, intent and public interfaces before inventing terms. Search only the material relevant to the current ambiguity. A word can have different meanings in different bounded contexts; name that context instead of forcing one global meaning onto unrelated modules.

For a disputed term, identify what it denotes here, which behavior or boundary depends on that meaning, and the evidence supporting the usage. Distinguish the current documented meaning, observed implementation and proposed change. If they conflict, expose the conflict and resolve it within the task's authority rather than silently rewriting one source to look consistent.

Prefer established vocabulary when it expresses the intended distinction. Introduce a new term only when it separates concepts the project actually needs to distinguish, and define it where readers already look for those concepts. Avoid renaming working concepts merely to match a fashionable architecture pattern.

For an important decision, explain the recommended outcome, the relevant alternatives, the evidence or assumptions that distinguish them, and the cost accepted. Reconsider when evidence or requirements change; a user's question by itself is not evidence that the recommendation should reverse. State what additional fact or priority would change the decision when that boundary is useful.

Preserve accepted decisions using the project's existing convention. Update an existing glossary or decision record when appropriate; do not require a new `CONTEXT` document, ADR or design ceremony for every change. Keep historical rationale outside `gbc.md`; its job is to express the current intent and constraints. A new meaning that changes architecture follows the intent approval process, while a clarification that preserves the meaning should not create a fictitious architecture change.
