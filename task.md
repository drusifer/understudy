# Sprint 16 Task Board: Staged Local ETL with Jev-Guided Categories

* **Goal**: Run the Monarch and Amex CSV exports through a repeatable local cleanup, reconcile overlapping transactions with source provenance, and categorize merchants from a fixed Jev taxonomy for owner review. Keep the workload local and sized for roughly 4,700 reconciled transactions.
* **Tier**: Tier 1 (Major)
* **Total Points**: 18
* **Branch**: `sprint-16`
* **Status**: Launched 2026-10-27 on branch `sprint-16`; not yet committed or merged (owner's call, per `docs/SDLC.md`).
* **Scope**: Monarch and Amex CSV inputs staged as flat JSONL for SQLMesh; no arbitrary JSONL or nested JSON input, Sheets, or MCP integration. Keep transaction data and private CSVs under ignored `build/runs/` and out of git and chat.

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Confirm `docs/SDLC.md` exists and its mechanism approval rules apply to adding Python/SQLMesh. (*Owner: Mouse | Verification: SDLC present and §6 classifies toolchain and make-target changes as Mechanism requiring Tank + owner approval.*)

## Sprint Execution Phases

### Phase 0: SQLMesh and Python feasibility / mechanism gate
*Phase goal: Resolve whether SQLMesh + DuckDB can be added through a repeatable isolated Python environment, and obtain both Tank and owner approval before any implementation begins.*

- [x] **Task 0.1:** Complete a documentation-backed feasibility review of SQLMesh + DuckDB for per-run snapshot paths and staged models; record the proposed sequential SQLMesh → Node `category_map` → SQLMesh handoff and the pinned toolchain recommendation. This is a document review only, not an execution probe. The shared-database handoff, including DuckDB read/write interoperability and SQLMesh run-variable behavior, remains unprobed and is gated on mechanism approval. (*Owner: Tank | Verification: review and limitations recorded in `agents/tank/phase0_sprint16.md`; no install, runtime change, or probe performed.*)
- [x] **Task 0.2:** Define the isolated Python/SQLMesh/DuckDB versions and required `bobp make` targets, then secure explicit Tank and owner approval for the mechanism change. (*Owner: Tank | Verification: recommendations in `agents/tank/phase0_sprint16.md`; owner approved with “proceed” on 2026-10-17; Tank approves the documented pinned mechanism.*)
- [x] **Task 0.3:** Establish the approved isolated environment and repeatable make entry points; update `docs/SDLC.md` through Tank's ownership and verify setup plus the synthetic SQLMesh → Node DuckDB → Python reopen handoff. (*Owner: Tank | Verification: clean `bobp make distclean` → `bobp make install` → `bobp make check` passes; second install is idempotent; `bobp make probe-etl` passes.*)

**Gate:** Owner and Tank mechanism approvals are recorded; clean setup and sequential shared-DuckDB handoff probe passed. Phase 1 may begin. If a runtime or adapter boundary changes, return to Morpheus and Tank before proceeding.

### Phase 1: Local CSV hydration and deterministic reconciliation
*Phase goal: Validate and snapshot both private CSVs, convert them to flat JSONL records, load those through SQLMesh into local DuckDB, and produce deterministic matched, unmatched, and ambiguous transaction records with source provenance (STORY-UND-46; STORY-UND-48).*

- [x] **Task 1.1:** Implement the staged input and reconciliation slice: accept explicit Monarch and Amex CSV paths, validate required headers, snapshot CSVs and hashes under ignored `build/runs/<run-id>/`, convert each row to flat JSONL with original fields and provenance, load JSONL through SQLMesh, and add SQL models that pair only unique date+amount matches while preserving single-source and ambiguous rows. (*Owner: Neo | Verification: `bobp make test-js`, `bobp make test-py`, and `bobp make test-etl` pass; synthetic `bobp make run ARGS="etl run --monarch tests/fixtures/etl/monarch.csv --amex tests/fixtures/etl/amex.csv"` reports one match and two unmatched rows.*)
- [x] **Task 1.2:** Run targeted acceptance checks for valid inputs, missing files/headers, one-to-one overlaps, ambiguous keys, and incomplete-stage behavior. (*Owner: Trin | Verification: Phase 1 scenarios and observed results recorded in `docs/sprints/UAT_PLAN_SPRINT16.md`; focused JavaScript/Python/SQLMesh tests and synthetic run pass.*)
- [x] **Task 1.3:** Review the phase against the owner-directed CSV-to-flat-JSONL boundary, SQLMesh ownership, source provenance, privacy requirements, and reconciliation rules. (*Owner: Morpheus | Verification: review passed; decision/architecture artifacts reflect the accepted conversion step; no Phase 1 defects found.*)

### Phase 2: Jev taxonomy choices, run-scoped maps, and review output
*Phase goal: Ask Jev once per distinct unknown merchant key using the fixed category/subcategory taxonomy with `Misc`, reuse valid choices through the run, and export auditable results and counts (STORY-UND-47; STORY-UND-48).*

- [x] **Task 2.1:** Add the fixed versioned category/subcategory taxonomy, bounded Jev choices for distinct merchant keys, run-scoped validated mappings, final SQL models, and local review output. Include provenance and counts; invalid/empty choices use `Misc` with a review marker; failed Jev/model stages cannot mark output complete. (*Owner: Neo | Verification: JavaScript unit/integration tests cover valid/off-list/empty/repeated choices, batching, SQLMesh model tests cover taxonomy join and fallback, synthetic end-to-end run checks summary and review export.*)
- [x] **Task 2.2:** Run targeted acceptance on representative fixtures and the provided workload when available; verify bounded Jev choices, duplicate-key reuse, output provenance, counts, privacy, and failure status. (*Owner: Trin | Verification: synthetic UAT in `docs/sprints/UAT_PLAN_SPRINT16.md`; the 4,700-pair SQLMesh-backed run completed in 10.286 s, `bobp make test-js` passed 310/310, and `bobp make check` passed. No private CSV or live Jev call was used.*)
- [x] **Task 2.3:** Review final SQL/decision handoff, deterministic replay, scope, and implementation against ADR-0037 and the approved architecture. (*Owner: Morpheus | Verification: Phase 2 review passed and is recorded in `agents/CHAT.md`, `docs/sprints/UAT_PLAN_SPRINT16.md`, and updated architecture/ADR text.*)

## Sprint Closeout

- [x] **Task C.1:** Run the required SDLC conformance check, including clean environment setup and project quality gates; update the SDLC verification record. (*Owner: Tank | Verification: `bobp make distclean`, `bobp make install`, `bobp make check`, and a repeated `bobp make install` all pass; `docs/SDLC.md` records verification.*)
- [x] **Task C.2:** Groom sprint docs, record lessons/decisions, and archive the sprint chat report after launch. (*Owner: Oracle | Verification: required artifact rubrics pass and `bobp chat-report --moniker SPRINT_16` completes after Cypher's launch so the report includes the acceptance and retro gates.*)
- [x] **Task C.3:** Perform owner-facing sprint acceptance and usability review. (*Owner: Smith | Verification: UAT rubric verdict and approval recorded in `agents/CHAT.md`.*)
- [x] **Task C.4:** Post persona retrospectives and capture backlog items. (*Owner: All personas | Verification: each persona posts a retrospective in `agents/CHAT.md`.*)
- [x] **Task C.5:** Launch Sprint 16 after all closeout gates pass. (*Owner: Cypher | Verification: launch announcement and sprint completion recorded in `agents/CHAT.md`.*)
