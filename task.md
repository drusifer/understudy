# Sprint 18 Task Board: Tech-debt cleanup

* **Goal**: Delete dead code and an unused dependency, lint the Python, and tidy git. No back-compat, YAGNY, DRY.
* **Tier**: Tier 2 (Minor/Maintenance)
* **Branch**: `sprint-18`
* **Plan**: `docs/sprints/STORY_ARCH_SPRINT18.md` (UND-56..59)

## Stage 0: SDLC Gate
- [x] **Task 0.1:** `docs/SDLC.md` exists; mechanism changes (Node DuckDB removal, Python lint target) approved by the owner ("go 18"). (*Owner: Tank*)

## Phases
### Phase 1: Dead Sprint 16 ETL code (UND-56)
- [x] **Task 1.1:** `*refactor` Delete `csv_to_jsonl.py`, `reconciled_transactions.sql`, `categorized_transactions.sql` and their three tests. (*Owner: Neo | Verification: `bobp make test-py`, `test-etl` pass; grep finds no references.*)

### Phase 2: Node DuckDB (UND-57)
- [x] **Task 2.1:** `*refactor` Remove `@duckdb/node-api`, the probe script and `probe-etl`; update SDLC. (*Owner: Neo, Tank | Verification: clean install and `bobp make check` pass.*)

### Phase 3: Python lint (UND-58)
- [x] **Task 3.1:** `*impl` Add pinned `ruff` with a broad rule set (owner: "add python quality lints"), extend `lint`, fix findings (split `run()`), document in SDLC. (*Owner: Neo, Tank | Verification: `bobp make lint` and `check` pass.*)

### Phase 4: Git housekeeping (UND-59)
- [ ] **Task 4.1:** Remove the sprint-16 worktree and delete merged local sprint branches. (*Owner: Tank | Verification: `git worktree list`, `git branch`.*) PARTIAL: `sprint-1`..`sprint-15` deleted; the sprint-16 worktree (only a chat-log change inside) and the `sprint-16`/`sprint-17` branches remain because the environment denied the force-removal; the owner decides.

## Sprint Closeout
- [x] **Task C.1:** Tank `*devops sdlc-check` (distclean, install, check, repeat install).
- [x] **Task C.2:** Oracle groom, CHANGELOG, chat archive after launch.
- [x] **Task C.3:** Smith acceptance.
- [x] **Task C.4:** Retros.
- [x] **Task C.5:** Cypher launch; merge and push only when the owner asks.
