# Guarantees and test evidence

Start with the behavior someone relies on, not the shape of the implementation. In ordinary prose identify the consumer, provider, promised behavior, public module boundary, independent expected result, and an example of wrong behavior the test must reject. This is a reasoning aid, not a new metadata schema or a mandatory document template.

Reuse an existing guarantee when it covers the actual promise. Register a new focused guarantee when new behavior deserves to be relied on, and record consumers' behavior dependencies through GBC. Avoid duplicate guarantees for different callers of the same contract. A symbol-only dependency does not establish a behavioral promise.

## Choose an independent oracle

Exercise the provider's public boundary with inputs that distinguish correct behavior from a plausible defect. Derive expected results from the accepted contract, an independently reasoned example, or an authoritative fixture. Recomputing the expected result with the same implementation logic can repeat its mistake.

Precision depends on the promise. An exact exit code, ordering, count or returned value is necessary when callers rely on it. A non-null or type assertion is sufficient only if that is the entire relevant promise; it cannot prove correct content, routing or failure handling. Prefer a small test of one behavior over broad incidental snapshots, without weakening the contract to make the test small.

Mocks may model a real external boundary to keep a test deterministic. They must not replace the behavior under test with a prearranged success. Make clear which boundary is simulated and which real behavior is exercised. Test environment failures separately from contract failures.

## Registration and sensitivity

GBC's normal enabled registration runs the test and refuses a failing new guarantee. This constrains formal registration and test/executor changes for enabled guarantees, not development feedback. Updates while disabled do not run the gate; a successful enable is required to restore protection. You may directly run an unregistered test or a focused debugging selection in the project's correct interpreter, working directory and dependencies. Observing red before implementing to green is allowed, not mandatory. After it passes, register the guarantee and dependencies, then perform final acceptance through GBC. Do not create a disabled placeholder to stage ordinary TDD, and do not add invented red-proof metadata.

GBC runs project-owned tests; its execution route cannot determine whether an assertion was weakened or the contract is adequately tested. Review test changes against the consumer's promise and the wrong behavior they should reject. Passing registration establishes an execution result, not defect sensitivity.

A defect replay or deliberate red probe can add confidence for a subtle regression or consequential contract when ordinary review leaves uncertainty. It is optional and risk-based, not a universal red-first requirement:

1. Use an isolated, authorized workspace with a known restoration point. Apply only the specific historical defect or controlled behavior change the test should detect.
2. Run the relevant test through GBC verification with the project's executor. For a new guarantee, register against the corrected behavior first so registration remains born-green, then probe in isolation.
3. Confirm that the failure is the target contract failure. An import error, missing dependency, permission failure or unrelated assertion is not useful red evidence.
4. Restore the correct state even if the probe fails unexpectedly, then verify through GBC again. Report the observed red and restored green, or say why sensitivity remains unproven.

Do not run such probes against unrelated or valuable work. If the isolation or restoration cannot be made reliable within scope, use review evidence and disclose the limitation instead.

## Accepting a change

Run affected guarantees through GBC; do not substitute a direct development run for the registered gate. Read the reported results, since a process exit code alone may not represent the gate. Green means no executed guarantee failed; heavy skips and disabled guarantees still leave coverage unverified, and zero execution supplies no behavioral evidence. Also inspect runner-level skips, expected failures and warnings in raw output. Completing acceptance requires the evidence needed for the task, not just a green label. Consistency checks establish metadata consistency, not behavioral correctness.

If a guarantee fails, investigate the affected contract and consumers. Fix the behavior or resolve an explicitly proposed contract change with the required authority. Do not loosen assertions, remove dependencies or disable the promise merely to obtain green. Refactor tools and temporary disabling remain available for their documented, authorized migration purpose; restore and verify the guarantees before claiming their protection.
