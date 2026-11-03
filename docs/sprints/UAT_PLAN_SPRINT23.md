# UAT Plan: Sprint 23, household numbers you can trust and a run that tells its story

- **Stories / criteria:** UND-89 to UND-92 and UND-81 in `docs/sprints/USER_STORIES_SPRINT23.md`
- **Environment and build:** branch `sprint-23`, local CLI (`bobp make run`), live Jev; real household data in `data/` (git-ignored)
- **Date / tester:** 2026-11-02, Trin
- **Entry conditions:** `bobp make check` green; baseline `data/Transactions_2026-11-02T19-14-07.csv` and `data/amex-2026-ytd.csv` present
- **Exit conditions:** every acceptance criterion of the sprint passes; unresolved issues listed

## Scenarios

Phases are added as they pass UAT.

### UAT-23-1: Transfers follow the owner's categories (Phase 1)

- **Linked criterion:** UND-89 AC1, AC2, AC3, AC4
- **Preconditions and data:** baseline Monarch export plus the Amex export, `since=2026-01-01`, live run `run-20261103T003217-0a5d23bd`
- **Steps:** `bobp make run ARGS="run examples/household/household.yaml --with monarch=data/Transactions_2026-11-02T19-14-07.csv --with amex=data/amex-2026-ytd.csv --with amex_account=Platinum --with since=2026-01-01"`, then read `records.jsonl` and `summary.json`
- **Expected observable outcome:** every record with Category Transfer or Credit Card Payment has kind transfer; no other record does; the 244 Ridgewood records agree; the Charles Schwab deposits are transfers; `summary.json` has `kind_changed_by_category`
- **Actual outcome:** 72 category-labeled records, all transfer; 5,081 others, none transfer; Ridgewood agrees on all 244; the 8 Charles Schwab records on Ridgewood are transfers; `kind_changed_by_category` = no 5,083, yes 70
- **Verdict:** PASS
- **Evidence / issue:** run folder above. The story named nine Schwab deposits; the data has eight, and the story is corrected.

### UAT-23-2: A file without a Category column is refused (Phase 1)

- **Linked criterion:** UND-89 AC5
- **Preconditions and data:** the baseline file with the Category column removed (`build/uat/nocat.csv`, first 49 rows)
- **Steps:** run the household sketch with `--with monarch=build/uat/nocat.csv`
- **Expected observable outcome:** exit 2, one line naming the column, no Jev request
- **Actual outcome:** exit 2; `understudy: source 'monarch_csv' has no Category column`; the unit test `MissingCategoryTests` also asserts Jev is never asked
- **Verdict:** PASS
- **Evidence / issue:** `build/build.out`; `tests/python/test_household.py`

### UAT-23-3: Income, expenses and net per account (Phase 2)

- **Linked criterion:** UND-90 AC1, AC2, AC3, AC4
- **Preconditions and data:** the baseline files as in UAT-23-1; live run `run-20261103T003702-035bf72b` (0 new Jev requests beyond the cached ones)
- **Steps:** run the household sketch, then read `totals.jsonl` and `summary.json`; sum the baseline file's Ridgewood rows by hand, setting Transfer and Credit Card Payment aside
- **Expected observable outcome:** one line per account with income, expenses and net, transfers left out; Ridgewood income 363,348.62 and expenses -205,042.27; a last `all` row that is also `net_spending` in `summary.json`; no line for an account with no records
- **Actual outcome:** Ridgewood income 363,348.62, expenses -205,042.27, net 158,306.35, equal to the baseline's sums to the cent; the `all` row is income 603,944.54, expenses -476,342.42, net 127,602.12 and matches `summary.json`; accounts with no records have no line; an account with no income showed `0` and now shows `0.0` (fixed, tested)
- **Verdict:** PASS
- **Evidence / issue:** run folder above; `tests/python/test_household.py` checks every account's totals against the records.

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 2 passed (UAT-23-1, UAT-23-2); Phase 2: 1 passed (UAT-23-3); 0 failed, 0 blocked
- **Open issue (found in Phase 2):** two lines in `totals.jsonl` are Amex-only rows that matched no Monarch row, shown as accounts named `-38016` and `-33009` (the Amex account numbers), 14 records, about -$77. They are real records, so UND-90 AC4 is not broken, but the names are not accounts the owner knows. Owner: Neo, Phase 3 or a fix after the owner decides whether unmatched Amex rows should be named for their card.
- **Open issues and impact:** the card-side records. On accounts other than Ridgewood the export still labels some payments "Food & Dining: Credit Card Payment" and "Transportation: Transfers", so they are no longer transfers and count as refunds or credits: 169 positive non-transfer records worth $240,596 outside Ridgewood in this run. Ridgewood is unaffected. Owner: decide whether to relabel those in Monarch or add the group labels to the rule.
- **Overall verdict:** PASS for Phase 1
- **Handoff evidence:** message in `agents/CHAT.md`
