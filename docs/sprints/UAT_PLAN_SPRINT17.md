# Sprint 17 Acceptance Test Plan (UAT): Dedupe, transfers, refunds and new categories

* **Sprint**: `SPRINT_17`
* **Author**: Trin (*qa)
* **Date**: 2026-10-27
* **Branch**: `sprint-17`
* **Status**: Phases 1 to 3 UAT passed; later phases not yet run

## 1. Scope

* **User stories covered so far:** `STORY-UND-49`. Later phases add `UND-50` to `UND-55` below as they are tested.
* **Environment:** Sprint 17 worktree, CPython 3.12.15, `mcp` 2.3.0, Node 24. Synthetic CSVs in temporary directories; the owner's real files were read locally for counts only and no snapshot was kept.

## 2. Phase 1: source servers and hydration (UND-49)

### `UAT-UND-49-01` Each export is served as JSONL records
* **Story/AC:** UND-49 AC 1, 2.
* **Command:** `bobp make test-py` (`tests/python/test_sources.py`, `test_hydrate.py`).
* **Expected:** each server offers `describe` and `read_transactions`; records carry `source`, `source_row_number`, `transaction_date`, `amount`, `merchant`, `account` and every original column in `raw_record`.
* **Result:** Pass. 16 Python tests, 0 failures. Record fields asserted for Monarch (account `Card (...1111)`, `Original Statement` kept) and Amex (US date `01/02/2026` normalized to `2026-01-02`, original kept). Both tools have a description.

### `UAT-UND-49-02` Counts on the real files
* **Story/AC:** UND-49 AC 3.
* **Command:** `hydrate("monarch", ...)` and `hydrate("amex", ...)` on the owner's files, from the Sprint 17 worktree; counts printed, snapshots deleted.
* **Expected:** Monarch 14,522 records and Amex 4,321, an Amex row with several lines counting once.
* **Result:** Pass. Monarch 14,522 records in 15 pages; Amex 4,321 records in 5 pages; line counts of the written files equal the record counts.

### `UAT-UND-49-03` A bad file stops the run before anything is written
* **Story/AC:** UND-49 AC 4.
* **Commands:** `python -m src.etl.source_server amex <file without an amount column>` and `... monarch <missing file>`; tests `test_a_missing_file_stops_before_anything_is_written`, `test_a_missing_column_stops_before_anything_is_written`.
* **Expected:** exit 2, a message naming the file and the column or the reason; no output directory or file created.
* **Result:** Pass. `understudy: Amex CSV /tmp/bad_amex.csv is missing a required amount column (recognized: amount, transaction amount)`, exit 2; `understudy: Monarch CSV cannot be read: /tmp/does-not-exist.csv (No such file or directory)`, exit 2. Tests confirm the destination and its parent directory do not exist afterwards.

### `UAT-UND-49-04` No household data in the repository; repeatable snapshot
* **Story/AC:** UND-49 AC 5 (and the traceability of AC 2).
* **Command:** tests use only temporary files built in the test; `git check-ignore data/activity.csv`; `test_the_snapshot_is_the_same_on_every_run`.
* **Expected:** fixtures are made up; `data/` is ignored; two hydrations of one file give the same hash.
* **Result:** Pass. `data/` is ignored (`.gitignore`); identical SHA-256 on both runs; the snapshot is written as `.part` and renamed on success, so a failed run leaves no partial file.

* **Phase 1 UAT verdict:** **PASSED**. No defects. One bug was found in review and fixed before the gate (an f-string docstring that would have left the `read_transactions` tool without a description); a test now asserts both tools are described.

## 3. Phase 2: one record per purchase (UND-50)

### `UAT-UND-50-01` Sign-flipped pairs keep both source rows; repeated amounts stay separate
* **Story/AC:** UND-50 AC 1, 3, 4.
* **Command:** `bobp make test-etl` (`sqlmesh/tests/test_purchase_pairs.yaml`, 6 cases) and `bobp make test-py` (`tests/python/test_pairing.py`, 6 cases).
* **Expected:** a charge and its sign-flipped copy become one `paired` record carrying both source rows; two real $4.50 purchases on one day stay two records, paired by statement text; a coincidence in another account is not paired; unequal counts pair what they can; a same-date pair is never given up for a near-date one; a row posted a day or two apart pairs, nearest first; a row without a date is kept as `invalid_key`.
* **Result:** Pass. 8 SQLMesh model tests (2 earlier + 6 new) and 6 account-detection tests; the near-date case failed before the third pass was written and passes after.

### `UAT-UND-50-02` Real-file counts
* **Story/AC:** UND-50 AC 2, 5.
* **Command:** hydrate both real files into an ignored folder, detect the card, run SQLMesh for `etl.purchase_pairs`, query counts, delete the folder (counts only).
* **Expected:** most Amex rows pair; the rest are listed single; no source row is used twice; records = Monarch rows + Amex rows − pairs.
* **Result:** Pass. 14,567 records = 14,522 + 4,321 − 4,276. 4,276 of 4,321 Amex rows paired (60 by statement text and date, 4,147 by order within a date, 69 within three days); 45 Amex rows unpaired; no Monarch or Amex row used twice. The first run, with same-date pairing only, paired 4,207 and left 114; 95 of those 114 had a same-amount card row one to three days apart, which led to the third pass.

