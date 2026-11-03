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

### UAT-25-3: Kinds follow links and the tool's categories (Phase 3)

- **Linked criterion:** UND-98 AC1 to AC6
- **Preconditions and data:** the full baselines (run `run-20261103T170638-7a523587`, 2,299 requests) and the new small sample `data/sample-monarch.csv` and `data/sample-amex.csv` (60 merchants chosen by size and frequency plus the special cases, all their rows for the year and every card payment line; run `run-20261103T171642-a7bce9a3`, 305 requests in 67 seconds)
- **Steps:** run live; read `summary.json`, `totals.jsonl`, `crosswalk.jsonl`, `records.jsonl`; unit tests for a mislabeled payment, labels that say transfer, a pin to Household: Transfer, a card payment received with no bank side
- **Expected observable outcome:** no export label decides a kind; a payment with a misleading category still links; the crosswalk lists every merchant with both categories and a flag; the summary counts the flagged merchants
- **Actual outcome:** full run: 5,739 purchases, 167 refunds, 68 transfers (36 by link, 32 by category), 62 credits; crosswalk 1,214 merchants, 27 flagged covering 178 records; Ridgewood income $440,201 and expenses $217,266 against the owner's earlier $363,349 and $205,042. The differences are explained: Charles Schwab ($82,000, 8 records) was put in "Service providers: Securities" so it counts as income, and Venmo (-$9,653) counts as spending, as the earlier file's labels treated them as transfers; the two oldest card payments (2025-11-14 and 2025-12-12) have no bank side because Monarch starts in 2026, so they were credits until the text rule below; pairing worked for the other ten payments; sample run: 3,407 records, 105 transfers (81 by category, 22 by link, 2 by payment text), crosswalk 138 merchants with 10 flagged; unit tests: labels never make a transfer, a payment labeled as income still links, a pin to Household: Transfer makes Venmo a transfer, a card payment received with no bank side is a transfer by its text; 461 unit tests green
- **Verdict:** PASS
- **Evidence / issue:** two changes made from the findings: a card's own "payment received" text makes a record a payment even when unpaired (`transfer_basis: payment`), and Jev's group question now says what Household is for (own accounts including brokerage). Charles Schwab and the American Express debits are still unplaced after the change; they are the owner's to pin (`Household: Transfer`).

### UAT-25-4: The allocation stages (Phase 4)

- **Linked criterion:** UND-99 AC1, AC5, AC6 (the generic part)
- **Preconditions and data:** `data/activity-11-03-2026.csv` read outside the sketch (a scratch script calling `map.allocate`)
- **Steps:** allocate the file's charges to its 12 payment lines; compare each remainder with its amount
- **Expected observable outcome:** 11 of 12 within 5%; the first short by about $10,437; settled plus open equal all charges to the cent
- **Actual outcome:** 11 of 12 within 5% (worst May 4.6%, $832.30); first payment short $10,437.36; settled plus open $299,942.17 equal all charges
- **Verdict:** PASS
- **Evidence / issue:** chat message "UAT phase 4 passed"

### UAT-25-5: Payments know what they paid for (Phase 5)

- **Linked criterion:** UND-99 AC1 to AC7
- **Preconditions and data:** the full baselines with `since=2025-11-01`; live run `run-20261103T215207-620ddcce` and replays of it; the small fixture for a card with no payments
- **Steps:** read `payments.jsonl`, `records.jsonl` (`settled_by`) and `summary.json` (`open_balance`); unit tests for a card with no payments and for the card's dates against the bank's
- **Expected observable outcome:** 12 payment lines; every payment after the first within 5%; the first unexplained; settled plus open equal all the card's charges; open balance about $28,444
- **Actual outcome:** 12 lines, 11 of 12 within 5% (worst 4.6%), first short $10,437.36 and unexplained; settled $271,498.50 + open $28,443.67 = $299,942.17 over 5,299 charges
- **Verdict:** PASS
- **Evidence / issue:** two defects found in the first real run and fixed test-first: merged records carried the bank's date (the allocation now reads the card's), and the order of a day's charges changed the result (now smallest first). Finding: "unplaced" is the largest category of every payment (23 to 61%) until more merchants are pinned.

### UAT-25-6: Spending by the tool's category (Phase 6)

- **Linked criterion:** UND-100 AC1 to AC4
- **Preconditions and data:** the full baselines (replay of `run-20261103T215207-620ddcce`); `bobp make test-browser`
- **Steps:** read `spending.jsonl`, `taxonomy.jsonl` and `summary.json`; run the browser suite, which draws the console's list
- **Expected observable outcome:** every category in the clean list or `unplaced`; shares add to 1 within 0.001; amounts add to `spending_total`
- **Actual outcome:** 99 categories, none outside the list except `unplaced`; shares add to 1.0001; amounts add to $450,144.50, equal to `spending_total` (5,812 records); `unplaced` is 38.6% ($173,565.40, 2,041 records); browser suite 22 of 22
- **Verdict:** PASS
- **Evidence / issue:** chat message "UAT phase 6 passed"

## Results and Handoff

- **Passed / failed / blocked:** Phases 1 to 6: 6 passed (UAT-25-1 to UAT-25-6); 0 failed, 0 blocked
- **Open issues and impact:** "unplaced" is 38.6% of spending until the owner pins more merchants; pins for Ridgewood Savings Bank and other own-account merchants are the owner's to add; Ridgewood income is high by Schwab's $82,000 until Schwab is pinned (decision 14 is in the owner's pins file).
- **Overall verdict:** PASS
- **Handoff evidence:** message in `agents/CHAT.md`
