# Project verification deduplication: validation record

Date: 2026-09-29. Source-checkout validation; no package publication or remote push.

## Behavior

`verify all` previously started an executor separately for each enabled guarantee,
even when several guarantees referenced exactly the same check. It now captures
immutable execution plans and runs each distinct plan once per invocation.

Identity includes executor name, full selector, expanded command, resolved working
directory, effective environment and effective timeout. Execution uses those
captured parameters. Provider, guarantee ID and heavy rank do not change execution
identity. Results are attributed to every referencing guarantee, including raw
stdout/stderr and failures. No result is cached across invocations.

The strict gate still rejects failures, disabled guarantees, missing results and
zero results. `executed` counts guarantees with results; `test_runs` counts distinct
execution attempts. Missing-executor, startup and timeout failures retain affected
references as missing. Diagnostic reasons contain exception types, not private
executor arguments or environment values.

## Regression evidence

- Before the fix, both shared-check regression cases failed: three subprocess
  calls were observed where one was required.
- Targeted executor and project-verification tests: **37 passed in 7.20 seconds**.
  Coverage includes shared success/failure, distinct selectors/executors/timeouts,
  effective command/cwd/environment changes, timeout defaults and overrides,
  missing results, disabled/empty projects and fresh execution on each call.
- A real temporary project registers three enabled guarantees across two providers
  against one pytest check. Verification observes one real subprocess and three
  passing guarantee results; an additional disabled guarantee keeps the gate red.
- Complete test suite: **453 passed in 73.42 seconds**, with no reported skips,
  xfails or warnings. Windows runs used the project interpreter and fresh
  project-local temporary directories with the required filesystem access.
- Intent consistency: no errors or notes. Guarantee graph consistency: no issues
  or disabled notices.
- Fresh CLI final GBC acceptance: **GREEN, passed=54, failed=0, disabled=0,
  executed=54, missing=0, test_runs=50**, exit code 0. All 54 registered guarantees
  received results through 50 actual execution attempts, versus 54 attempts under
  the previous per-guarantee algorithm. The CLI summarizes passing checks rather
  than printing their raw output; the separate full-suite run above supplies the
  complete suite outcome.

Commands used the dedicated `gbc-codex` Python environment:

```text
python -X utf8 -m pytest tests/test_verify_all.py tests/test_core_executor.py -q -p no:cacheprovider --basetemp .cache/verify-all-dedup/targeted-4
python -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp .cache/verify-all-dedup/full-suite-1
python -X utf8 -m gbc.entry --lang en verify all
```

## Consumer execution counts

Read-only inspection of DipSea's current metadata, `project-guarantee` configuration
and runner found 290 enabled guarantees referencing 228 check files. Resolving the
actual plans reduces the planned invocations from **290 to 229**, with up to seven
references sharing one execution. DipSea was neither modified nor fully executed
for this measurement; this is a plan count, not a measured runtime improvement.

The extra invocation is intentional: `check_persistent_transaction.py` has a
90-second effective timeout for `MonitorStateStore.persists_one_upgrade_at_a_time`
and a 120-second override for `MonitorControl.fixed_core_upgrade_surface`.
Combining those would change the timeout contract. The runner receives the test
selector, not a provider or guarantee ID, so equivalent references need no extra
provider-specific execution.
