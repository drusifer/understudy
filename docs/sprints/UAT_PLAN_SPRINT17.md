# Sprint 17 Acceptance Test Plan (UAT): Dedupe, transfers, refunds and new categories

* **Sprint**: `SPRINT_17`
* **Author**: Trin (*qa)
* **Date**: 2026-10-27
* **Branch**: `sprint-17`
* **Status**: Phase 1 and Phase 2 UAT passed; later phases not yet run

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

*Self-check: rubric UAT: COVER=A STEPS=A FAIL=A DATA=A EVID=A (phases 1 and 2; the plan grows with each phase).*
