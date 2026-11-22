# Workflow flexibility changes: verification record

Initial verification: 2026-09-23. Authorized completion: 2026-09-24.
Local source validation only; no version bump, package build or publication was performed for this change.

## Scope

Project rules, the existing workflow/CLI skills, bilingual manuals and bundled rules/setup now
separate development feedback from formal GBC acceptance. Delegation is selected by independence,
complexity and benefit; tasks cover verifiable behavior slices within explicit writable scope.
Existing authorization covers ordinary implementation and file-entry maintenance. Material changes
outside that authority still need approval, and intent/graph metadata still use GBC tools.

Tests require focused scope and sufficient contractual assertions. GBC runs project-maintained
tests; centralizing execution does not detect weakened assertions. Normal enabled registration and
test/executor updates retain born-green; retirement protection and consumer relationships remain.
No new development-run or mutation-testing command was added; defect replay remains optional.

CLI provider verification preserves GREEN/RED and exit semantics while adding localized notices
for zero execution, skipped guarantees and disabled guarantees. MCP keeps the original JSON fields
and clarifies their meaning in its tool description. No model or core state protocol was changed.

`AGENTS.md` is locally ignored by the repository's existing `.gitignore`; its local instructions
were updated, and the distributable guidance carries the same workflow boundaries.

## Behavior verification

New tests in `tests/test_verification_reporting.py` exercise eight summary combinations: empty,
heavy-only, disabled-only, pass plus heavy, pass plus disabled, pass, fail, and fail plus disabled.
The CLI runs each in English and Chinese (16 cases); MCP verifies the unchanged payload and
forwarded arguments (8 cases). The rendering tests stub the base summary, so they establish the
surface contract rather than independently proving executor behavior. Existing CLI gate tests
exercise real subprocess entry points and remain part of final acceptance.

The implementer's initial GBC creation attempt failed at the empty English CLI case: output was
`GREEN passed=0 failed=0 skipped=0` without the required no-execution notice. Registration was
refused. After implementing the notices, the same test selector passed normal registration.
No disabled placeholder was used. Final GBC verification below independently repeated the new
guarantees after the implementer's own checks.

| Provider | Passed guarantees | Failed | Skipped |
| --- | ---: | ---: | ---: |
| `gbc/app/assets.py` | 2 | 0 | 0 |
| `gbc/app/i18n/translate.py` | 1 | 0 | 0 |
| `gbc/app/documentation/base.py` | 1 | 0 | 0 |
| `gbc/app/documentation/cli.py` | 1 | 0 | 0 |
| `gbc/app/interface/cli.py` | 4 | 0 | 0 |
| `gbc/app/interface/mcp.py` | 4 | 0 | 0 |
| `gbc/entry.py` | 1 | 0 | 0 |
| **Total** | **14** | **0** | **0** |

These seven affected providers were verified through the configured `pytest-gbc-v2` executor via
GBC MCP. Their raw outputs reported no runner skips, xfails or warnings. Local raw results are in
`.cache/workflow-flexibility-validation/gates.json`. This is affected-scope verification, not a
full-repository or newly built-package acceptance claim.

Both shipped skills passed the existing skill-creator format validator using the existing local
validator dependency directory; no new package was installed. Resource/link and manual-query
guarantees passed. Bilingual guidance was reviewed; graph and intent consistency checks passed.
Consistency checks establish structure, not approval or behavioral correctness.

## Authorization and development-run follow-up

An initial direct development test run encountered Windows temporary-directory access denial.
Automatic approval review rejected its elevated retry under the previous no-direct-test rule.
The meaningful RED evidence above came from rejected GBC registration, not a direct development
RED run. On 2026-09-24, after the user explicitly authorized the concrete intent updates and the
development-test retry, the direct run of `tests/test_verification_reporting.py` passed all 24 cases
using the existing `gbc-codex` interpreter and a fresh project-local `--basetemp`, outside the sandbox.
The command disabled pytest's cache provider; it did not change assertions, filesystem permissions,
dependencies or global configuration. There were no skips, xfails or warnings in its output.

This confirms that the direct test-run path works with the corrected implementation. It does not
claim a newly observed direct RED phase: the implementation was already corrected. No extra defect
replay was performed merely to recreate that phase, and no efficiency improvement is claimed.

After the direct run, final GBC verification of `verify_provider.reports_execution_gaps` and
`verify_provider.preserves_evidence_payload` passed again (16 CLI cases and 8 MCP cases respectively).
These two checks supplement the 14-guarantee affected-scope acceptance above; they are not another
full run of those 14 guarantees. Intent consistency returned no errors or notes; graph consistency
returned an empty list, including no disabled notices.

A separate sandbox CLI verification also failed on temporary-directory access; the final GBC MCP
runs above succeeded with the same registered executor. Tests were not weakened or disabled, and
filesystem permissions were not changed to obtain those results.

Automatic approval review initially rejected the proposed root intent clarification, including after
checking the originating user's delegation. Following the user's direct approval on 2026-09-24,
the root intent was updated through `intent_set_intent` and the interface's verification-display
constraint was added through `intent_set_constraints`, preserving its existing constraints.
No intent files were hand-edited or changed through an alternative entry point. The earlier
approval blockers are resolved; no approval remains pending for this task.
