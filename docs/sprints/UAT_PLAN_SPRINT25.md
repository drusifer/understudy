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

### UAT-25-2: Jev puts every merchant in a category (Phase 2)

- **Linked criterion:** UND-97 AC1 to AC6
- **Preconditions and data:** the two baselines with `since=2025-11-01`; live runs `run-20261103T162337-b0e16ede` (first version), `run-20261103T163411-3e645dc1` (after the changes below) and `run-20261103T164205-5e3254bb`; a replay on a copy of the Monarch file with its categories scrambled (`build/uat25/monarch-scrambled.csv`)
- **Steps:** run live and read `records.jsonl`, `review.jsonl` and `statuses.jsonl`; replay the second run's captures against the scrambled export; compare each merchant's category and status
- **Expected observable outcome:** every merchant placed or for review; Jev chooses a group then a name from the clean list; the export's categories change nothing about what Jev is asked or answers; pinned merchants never asked
- **Actual outcome:** first version (placed only above 0.7 in both steps, four example names per group): 4,404 of 6,036 records for review (73%), 386 merchants (1,035 records) "none of these" including Seamless and Cash & ATM, and right answers at 0.45 to 0.67 (MTA, FreshDirect). Two changes: Jev is shown every name in each group, and a choice also counts at 0.4 or more when it is twice as sure as the runner-up. Result: 2,985 placed and 2,908 for review (48%), 687 merchants for review (508 below the bar, 179 none of these, 392 records); the largest placed merchants are MTA and the Apple Pay and Google Pay NYCT lines (local commuter transport), Seamless (eating places and restaurants), Gristedes and FreshDirect (groceries), Uber, Curb and Lyft (taxi-cabs), Cash & ATM (financial institutions: automated cash disbursements), Deposit / Income (Household: Income); a sample of 14 small merchants was reasonable except Amex placed in Government services and Apple.com/bill in Utilities; replay of the second run on the scrambled export: 0 Jev requests, not stale, and all 1,220 merchants have the same category and status; two live runs differ on 101 of 1,220 merchants (Jev varies near the thresholds); a live run takes about seven minutes and 2,280 requests, a replay about four minutes and none; 452 unit tests green
- **Verdict:** PASS
- **Evidence / issue:** run folders above. Findings: (1) the first rule would have sent 73% of records to review, so the rule was amended with the owner told (story AC2, ARCH); (2) refund detection still reads Income, Paycheck, Interest and Payroll labels, so scrambling those makes new refund questions: Phase 3 removes it; (3) a replay takes about four minutes (backlog).

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 1 passed (UAT-25-1); Phase 2: 1 passed (UAT-25-2); 0 failed, 0 blocked
- **Open issues and impact:** none open for Phase 1.
- **Overall verdict:** PASS for Phase 1
- **Handoff evidence:** message in `agents/CHAT.md`
