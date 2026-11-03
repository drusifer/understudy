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

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 1 passed (UAT-24-1); 0 failed, 0 blocked
- **Open issues and impact:** none open for Phase 1.
- **Overall verdict:** PASS for Phase 1
- **Handoff evidence:** message in `agents/CHAT.md`
