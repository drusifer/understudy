# Sprint 16 Acceptance Test Plan (UAT): Staged Local ETL with Jev-Guided Categories

* **Sprint**: `SPRINT_16`
* **Author**: Trin (*qa)
* **Date**: 2026-10-17
* **Branch**: `sprint-16`
* **Status**: Phase 1 and Phase 2 UAT and Morpheus review passed

## 1. Scope of Acceptance Testing

* **User Stories Covered:** `STORY-UND-46`, `STORY-UND-47`, and `STORY-UND-48`.
* **In-Scope Workflows:** Validate and snapshot local CSV exports, convert flat CSV rows to JSONL, load JSONL through SQLMesh, reconcile unique matches, retain unmatched and ambiguous rows, classify distinct merchants with finite Jev choices, reuse run-scoped mappings, and export an auditable local review file.
* **Out-of-Scope:** Live Jev calls with private account data; Google Sheets/MCP integration; arbitrary or nested JSONL input. Users supply Monarch and Amex CSV files.

## 2. Preconditions & Test Environment Setup

* **Environment:** Sprint 16 worktree, CPython 3.12.15 / SQLMesh 0.236.3 / DuckDB 1.5.6, Node.js 24.
* **Fixtures & Test Data:** Synthetic inputs at `tests/fixtures/etl/monarch.csv` and `tests/fixtures/etl/amex.csv`. They contain one shared transaction and one unmatched transaction per source. No owner CSV was accessed.
* **Environment Verification:** Tank's Phase 0 clean install/check and SQLMesh/Node/Python DuckDB handoff passed; see `agents/tank/phase0_sprint16.md` and `agents/CHAT.md`.

## 3. Scenario-Driven Acceptance Test Cases

### Test Case `UAT-UND-46-01`: Convert and reconcile two exports

* **User Story:** `STORY-UND-46`, AC 1–3.
* **Preconditions:** The two synthetic fixture files exist.
* **Execution Steps:**
  ```bash
  bobp make run ARGS="etl run --monarch tests/fixtures/etl/monarch.csv --amex tests/fixtures/etl/amex.csv"
  ```
* **Expected Result:** Exit code `0`; source counts are two Monarch and two Amex rows; one unique date+amount overlap is `matched`; one row from each source remains `unmatched`. Run files are staged below ignored `build/runs/<run-id>/`.
* **Actual Execution Result:** Pass. Command exited `0`, reported `input_rows`: Monarch `2`, Amex `2`; reconciliation counts: `matched` `1`, `unmatched` `2`. The JSONL snapshot had two records, normalized `merchant` preserved `Cafe, Local`, and `raw_record.Merchant` retained the original value. Manifest stages `validation`, `snapshot`, `csv_to_jsonl`, and `sqlmesh` were `complete`.

### Test Case `UAT-UND-46-02`: Keep ambiguous date+amount candidates separate

* **User Story:** `STORY-UND-46`, AC 3.
* **Execution Steps:**
  ```bash
  bobp make test-etl
  ```
* **Expected Result:** SQLMesh model test passes with duplicate-key rows marked `ambiguous`, unique overlap marked `matched`, unmatched rows retained, and invalid keys retained.
* **Actual Execution Result:** Pass. `bobp make test-etl` reported one SQLMesh reconciliation model test passed. The fixture asserts one matched pair with both source-row references, three separate ambiguous rows, two unmatched rows, and two invalid-key rows.

### Test Case `UAT-UND-46-03`: Reject an unavailable source before creating a run

* **User Story:** `STORY-UND-46`, AC 4.
* **Execution Steps:**
  ```bash
  bobp make run ARGS="etl run --monarch tests/fixtures/etl/missing.csv --amex tests/fixtures/etl/amex.csv"
  ```
* **Expected Result:** Non-zero exit code; message identifies `Monarch CSV cannot be read`; no run directory or completed database is published.
* **Actual Execution Result:** Pass. Exit code `2`; output named the missing Monarch path. Unit test `missing source file is named before any run directory is created` also asserts no run manifest was created.

### Test Case `UAT-UND-46-05`: Guide an incomplete CLI invocation

* **User Story:** `STORY-UND-46`, AC 4.
* **Execution Steps:** Run `bobp make run ARGS="etl run --monarch tests/fixtures/etl/monarch.csv"` without a TypeSafe key.
* **Expected Result:** The CLI refuses before creating a run, exits `2`, and names the missing `--amex <csv>` input.
* **Actual Execution Result:** Pass. Exit code `2`; output was `understudy: understudy etl run needs --amex <csv>`. No Jev call or run directory was created.

### Test Case `UAT-UND-46-04`: Reject a missing required header and preserve CSV quoting

* **User Story:** `STORY-UND-46`, AC 4; hydration integrity.
* **Execution Steps:**
  ```bash
  bobp make test-js
  bobp make test-py
  ```
* **Expected Result:** Header validation rejects the source lacking `amount`; converter unit tests preserve quoted commas and multiline fields and retain source identity, source row number, normalized fields, and the complete original row.
* **Actual Execution Result:** Pass. JavaScript suite: 303 passed. Python suite: 3 passed, including conversion and missing-column tests.

## 4. Negative & Error Handling Test Cases

