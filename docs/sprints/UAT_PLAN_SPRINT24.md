# UAT Plan: Sprint 24, what the money goes on, typed inputs, and the statechart you can see

- **Stories / criteria:** UND-93, UND-94, UND-95, UND-87 and UND-82 in `docs/sprints/USER_STORIES_SPRINT24.md`
- **Environment and build:** branch `sprint-24`, local CLI and console (`bobp make run`, `bobp make dashboard`), live Jev; real household data in `data/` (git-ignored)
- **Date / tester:** 2026-11-02, Trin
- **Entry conditions:** `bobp make check` green; baseline `data/Transactions_2026-11-02T19-14-07.csv` and `data/amex-2026-ytd.csv` present
- **Exit conditions:** every acceptance criterion of the sprint passes; unresolved issues listed

## Scenarios

Phases are added as they pass UAT.

### UAT-24-1: Card payments and moves between accounts are not spending (Phase 1)

- **Linked criterion:** UND-93 AC1 to AC6
- **Preconditions and data:** the baseline files, `since=2026-01-01`; live run `run-20261103T031222-20544bb5`; unit tests for each label form and for a link-only transfer
- **Steps:** `bobp make run ARGS="run examples/household/household.yaml --with monarch=data/Transactions_2026-11-02T19-14-07.csv --with amex=data/amex-2026-ytd.csv --with amex_account=Platinum --with since=2026-01-01"`; read `records.jsonl` and `summary.json`
- **Expected observable outcome:** every labeled or linked record is a transfer; none other is; positive non-transfer records outside Ridgewood under $30,000; Ridgewood income $363,348.62 and expenses $205,042.27; `transfer_basis` counts
- **Actual outcome:** labeled or linked records that are not transfers: 0; `transfer_basis` both 35, label 103, link 5, none 5,010; positives outside Ridgewood 143 records, $20,038.35 (was 169, $240,596); Ridgewood income $363,348.62 and expenses $205,042.27; the all-account figures are now income $383,386.97, expenses $454,415.02, net -$71,028.05; unit tests: `Transportation: Transfers`, `Food & Dining: Credit Card Payment` and plain `Transfer` are transfers, `Shopping: Transferware` is not, and a card payment labeled as income is a transfer by its link
- **Verdict:** PASS
- **Evidence / issue:** run folder above; 368 tests green. A condition `ends` was added so `: Transfer` cannot match `Transferware`. The mislabeled purchases the owner knows of (Depop, Soho Deli, Levy Restaurants) are now transfers until relabeled in Monarch.

### UAT-24-2: Where the money goes (Phase 2)

- **Linked criterion:** UND-94 AC1 to AC6
- **Preconditions and data:** the baseline files; live run `run-20261103T031634-2a0afad6`; unit tests against the fixture, worked out independently from the records, and for a run with no records (`since` after the data)
- **Steps:** run the household sketch; read `spending.jsonl` and `summary.json`; add up the lines
- **Expected observable outcome:** one line per category with `category`, `count`, `amount`, `share`; biggest first; the export's Category first, then Jev's, then `uncategorized`; shares add to 1 within 0.001; amounts and counts equal `spending_total`; income, credits and transfers absent; an empty file when no spending
- **Actual outcome:** 90 lines for 4,951 records; $403,977.13 in total, equal to `spending_total` in `summary.json`; shares add to 1.0 and counts to 4,951; biggest are Housing & Real Estate: Rent $60,807.08 (15.05%, 14 records), Taxes $40,674.00 (10.07%), Mortgage $31,348.60 (7.76%), Bills & Utilities: Medical & Healthcare $24,156.74 (164 records), Food & Dining: Insurance $20,408.00; none `uncategorized` on this file; the empty case writes an empty file
- **Verdict:** PASS
- **Evidence / issue:** run folder above; 377 tests green. Findings for the owner: the category `Refund` shows as a negative amount (money back with no original category); some of the owner's own groups read oddly ("Shopping & Retail: Restaurants & Dining" 469 records, $18,332; "Food & Dining: Insurance"), inherited from the earlier categorization.

### UAT-24-3: The console shows what the money goes on (Phase 3)

- **Linked criterion:** UND-95 AC1 to AC4
- **Preconditions and data:** the real run `run-20261103T031634-2a0afad6` opened in a real Chromium (Professional light at 1300 px, Steampunk light at 390 px); browser tests with built runs for the other cases
- **Steps:** open the console on `.understudy/runs`, choose the run, read the summary panel; the browser tests open a run with 13 categories, a run without the file, a run with an unreadable file, a run at 390 px; the readability test measures the heading and rows in all six theme and mode looks
- **Expected observable outcome:** ten largest categories with amount and share and "and N more"; no heading or list when the file is absent; the unreadable file named and the page working; no sideways scrolling at 390 px; readable text everywhere
- **Actual outcome:** the real run lists Rent $60,807.08 15.0%, Taxes $40,674.00 10.1%, Mortgage $31,348.60 7.8% and seven more, then "and 80 more"; the browser tests: ten rows with the first one's amount and share and "3 more"; a run without the file has the heading hidden; `spending.jsonl line 2 is not readable` shown with the status still DONE; no horizontal overflow at 390 px; the readability check first found the heading unreadable in two light looks (1.06:1 and 1.77:1) and passes after the heading took the theme's heading color; 10 of 10 browser tests pass (69 seconds)
- **Verdict:** PASS
- **Evidence / issue:** screenshots checked by eye (desktop and phone); 386 unit tests green.

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 1 passed (UAT-24-1); Phase 2: 1 passed (UAT-24-2); Phase 3: 1 passed (UAT-24-3); 0 failed, 0 blocked
- **Open issues and impact:** Phase 2: the oddly grouped categories and a negative `Refund` line are the owner's data, not a defect; noted for the backlog.
- **Overall verdict:** PASS for Phases 1 to 3
- **Handoff evidence:** message in `agents/CHAT.md`
