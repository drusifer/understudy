# Sprint 17 Acceptance Test Plan (UAT): Dedupe, transfers, refunds and new categories

* **Sprint**: `SPRINT_17`
* **Author**: Trin (*qa)
* **Date**: 2026-10-27
* **Branch**: `sprint-17`
* **Status**: Phase 1 UAT passed; later phases not yet run

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

*Self-check: rubric UAT: COVER=A STEPS=A FAIL=A DATA=A EVID=A (Phase 1 only; the plan grows with each phase).*
