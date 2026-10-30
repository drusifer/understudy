# Sprint 20 Task Board: the evening and the household ETL as sketches

* **Goal**: The owner's two real pipelines run as sketches with `understudy run`: the evening at the cinema (with a seating subsketch, on file fixtures) and the household spending ETL (on his Monarch and Amex files). The old examples, the old schema and the ETL's own controller, MCP servers and command are deleted.
* **Tier**: Tier 1 (Major)
* **Total Points**: 26
* **Branch**: `sprint-20`
* **Plan**: `docs/sprints/USER_STORIES_SPRINT20.md` (UND-68..73), `docs/sprints/ARCH_SPRINT20.md` (ADR-0046..0049), epic `docs/sprints/EPIC_PYTHON_PORT.md`
* **Status**: Planned 2026-10-30; stories (Smith Gate 1) and architecture (Gate 2) approved; awaiting Morpheus Step 3a review
* **Rules**: no back-compat, YAGNY, DRY (every duplicate removed or moved), tests at the base of the pyramid, `bobp make` only, edit with the Edit tool, full test suite at every phase gate.

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` exists; ARCH_SPRINT20 section 7 adds no dependency, language or make target, so no Phase 0. (*Owner: Mouse*)

## Sprint Execution Phases

### Phase 1: The model's small gaps (UND-68)
*Phase goal: walk away, count and weight inputs, and several reads of one source work and are documented.*

- [ ] **Task 1.1:** `*impl` `on_empty: walk_away` (exit 0, no sink output, `walked away at <stage>`); `count` and `weight` inputs with `--input` and range errors; a source read twice with different params, one captured sample per request hash. (*Owner: Neo | Verification: unit tests for every UND-68 AC, including `tickets must be 1 to 4, got 9`, unknown input names the known ones, and coffee tests unchanged.*)
- [ ] **Task 1.2:** UAT: UND-68 AC 1-5, with a doc check of `docs/SKETCHES.md`. (*Owner: Trin | Verification: UAT rows in `docs/sprints/UAT_PLAN_SPRINT20.md`; full suite green.*)
- [ ] **Task 1.3:** Review against the architecture sections 3 and 5. (*Owner: Morpheus | Verification: verdict; commit `Phase 1: ...`.*)

### Phase 2: Candidates from a file, shortlist, Jev pick (UND-73)
*Phase goal: a decision weighs options that exist only in a file and Jev chooses among the shortlist.*

- [ ] **Task 2.1:** `*impl` outcome dimension `{from, key}`, `shortlist: {at_most: n}` on a blend, `kind: jev` with `options:` from a stage's shortlist; refusal of answers outside it; capture and replay for that read. (*Owner: Neo | Verification: unit tests for every UND-73 AC, including three candidates keep three, the near-miss message, a Jev double that answers outside the list.*)
- [ ] **Task 2.2:** UAT: UND-73 AC 1-4. (*Owner: Trin | Verification: UAT rows; full suite green.*)
- [ ] **Task 2.3:** Review against ADR-0048, domain invariants (Jev chooses, never writes). (*Owner: Morpheus | Verification: verdict; commit `Phase 2: ...`.*)

### Phase 3: Seating is a subsketch (UND-69)
*Phase goal: a seat map becomes blocks of adjacent free seats and one hold the parent can use.*

- [ ] **Task 3.1:** `*impl` `seating.yaml`, the blocks stage (DuckDB gaps and islands), the `returns` hold, `none` outcome, fixtures under `tests/fixtures/evening/`. (*Owner: Neo | Verification: unit tests for every UND-69 AC, including the E3-E5 / E8-E9 example and a missing `seat` column.*)
- [ ] **Task 3.2:** UAT: UND-69 AC 1-5. (*Owner: Trin | Verification: UAT rows; full suite green.*)
- [ ] **Task 3.3:** Review. (*Owner: Morpheus | Verification: verdict; commit `Phase 3: ...`.*)

### Phase 4: The evening (UND-70)
*Phase goal: the evening books like the owner, or walks away.*

- [ ] **Task 4.1:** `*impl` `examples/evening/evening.yaml` and fixtures, replacing the old example outright; scaled-weight stage for tomato and centre; every input case in UND-70 AC2. (*Owner: Neo | Verification: unit tests for every UND-70 AC; `understudy check` and a Jev-double run pass.*)
- [ ] **Task 4.2:** UAT: UND-70 AC 1-6, walk-away and replay included. (*Owner: Trin | Verification: UAT rows; full suite green.*)
- [ ] **Task 4.3:** Review. (*Owner: Morpheus | Verification: verdict; commit `Phase 4: ...`.*)

### Phase 5: The ETL's expected result and its stage wrappers (UND-71, part 1)
*Phase goal: the current ETL's answer is frozen before anything moves, and CSVs read as file sources.*

- [ ] **Task 5.1:** `*impl` Commit `tests/fixtures/etl/expected/result.jsonl` and summary from the current ETL on the fixtures (before any ETL change); `format: csv` file sources; `stages_etl.py` wrappers over the existing functions. (*Owner: Neo | Verification: expected files exist and a test regenerates and compares them; a CSV with no `merchant` column fails with `<file>: missing a required merchant column (recognized: …)`.*)
- [ ] **Task 5.2:** UAT: UND-71 AC 1, 5. (*Owner: Trin | Verification: UAT rows; full suite green.*)
- [ ] **Task 5.3:** Review against ADR-0046, ADR-0049. (*Owner: Morpheus | Verification: verdict; commit `Phase 5: ...`.*)

### Phase 6: The household sketch (UND-71, part 2)
*Phase goal: the sketch makes the same answer as the old ETL, offline, then on the owner's real files.*

- [ ] **Task 6.1:** `*impl` `sketches/household.yaml` with the machine of `stages.yaml`, the three Jev judgements as `kind: jev` sources with captured replay fixtures. (*Owner: Neo | Verification: sorted-record equality with the expected file, summary numbers equal, failing stage publishes nothing, replay offline.*)
- [ ] **Task 6.2:** UAT: UND-71 AC 2-6, then the owner's real-file run (5,074 records; counts and paths only). (*Owner: Trin | Verification: UAT rows; no private text in output or under `src/`.*)
- [ ] **Task 6.3:** Review against ADR-0047. (*Owner: Morpheus | Verification: verdict; commit `Phase 6: ...`.*)

### Phase 7: Purge and docs (UND-72)
*Phase goal: one kind of sketch and one way to run it.*

- [ ] **Task 7.1:** `*refactor` Delete the listed examples, `seed/`, old schema, Node box office and ratings servers, `etl run`, the ETL controller, `stages.yaml`, `source_server.py` and MCP paging; rewrite the docs; mark ADR-0011, 0018, 0030 superseded. (*Owner: Neo | Verification: `git grep` finds none of the deleted names; `understudy etl run` reports an unknown command.*)
- [ ] **Task 7.2:** UAT: UND-72 AC 1-4. (*Owner: Trin | Verification: full `bobp make` suite green.*)
- [ ] **Task 7.3:** Review against the epic's purge list. (*Owner: Morpheus | Verification: verdict; commit `Phase 7: ...`.*)

## Sprint Close

- [ ] **Task C.1:** `*devops sdlc-check`. (*Owner: Tank | Verification: clean rebuild; "Last verified" updated.*)
- [ ] **Task C.2:** `*ora groom`, new ADRs, lessons, chat report. (*Owner: Oracle*)
- [ ] **Task C.3:** `*user test` sprint 20 against `UAT_PLAN_SPRINT20.md`. (*Owner: Smith*)
- [ ] **Task C.4:** Retro, then `*pm launch`. (*Owner: all, Cypher*)
