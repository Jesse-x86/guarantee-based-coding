---
name: gbc-workflow
description: Plan GBC intent changes, define and review behavior guarantees, and resolve domain terminology or design decisions in a GBC project. Use for these reasoning tasks with either MCP or CLI; ordinary edits that do not involve them need not load this skill.
---

# GBC workflow

Use GBC to connect the user's intended change to current architecture and testable promises. This skill guides the reasoning; use available GBC MCP tools or the [gbc-cli command adapter](../gbc-cli/SKILL.md) for operations. Neither transport changes the project's authority or approval rules.

## Working loop

1. Establish the requested outcome and scope. Read relevant `gbc.md` intent, constraints and file entries, then inspect the code, tests and existing project terminology needed to resolve the current question. Do not load the whole intent tree for a local change.
2. Separate observed behavior, inference and open decisions. Recommend a concrete outcome with its evidence and tradeoffs. Investigate missing facts yourself where possible; ask the user only about consequential unresolved choices after their prerequisites are understood. Keep independent work moving, preserve accepted decisions, and stop investigating when the current scope is sufficiently clear.
3. If the change alters architectural purpose, responsibility or constraints, draft the complete affected intent delta before implementation. Follow the host's human sign-off rule and write accepted intent only through GBC intent tools. Existing approval remains valid within its scope. If architecture is unchanged, do not manufacture an intent edit or approval step.
4. Identify the behavior consumers need, reuse an existing matching guarantee, or write a focused test and register a new guarantee. Record actual behavior dependencies through GBC. A passing registration establishes today's result, not that the test could reject the relevant defect.
5. Implement within the accepted scope and verify affected guarantees through GBC using the project's executor. Inspect failures, skipped or disabled coverage and actual output; report what was established and what remains unknown. Do not weaken assertions or suspend guarantees to manufacture a green gate.

Read supporting guidance only for the part being worked on:

- [Intent and consequential questions](references/intent.md): architecture changes, incomplete requirements, or drafting an intent delta.
- [Guarantees and test evidence](references/guarantees.md): choosing a promise, reviewing its oracle, or deciding whether a defect replay is useful.
- [Vocabulary and decision reasoning](references/vocabulary.md): ambiguous domain terms, conflicting descriptions, or important design tradeoffs.

Follow the project's delegation and final acceptance rules. A delegated brief should include the relevant intent, writable scope, required behavior and executor; the accepting agent still performs its required final gate. This skill grants no permission to install tools, change hooks or global policy, publish, or act on external systems.
