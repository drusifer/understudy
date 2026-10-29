# Sprint 18 — Tech-debt cleanup (Tier 2: story and architecture in one)

* **Branch**: `sprint-18` (cut from `main` 6c3d8b3, no worktree)
* **Owner rules**: no back-compat (delete outright, no shims), YAGNY, DRY.
* **Mechanism approval**: the owner said "go 18" on 2026-10-29, covering the removal of the Node DuckDB client and `probe-etl`, and a Python lint target.

## Stories

* **UND-56 Dead Sprint 16 ETL code is gone.** The Python controller (ADR-0038) no longer uses `src/etl/csv_to_jsonl.py`, `sqlmesh/models/reconciled_transactions.sql` or `categorized_transactions.sql`. AC: those files and their tests (`test_csv_to_jsonl.py`, `test_reconciliation.yaml`, `test_categorized_transactions.yaml`) are deleted; no remaining reference outside historical docs; `bobp make check` and a synthetic `etl run` still pass.
* **UND-57 No unused Node DuckDB.** AC: `@duckdb/node-api` leaves `package.json` and the lockfile; `scripts/etl-handoff-probe.mjs` and the `probe-etl` target (and its `.PHONY` entry) are deleted; `docs/SDLC.md` drops them; `bobp make check` passes after a clean install.
* **UND-58 Python is linted.** AC: `bobp make lint` also runs `ruff` over `src/etl` and `tests/python` with a pinned version in `pyproject.toml`/`uv.lock`; findings are fixed, not ignored wholesale; SDLC lists the target.
* **UND-59 Git housekeeping.** AC: the `understudy-sprint-16` worktree is removed and merged local `sprint-*` branches are deleted (remote branches stay).

## Architecture

* No new runtime behaviour. Deletions only, plus `ruff` as a dev dependency in the existing `uv` flow (`lock-py`, `install-py`). The lint target is a new standard make target, a mechanism change approved above.
* DRY: `lint` stays one target that runs both linters, so `check` needs no second hook.
* Failure: if a deletion breaks the synthetic ETL run or `test-etl`, restore nothing; fix the reference (no shims).
* ADR-0037/0038 text is history; leave it.

Smith Gate 1+2 (combined): no user-facing change except `probe-etl` disappearing from `bobp make help`. `rubric STORIES: OUT=S TEST=A ...` `rubric ARCH: BOUND=A FLOW=A FAIL=A USER=S DECS=A FEAS=A` — approved.
