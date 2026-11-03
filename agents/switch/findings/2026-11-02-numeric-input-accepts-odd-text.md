# SEC-010: A typed number was checked as a float but passed on as the owner's text (`1e2`, `nan`, `0x5`)

- **Severity:** Low — the value only reaches the owner's own sketch as a template variable and a child process argument list (no shell); the worst effect was a sketch given text it was not checked on.
- **Status:** Fixed
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-02 / Switch
- **Affected:** `src/sketch/inputs.py` (`_range_value`, `_count_value`), reached from `src/sketch/loader.py` and `src/dashboard/runs.py`
- **Class / reference:** CWE-20 improper input validation (checked value differs from the value used)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | Done: only plain ASCII digits, an optional sign and one decimal point are accepted as a number | Before the Phase 4 commit |

## Evidence

- **Reproduce / detect:** `value_problem("tickets", {"kind": "count", "min": 1, "max": 10, "default": 2}, "1e2")` before the fix read the text as 100.0 and said it was outside 1 to 10; `"nan"` and `"0x5"` were not accepted by float but `" 5"` and `"5_0"` were (Python's float tolerates padding and underscores), and a range accepted `"1e0"`.
- **Observed:** the text that passed the check is the text the run receives, so the check and the use disagreed.
- **Confidence:** High; `tests/python/test_sketch_inputs.py::test_a_number_must_be_written_as_plain_digits_so_the_run_gets_the_text_it_was_checked_on`.

## Impact and Reachability

Reachable from the command line (`--with`) and from the console's start request (behind the access secret). The value goes to a Jinja template and a YAML flow value (`tickets: 1e2` would read as a float). No code runs and no file is named by it; the impact is a sketch that gets text it was not validated on. Runtime scope.

## Recommendation

- **Fix:** accept a number only when it fully matches `-?[0-9]+(\.[0-9]+)?` (whole: `-?[0-9]+`), then compare it with the limits.
- **Verify:** the test above, `bobp make check`.
- **Alternatives rejected:** rewriting the accepted value to a canonical form (the run would then differ from what was posted).

## Risk Acceptance

Not accepted (fixed).