The missing-file and incomplete-invocation commands above are CLI-level negative checks. Header-missing and converter-column checks are covered by unit tests; both fail before SQLMesh can publish a completed result. No personal data or persistent external state was used.

## 5. Defect Summary & Gate Outcome

### Test Case `UAT-UND-47-01`: Classify distinct merchants from the fixed taxonomy

* **User Story:** `STORY-UND-47`, AC 1–3.
* **Execution Steps:**
  ```bash
  bobp make test-js
  bobp make test-etl
  ```
* **Expected Result:** Jev receives only distinct merchant descriptors, transaction counts, and finite offered category/subcategory pairs. Same-key records are consolidated before a request. A valid pair is reused by SQL; the SQLMesh category model retains reconciliation provenance.
* **Actual Execution Result:** Pass. JavaScript unit coverage validates the 46-option taxonomy, duplicate-key consolidation, batching, and valid choices. The SQLMesh model test verifies a run-scoped mapping joined to its transaction row with both source references.

### Test Case `UAT-UND-47-02`: Fall back safely for invalid or missing choices

* **User Story:** `STORY-UND-47`, AC 4; `STORY-UND-48`, AC 5.
* **Execution Steps:**
  ```bash
  bobp make test-js
  bobp make test-etl
  ```
* **Expected Result:** Off-list and empty Jev answers become `Misc / Other or not yet classified` with `review_required = true`; a failed Jev request marks its stage failed and produces no complete summary or review export.
* **Actual Execution Result:** Pass. Unit tests assert off-list/empty fallbacks. The synthetic end-to-end failure test confirms `run.json` is failed at `jev_categories` and neither `summary.json` nor `review.csv` exists.

### Test Case `UAT-UND-48-01`: Review categorized output and counts

* **User Story:** `STORY-UND-48`, AC 1–5.
* **Execution Steps:** Synthetic e2e scenario runs from `tests/etl/run.test.js` with the SQLMesh CLI and a scripted Jev double; no network call or personal CSV is used.
* **Expected Result:** Local summary reports per-source counts, reconciliation statuses, classified count, Misc count, and review-required count. `review.csv` retains both input source references and raw row values.
* **Actual Execution Result:** Pass. Synthetic run reports 2 Monarch + 2 Amex rows, 1 match + 2 unmatched rows, 3 reconciled transactions, 2 classified transactions, 1 Misc fallback, and 1 review-required row. Review export includes provenance and raw values.

### Test Case `UAT-UND-48-02`: Process the target local row volume

* **User Story:** `STORY-UND-48`, AC 4.
* **Preconditions:** Generate two temporary synthetic CSVs with 4,700 matching date+amount pairs and five repeated merchants. Use a scripted Jev double; never read owner data or call the paid API.
* **Execution Steps:** Run `bobp make test-js`; the `reconciles and categorizes a synthetic 4,700-transaction workload locally` scenario creates the CSVs in a temporary directory and exercises the full SQLMesh-backed runner.
* **Expected Result:** Both sources load 4,700 rows; all 4,700 pairs reconcile and appear in the review export; five merchant keys use one bounded Jev-double batch; run stages complete.
* **Actual Execution Result:** Pass. 4,700 matches and categorized rows, 9,400 input rows, five merchant choices in one request; review CSV contains its header plus 4,700 rows. The full staged run completed in 10,286 ms on this development machine.

| Defect ID | Severity | Description | Assignee | Status |
|---|---|---|---|---|
| — | — | No Phase 1 acceptance defects found. | — | — |

* **Phase 1 UAT Verdict:** **PASSED**
* **Phase 1 Morpheus Review:** **PASSED** — owner-directed conversion boundary, SQLMesh load, provenance, privacy, and scope align; no Phase 1 defects found.
* **Phase 2 UAT Verdict:** **PASSED** — synthetic end-to-end, model, failure, and 4,700-row local workload scenarios pass.
* **Phase 2 Morpheus Review:** **PASSED** — the staged CSV-to-flat-JSONL boundary, SQLMesh/Node/DuckDB sequencing, run-scoped Jev mappings, bounded taxonomy validation, failure publication rules, and stated workload/privacy limits match ADR-0037. Review also corrected stale architecture text about pending runtime approval, a proposed command shape, and unsupported resume behavior.
* **Summary:** Synthetic cases validate CSV-to-flat-JSONL hydration, SQLMesh reconciliation, bounded Jev classifications, run-scoped map reuse, fallback behavior, stage failure handling, review export, the stated local row volume, and the incomplete CLI error path. The 4,700-pair run completed in 10.286 seconds on this machine. After the scale scenario was added, `bobp make test-js` passed (310/310), `bobp make lint` passed, and `bobp make check` passed including Python/SQLMesh tests and secret scanning. No live Jev call or owner data was used; a future run on the owner's CSVs remains a production-data acceptance opportunity. The Trin skill's `bobp make judge-trace DATE=2026-10-17` check was attempted, but this worktree's Makefile has no `judge-trace` target; no source-trace result is available.

*Self-check: rubric UAT: COVER=S STEPS=A FAIL=S DATA=S EVID=A. Covers every Phase 1 criterion with isolated synthetic data, exact commands, negative paths, and captured counts/statuses; no arbitrary JSONL input is claimed.*
