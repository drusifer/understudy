# Agent State

## Context

### Recent Decisions
- Owner clarified Sprint 16's internal hydration boundary: accept Monarch and Amex CSV, convert each flat row into JSONL, then use SQLMesh/DuckDB's JSONL ingestion path. This does not add arbitrary, nested, or user-supplied JSONL input support.
- JSONL line shape is `source`, `source_row_number`, `transaction_date`, `amount`, `merchant`, and `raw_record` with original source columns.

### Key Findings
- Added standard-library Python CSV conversion at `src/etl/csv_to_jsonl.py`; Python's CSV reader preserves quoted commas and multiline fields.
- `src/etl/run.mjs` runs the conversion between snapshot and SQLMesh, tracks `csv_to_jsonl` status and staged filenames in the run manifest, and passes JSONL paths to SQLMesh.
- SQLMesh raw models use DuckDB `read_json_auto(..., format = 'newline_delimited')`.
- A live Amex export used `MM/DD/YYYY`; raw pass-through caused every Amex row to land in `invalid_key`. `src/etl/csv_to_jsonl.py` now normalizes recognized dates to ISO for SQLMesh while preserving the original date in `raw_record`.
- Run review artifacts: `events.jsonl` records stage transitions and Jev batch durations/counts without merchant descriptions; `walkthrough.md` summarizes stage timings, input/reconciliation counts, Jev request counts, and output names. The final CLI summary points to the walkthrough.
- The walkthrough/summary count unique same-date, opposite-sign one-to-one pairs as diagnostics only; rows remain unmatched and separate. Latest owner-data run found 3,484 candidates.
- Two identical-input Jev runs changed 152 merchant choices (309 transaction rows). The sprint architecture explicitly allows new Jev choices on a new run; within each run, one mapping is reused for each merchant key.
- The owner's shared Google workbook was downloaded to ignored `build/runs/source/original-workbook.xlsx`. Comparison to latest Jev run uses the workbook transaction `Id` matched against `monarch_raw.Id`: 4,666/4,672 rows matched; 6 are absent from the newer Monarch export. `category-comparison.md` and `category-comparison.csv` are in the latest run folder.
- Workbook fields are not one consistent baseline: `Category` parent vs `Category_Ontology` super-category disagrees for 2,522 of 4,671 mapped rows. Exact label results: legacy parent 1,654/4,666; legacy full pair 344/4,666; `New Categories` leaf vs Jev subcategory 363/4,666; ontology super-category vs Jev category 2,313/4,666. These are literal matches, not semantic accuracy; a curated crosswalk is needed.
- Fixed the missing-input race in `src/etl/csv.mjs` by checking the file before opening a stream.
- Corrected pre-existing SQLMesh reconciliation fixture ordering and its invalid-date expected value so model tests reflect actual sorted output and source data.
- Tests used only synthetic fixture CSVs in `tests/fixtures/etl/`; the two generated run directories were removed after verification.

### Important Notes
- Modified source/tests: `src/etl/csv.mjs`, `src/etl/csv_to_jsonl.py`, `src/etl/run.mjs`, `sqlmesh/config.yaml`, raw models, `sqlmesh/tests/test_reconciliation.yaml`, `tests/etl/csv.test.js`, `tests/python/test_csv_to_jsonl.py`, synthetic CSV fixtures.
- Updated the Sprint 16 architecture and `task.md` to reflect CSV-to-flat-JSONL hydration. The worktree contains prior Phase 0 changes from Tank plus sprint planning artifacts; do not sweep unrelated changes into a commit.

## Current Task
**Status:** Completed the owner-requested Excel-to-Jev category comparison; Sprint 16 owner acceptance remains pending.
**Assigned to:** Neo
**Started:** 2026-10-17

### Task Description
Run the provided Monarch and Amex exports, make the run reviewable, and correct input issues found by the real data.

### Progress
- [x] Run both owner-provided CSVs through the CLI; the first result exposed unnormalized Amex US-style dates.
- [x] Normalize ISO and `MM/DD/YYYY` dates in staged JSONL while preserving source date text in `raw_record`.
- [x] Add stage and Jev-batch instrumentation, `events.jsonl`, and a human-readable `walkthrough.md`.
- [x] Fix source-local duplicate keys being labeled ambiguous when no counterpart exists in the other export; regression fixture now covers duplicate-only keys on both sides.
- [x] Add a summary/walkthrough diagnostic for unique opposite-sign candidates without changing match statuses; synthetic regression verifies the count.
- [x] Rerun the exports: 18,817 output rows; 26 matched, 18,791 unmatched, 3,484 opposite-sign candidate pairs kept separate, zero ambiguous/invalid-key rows, zero review-required rows.
- [x] Verification: `bobp make test` (310 JS tests, 4 Python tests, 2 SQLMesh model tests), `bobp make lint`, and `git diff --check` passed.
- [x] Download the shared Google workbook and compare its 4,672 transaction assignments with the latest Jev run by transaction ID; save aggregate and row-level comparisons under the ignored run directory.

### Blockers
None.

### Oracle Consultations
None.

## Next Steps
### Immediate Next Action
Owner to review `build/runs/1792273673200-4223e1cb-2ccc-4b98-8539-79b03e266b93/category-comparison.md` and `.csv`. If a semantic accuracy score is wanted, first decide which workbook category field is authoritative and approve a crosswalk; current reported comparisons are exact-label only.

### Waiting On
Owner acceptance for Sprint 16 closeout. The current run used the real Jev service; tests use only doubles.

### Planned Work
- [ ] Respond to owner feedback on the category comparison and whether a crosswalk should be built.
- [ ] Resume Sprint 16 closeout only after owner acceptance.

### Verification and Real Run
- `bobp make test`: 310 JS tests, 4 Python tests, and 2 SQLMesh model tests passed.
- `bobp make lint`: passed.
- Latest real run directory: `build/runs/1792273673200-4223e1cb-2ccc-4b98-8539-79b03e266b93/`; walkthrough and structured event log are present there.
- Excel comparison artifacts: `category-comparison.md`, `category-comparison.csv`; workbook copy at `build/runs/source/original-workbook.xlsx`.
- Real Jev run classified 3,824 distinct merchants in 765 requests (101.43 seconds); no fallback-to-Misc decisions.

---
*Last updated: 2026-10-17*
