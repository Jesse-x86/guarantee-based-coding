---
name: gbc-workflow
description: Plan GBC intent changes, define and review behavior guarantees, and resolve domain terminology or design decisions in a GBC project. Use for these reasoning tasks with either MCP or CLI; ordinary edits that do not involve them need not load this skill.
---

# GBC workflow

Use GBC to connect the user's intended change to current architecture and testable promises. This skill guides the reasoning; use available GBC MCP tools or the [gbc-cli command adapter](../gbc-cli/SKILL.md) for operations. Neither transport changes the project's authority or approval rules.

## Working loop

1. Establish the requested outcome and scope. Read relevant `gbc.md` intent, constraints and file entries, then inspect the code, tests and existing project terminology needed to resolve the current question. Do not load the whole intent tree for a local change.
2. Separate observed behavior, inference and open decisions. Recommend a concrete outcome with its evidence and tradeoffs. Investigate missing facts yourself where possible; ask the user only about consequential unresolved choices after their prerequisites are understood. Keep independent work moving, preserve accepted decisions, and stop investigating when the current scope is sufficiently clear.
3. Check whether existing intent and authorization cover the change. Ordinary implementation choices, helper-file splits and file-entry maintenance within approved responsibilities do not require renewed architectural approval. For a materially new purpose, responsibility, compatibility, permission or important constraint outside that authority, draft the affected delta and obtain the required approval. Write intent only through GBC intent tools; preserve existing authorization and avoid invented approval steps.
4. Identify the behavior consumers need and reuse an existing matching guarantee or write a focused test. Development feedback may include directly running unregistered tests in the project's correct environment, observing red and implementing to green. Register new guarantees only when their normal born-green gate passes, and record actual behavior dependencies. A passing registration does not establish defect sensitivity.
5. Complete the authorized behavior slice and perform final verification of affected guarantees through GBC using the project's executor. Direct development runs do not replace this gate. Inspect failures, skipped or disabled coverage, zero execution and actual output; report what was established and what remains unknown. GBC runs project-owned tests; review test changes because the execution route cannot detect weakened assertions on its own.

Read supporting guidance only for the part being worked on:

- [Intent and consequential questions](references/intent.md): architecture changes, incomplete requirements, or drafting an intent delta.
- [Guarantees and test evidence](references/guarantees.md): choosing a promise, reviewing its oracle, or deciding whether a defect replay is useful.
- [Vocabulary and decision reasoning](references/vocabulary.md): ambiguous domain terms, conflicting descriptions, or important design tradeoffs.

Choose delegation by independence, complexity and benefit, within the project's rules. A task should cover a complete, verifiable behavior slice, including related files within its writable scope. A delegated brief includes relevant intent, scope, behavior and executor; the accepting agent performs the final integration gate. Do not create handoffs solely to separate roles. This skill grants no permission to install tools, change hooks or global policy, publish, or act on external systems.