### `UAT-UND-50-03` The card account is found, or the run says what to pass
* **Story/AC:** ARCH_SPRINT17 section 6 (account detection) supporting UND-50 AC 1.
* **Command:** `bobp make test-py` (`test_pairing.py`).
* **Expected:** the account with the most sign-flipped matches is the card; no matches, a tie, an override matching nothing or two accounts is refused with "could not tell which Monarch account is the Amex card (candidates: ...); pass --amex-account <text>", account names shown without their digits.
* **Result:** Pass. All refusals asserted, including that no account number appears in the message. On the real files the card was detected without an override.

* **Phase 2 UAT verdict:** **PASSED**. No defects. Finding recorded: only 60 pairs match on statement text (Monarch's `Original Statement` rarely equals Amex's description exactly), so most pairs rely on being the only candidate in their date and amount group; it does not change counts but weakens the exact-first rule for busy days.

## 4. Phase 3: transfers and refunds (UND-51, UND-52)

### `UAT-UND-51-01` Transfer legs pair one-to-one on business days and both are kept
* **Story/AC:** UND-51 AC 1, 5, 6.
* **Command:** `bobp make test-etl` (`test_transfer_pairs.yaml`, 8 cases, `test_business_calendar.yaml`).
* **Expected:** a Ridgewood debit and the card's credit pair and both rows stay; two same-amount payments in a week pair one-to-one; a Friday payment landing Monday, or the Tuesday after a Monday holiday, is one business day; legs more than three business days apart, or in one account, do not pair; a refund is never a transfer; a merchant whose name contains "payment" is not a candidate.
* **Result:** Pass. 8 transfer cases and the calendar case pass (25 model tests in all).

### `UAT-UND-51-02` Unpaired candidates are judged by payee, Venmo and Zelle are spending
* **Story/AC:** UND-51 AC 3, 4.
* **Command:** `bobp make test-py` (`test_transfers.py`, a Jev double).
* **Expected:** one request per distinct payee; Venmo and Zelle judged as spending, a savings-bank payee as an external transfer, an unsure payee goes to review; Jev sees the payee, the owner's account names without numbers and the payment counts, never Monarch's category label; Jev unreachable stops the stage naming it.
* **Result:** Pass. 5 tests: decisions for 4 distinct payees from 6 records with 4 requests, no account number or category in the state, error message names "transfer payees".

### `UAT-UND-51-03` Real-file transfer counts (fresh exports, counts only)
* **Story/AC:** UND-51 AC 3, 4.
* **Command:** hydrate, detect, run SQLMesh through `refund_candidates`, query counts, delete the run.
* **Expected:** every leg is used at most once; the unpaired candidates are the ones Jev will judge.
* **Result:** Pass. 155 transfer candidates: 40 paired (20 pairs, 24 at gap 0 and 16 at gap 1 business day, all one-to-one), 115 unpaired, across 25 distinct payees (Venmo 59 records, Bank Transfer 18, Ridgewood Savings Bank 7, Zelle 6). That is 25 Jev requests. Live Jev decisions are not run in this phase (owner's go-ahead needed); the owner checks the final Venmo/Zelle outcome on the acceptance run.

### `UAT-UND-52-01` Refunds link to their original, or are marked
* **Story/AC:** UND-52 AC 1, 3, 4.
* **Command:** `bobp make test-etl` (`test_refund_candidates.yaml`, 4 cases).
* **Expected:** one earlier same-merchant charge at least the refund's links without asking; several are listed most recent first with the full count (five shown); none is marked `no_original`; a later-dated charge, a smaller charge, a transfer leg and income are not offered or counted as refunds.
* **Result:** Pass.

### `UAT-UND-52-02` Jev chooses among several originals, never off the list
* **Story/AC:** UND-52 AC 2.
* **Command:** `bobp make test-py` (`test_refunds.py`, a Jev double).
* **Expected:** only refunds with several originals are asked; the choice and its confidence are kept; an answer that is not offered links nothing; one original or none asks nothing; Jev unreachable stops the stage naming it; two identical charges get distinct option names.
* **Result:** Pass. 5 tests. Real files: 65 refunds need a choice (65 requests), 27 link directly, 18 have no original.

### `UAT-UND-52-03` Jev client behaviour
* **Story/AC:** supports UND-52 AC 2 and UND-51 AC 3.
* **Command:** `bobp make test-py` (`test_jev.py`, a fake SDK client).
* **Expected:** a Choice returns the option, its confidence and every probability; a Noul returns the probability of yes; no key is refused naming `TYPESAFE_API_KEY`; an unreachable service is an error, not an answer.
* **Result:** Pass. 4 tests.

* **Phase 3 UAT verdict:** **PASSED** for the SQL and the Jev stages with doubles. Open for the acceptance run: the live Jev outcome on the real payees and refunds (needs the owner's go-ahead and key), and persistence of the decision rows, which belongs to the controller in Phase 5.

*Self-check: rubric UAT: COVER=A STEPS=A FAIL=A DATA=A EVID=A (phases 1 to 3; the plan grows with each phase).*
