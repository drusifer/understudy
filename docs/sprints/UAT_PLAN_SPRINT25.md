# UAT Plan: Sprint 25, the tool fixes the categories, and payments know what they paid for

- **Stories / criteria:** UND-96 to UND-100 in `docs/sprints/USER_STORIES_SPRINT25.md`
- **Environment and build:** branch `sprint-25`, local CLI (`bobp make run`), live Jev; real household data in `data/` (git-ignored): `Transactions_2026-11-02T19-14-07.csv` (Monarch) and `activity-11-03-2026.csv` (Amex, from 2025-11-01)
- **Date / tester:** 2026-11-03, Trin
- **Entry conditions:** `bobp make check` green; both baselines present
- **Exit conditions:** every acceptance criterion of the sprint passes; unresolved issues listed

## Scenarios

Phases are added as they pass UAT.

### UAT-25-1: A clean list of categories (Phase 1)

- **Linked criterion:** UND-96 AC1 to AC5
- **Preconditions and data:** the two baselines with `since=2025-11-01`; live run `run-20261103T161154-36af205f`; small additions files under `build/uat25/` for the refusals
- **Steps:** run the household sketch and read `taxonomy.jsonl`; run it with a missing additions path, a line without a name, a name that repeats an ISO name, a pin naming an export category, and the owner's own additions file
- **Expected observable outcome:** 280 ISO names in 13 groups plus the six shipped additions, each written `Group: Name`; the owner's file replaces the shipped six; each bad input stops the run before any Jev request with one line naming the path, line or category
- **Actual outcome:** `taxonomy.jsonl` has 286 lines (280 `iso`, 6 `owner`: Household Rent, Mortgage, Tuition, Income, Transfer, Loan repayment); a missing path says `file build/uat25/nowhere.jsonl does not exist (looked for .../examples/household/build/uat25/nowhere.jsonl)`; `source 'additions_file' line 2 has no name`; `source 'additions_file' line 1 repeats 'Family clothing shops' (also in 'iso')`; a pin of `Shopping` says `source 'pins_file' line 1: 'Shopping' is not a category in 'taxonomy'`; with the owner's file (`Pets: Vet bills`) the owner entries are that one only; no refused run wrote a summary or asked Jev anything; 441 tests green
- **Verdict:** PASS
- **Evidence / issue:** run folder above; `build/uat25/`. Finding fixed in the phase: a relative path that does not exist was named against the sketch's folder, not as typed; it now says both.

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 1 passed (UAT-25-1); 0 failed, 0 blocked
- **Open issues and impact:** none open for Phase 1.
- **Overall verdict:** PASS for Phase 1
- **Handoff evidence:** message in `agents/CHAT.md`
