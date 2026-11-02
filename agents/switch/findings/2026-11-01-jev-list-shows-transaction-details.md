# SEC-007: The Jev list would send refund candidates' dates and amounts to the network (`src/dashboard/reads.py`)

- **Severity:** Medium — the owner's real captures name refund candidates by date and amount, and the console is readable by everyone on the network; found before any release.
- **Status:** Fixed in Sprint 22 phase 4 (names hidden); the reveal for the secret's holder arrives with Phase 6
- **Verdict:** No blocking findings
- **Date / author:** 2026-11-01 / Switch (found by Trin in UAT, confirmed by Switch)
- **Affected:** `src/dashboard/reads.py` `_one_read`; capture files under `.understudy/cache/<run>/` written by `src/sketch/sources/capture.py`
- **Class / reference:** CWE-200 (information exposure); project rule P6 (private values never printed or served)

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| Neo | In Phase 6, let a request that carries the access secret receive the real level names (the page's secret box), with a test that no secret means `option N` | Sprint 22 phase 6 |
| Switch | Re-check the `/jev` payload of the real household run for dates and amounts | After Phase 6 |

## Evidence

- **Reproduce / detect:** mask the level names of the real run's captures (letters to `a`, digits to `9`): refund candidates read `a_9-9-9_-9.9_a9`, a date and an amount; category and merchant levels read as words.
- **Observed:** after the fix, the `/api/runs/<id>/jev` payload of the real household run (932 reads) contains 0 level names with a date or an amount; every top level is `option N` or the sketch's own `none_of_these`.
- **Confidence:** High.

## Impact and Reachability

Without the fix any host on the network could read which charges the owner's refunds might match, with dates and amounts. Reachable through one GET.

## Recommendation

- **Fix:** capture files record `levels_from_data` (true when the sketch's options come from the owner's rows); the Jev list shows the names only when it is false, and shows `option N` for data-derived levels and for captures too old to say. Done, with tests `PrivacyTest`.
- **Verify:** `tests/python/test_dashboard_reads.py::PrivacyTest`; the real-run payload check above.
- **Alternatives rejected:** hiding only names that look like amounts (fragile); hiding the whole list (loses the confidence the owner needs to tune).

## Risk Acceptance

Not accepted.
