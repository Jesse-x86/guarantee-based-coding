# Executor output decoding: validation record

Date: 2026-09-29. Source-checkout validation; no package release or remote push.

## Defect and contract

The executor used `subprocess.run(text=True)` without an encoding. On Chinese
Windows, locale-based GBK decoding of UTF-8 child output could raise inside
`subprocess._readerthread`, losing stdout/stderr even when the child returned a
normal exit code. A successful exit alone therefore did not prove intact evidence.

The shared executor now explicitly uses UTF-8 with `backslashreplace` for both
streams. Valid UTF-8 remains readable; malformed bytes become hexadecimal escapes
without losing adjacent text. Child exit codes, timeout rules and plan identity
remain unchanged. Single and project-wide execution use the same implementation.

This is a diagnostic-text contract, not a lossless binary archive. Universal
newline translation remains enabled, and literal backslash escapes cannot be
distinguished from escaped invalid bytes. Legacy producers should emit UTF-8 for
readable text; there is no locale guessing or silent `ignore` policy.

## Regression evidence

Eight real-process cases cover single/prepared execution, exit codes 0/7, valid
Unicode and malformed/truncated UTF-8. Each writes exact bytes through `os.write`
to stdout and stderr and asserts complete decoded output, exit code and JSON
round-trip. The tests force subprocess's locale fallback to GBK, so launching
pytest in UTF-8 mode cannot conceal the original defect.

- Original implementation: **8 failed, 16 reader-thread warnings in 0.58 seconds**.
- Targeted executor/project-verification tests: **45 passed in 5.54 seconds**.
- Complete suite: **461 passed in 83.98 seconds**, with no reported skips, xfails
  or warnings.
- Intent check: no errors or notes. Guarantee graph: no issues or disabled notices.

Real CLI validation uses the dedicated GBC Python environment with `-X utf8=0`:
`sys.flags.utf8_mode` is 0 and `locale.getencoding()` is `cp936`. It invokes
`python -X utf8=0 -m gbc.entry --lang en verify all -C <project>` without a global
timeout override. The launcher captures CLI stdout/stderr as binary files, records
wall-clock time and exit code, then decodes the CLI's cp936 console output into
UTF-8 log files for inspection. No GBC or DipSea executor configuration is changed.

## Real CLI outcomes

| Project | Exit | Passed | Failed | Disabled | Executed | Missing | Test runs | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GBC | 0 | 54 | 0 | 0 | 54 | 0 | 50 | 127.89 s |
| DipSea | 0 | 290 | 0 | 0 | 290 | 0 | 229 | 230.48 s |

Both CLI gates reported GREEN. Their stderr files were empty; neither captured
stream contained a `UnicodeDecodeError`. No failing or missing DipSea guarantees
were observed to classify as encoding-related or unrelated. DipSea source was not
modified. Its own runners used their existing disposable test-state mechanism.

The CLI prints raw check diagnostics only for failed results, so these successful
CLI logs are gate summaries, not a complete transcript of every passing check.
The eight byte-level regressions above separately prove output preservation and
exit-code behavior. These timings include concurrent validation workloads and
are not a controlled performance comparison.

Local evidence is under `.cache/output-decoding/`: `red.log`, `targeted.log`,
`full-suite.log`, and `gbc`/`dipsea` `.json`, `.stdout.bin`, `.stderr.bin`, and
decoded `.stdout.log`/`.stderr.log` files. Cache evidence is not committed.
