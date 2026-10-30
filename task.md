# Sprint 19 Task Board: The coffee proof of concept

* **Goal**: A shop owner writes one YAML sketch and runs `understudy run coffee_week.yaml` to get next week's ingredients: owner's rules, SQL, one Jev judgement, capture and replay.
* **Tier**: Tier 1 (Major)
* **Total Points**: 28
* **Branch**: `sprint-19`
* **Plan**: `docs/sprints/USER_STORIES_SPRINT19.md` (UND-60..67), `docs/sprints/ARCH_SPRINT19.md`, `docs/sprints/DESIGN_SKETCH_MODEL.md`, `docs/DOMAIN.md`, epic `docs/sprints/EPIC_PYTHON_PORT.md`
* **Status**: Planned 2026-10-29; stories (Smith Gate 1) and architecture (Gate 2) approved; plan reviewed by Morpheus (Phase 4 split in two so every phase has at most three tasks and one owner per task)
* **Rules**: no back-compat, YAGNY, DRY (every duplicate removed or moved, none copied), tests at the base of the pyramid, `bobp make` only, edit with the Edit tool.

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` exists; ARCH_SPRINT19 section 7 adds only ordinary dependencies (`ruamel.yaml`, `jsonschema`) and edits to existing targets, so no mechanism approval is needed. (*Owner: Mouse*)

## Sprint Execution Phases

### Phase 1: Build setup and shared modules (UND-61 groundwork)
*Phase goal: the environment and the shared code the new package needs, with no duplicates created.*

- [x] **Task 1.1:** `*devops` Pin `ruamel.yaml` and `jsonschema` as direct dependencies (`lock-py`), add `src/sketch` and its tests to the `lint` ruff paths, add `.understudy/` to `.gitignore`; update `docs/SDLC.md`. (*Owner: Tank | Verification: `bobp make install`, `bobp make lint`, `bobp make check` pass from a clean install.*)
- [x] **Task 1.2:** `*refactor` Move the Jev wrapper to `src/jev.py` and the output-destination policy to `src/paths.py`; `src/etl` imports them; delete the originals. (*Owner: Neo | Verification: `bobp make test-py` passes with the moved modules and no copy left (`git grep` finds one definition of each).*)
- [x] **Task 1.3:** Review: shared modules, dependencies, SDLC edit. (*Owner: Morpheus | Verification: verdict recorded; commit `Phase 1: ...`.*)

### Phase 2: Load and check a sketch (UND-61)
*Phase goal: a wrong sketch is refused before anything runs, naming file, path, value and the nearest good one.*

- [x] **Task 2.1:** `*impl` `src/sketch/model.py`, `loader.py` (ruamel YAML 1.2, relative paths, `--source` overrides), `check.py` and `schema/decision_sketch.schema.json`. (*Owner: Neo | Verification: unit tests for every UND-61 AC: bad sketch, nearest-good message, segment shares, missing source file, slices read as text (`70:30` stays text), outcome checks.*)
- [x] **Task 2.2:** UAT: UND-61 AC 1-5 on the coffee sketch and deliberately broken copies. (*Owner: Trin | Verification: UAT rows in `docs/sprints/UAT_PLAN_SPRINT19.md`.*)
- [x] **Task 2.3:** Review against ADR-0042 and the domain invariants 1, 2, 7. (*Owner: Morpheus | Verification: verdict; commit `Phase 2: ...`.*)

### Phase 3: Decide, blend, forbid (UND-63)
*Phase goal: the owner's logic produces weighted rows, hard rules always win.*

- [x] **Task 3.1:** `*impl` `conditions.py` (operators `eq ne lt le gt ge in not_in has`, `and or not`, slices), `decide.py` (trees, weights as number or `if/then/else`), `blend.py` (weighted average, `forbid`, renormalise, `on_empty`, default fail). (*Owner: Neo | Verification: unit tests for every UND-63 AC, operator tables, a `forbid` that empties a segment fails naming rule and segment, weights sum to 1 after every step.*)
- [x] **Task 3.2:** UAT: UND-63 AC 1-5. (*Owner: Trin | Verification: UAT rows; the under-18 rule never broken in any combination.*)
- [x] **Task 3.3:** Review against ADR-0041 and ADR-0044, invariants 3 to 5. (*Owner: Morpheus | Verification: verdict; commit `Phase 3: ...`.*)

### Phase 4: Run the owner's machine (UND-62, UND-60 AC1-4)
*Phase goal: the Python package runs a sketch's machine, writes a run folder and answers on the command line.*

- [x] **Task 4.1:** `*impl` `machine.py` (the sketch's python-statemachine YAML, loop, guards from explicit conditions), `run.py` (run folder, manifest, events, outputs last, reuses `src/paths.py`), `cli.py` (flags `--source`, `--out`, exit codes 0/1/2, one line per stage). (*Owner: Neo | Verification: tests for UND-62 AC 1-4 on `tests/fixtures/machine_branch.yaml`, UND-60 AC 1-4, a failed stage leaves no output.*)
- [x] **Task 4.2:** UAT: UND-62 AC 1-4 and UND-60 AC 1-4. (*Owner: Trin | Verification: UAT rows; exit codes and last error line checked.*)
- [x] **Task 4.3:** Review against ADR-0040 and invariants 1, 9, 10. (*Owner: Morpheus | Verification: verdict; commit `Phase 4: ...`.*)

### Phase 5: Replace the old Node commands (UND-60 AC8)
*Phase goal: `understudy run` and `understudy check` are the Python commands; the old Node run and check are gone.*

- [x] **Task 5.1:** `*refactor` Point `run` and `check` in `src/cli.mjs` at the Python package; delete the old Node `run`/`check` implementations (`src/run.mjs`, `src/sketch.mjs`, `src/machine.mjs`, `src/engine.mjs` and what only they use) and their tests; update the usage text. (*Owner: Neo | Verification: `bobp make test-js` passes on what remains; `tests/cli.test.js` covers the launcher and exit codes; `git grep` finds no use of the deleted modules.*)
- [x] **Task 5.2:** UAT: `understudy run` and `understudy check` through the Node launcher; the other old commands fail with an error that says they are being rebuilt, not a stack trace. (*Owner: Trin | Verification: UAT rows for UND-60 AC1, AC2, AC8.*)
- [x] **Task 5.3:** Review against ADR-0045 and the epic's purge list (what is gone, what remains and why). (*Owner: Morpheus | Verification: verdict; commit `Phase 5: ...`.*)

### Phase 6: Sources, capture and replay (UND-60 AC5-7, UND-65 groundwork)
*Phase goal: file and Jev sources, one `--replay` flag, test and live data never mixed.*

- [ ] **Task 6.1:** `*impl` `sources/file.py`, `sources/jev.py` (a `kind: jev` source: `instructions`, `criteria`, `state` from `from:` sources, through `src/jev.py`), `sources/capture.py` (capture after a complete read, keep the last 5 runs, replay one complete run, never go live, `stale` flag, `mode` in the summary). (*Owner: Neo | Verification: tests with a Jev double for capture, replay of the latest complete run, a named run, a directory, missing-source stop, stale flag, no fallback to live.*)
- [ ] **Task 6.2:** UAT: UND-60 AC 5-7. (*Owner: Trin | Verification: UAT rows; a replay makes no network call.*)
- [ ] **Task 6.3:** Review against ADR-0043 and invariants 6, 9. (*Owner: Morpheus | Verification: verdict; commit `Phase 6: ...`.*)

### Phase 7: Coffee end to end (UND-64, UND-65, UND-66)
*Phase goal: the coffee sketch and its weather subsketch run from fixtures and replay to a reproducible ingredient file.*

- [ ] **Task 7.1:** `*impl` `stages.py` (`etl.split_by_share`, `etl.join_weights`, `convert.recipes` with round-up to packs, `sink.<name>`, `sketch.<file>` as a nested run sharing the run id), the invented fixtures under `tests/fixtures/coffee/` (about 1,600 drinks, five segments, two Almanac descriptions) and `coffee_week.yaml` plus `weather_change.yaml`. (*Owner: Neo | Verification: end-to-end test on a Jev double: split sums to the total, under-18 rule holds, night workers unchanged by warm weather, pack round-up, byte-identical rerun with `--replay`.*)
- [ ] **Task 7.2:** UAT: UND-64, UND-65, UND-66 and the full command on the fixtures. (*Owner: Trin | Verification: UAT rows; two `--replay` runs are byte-identical; output outside tracked folders.*)
- [ ] **Task 7.3:** Review the whole slice against the architecture and the epic's purge list (no duplicate introduced). (*Owner: Morpheus | Verification: verdict; commit `Phase 7: ...`.*)

## Sprint Closeout

- [ ] **Task C.1:** Tank `*devops sdlc-check`: `distclean`, `install`, `check`, repeat `install`; SDLC updated. (*Owner: Tank | Verification: all green; `docs/SDLC.md` Last verified line.*)
- [ ] **Task C.2:** Live judgement, with the owner's go-ahead: one live Jev run on the fixture descriptions; the capture copied into `tests/fixtures/` as the committed replay fixture; rubric reworded and rerun once if the answer is not sensible (UND-67). (*Owner: Trin | Verification: probabilities and resulting hot/iced weights in the UAT plan.*)
- [ ] **Task C.3:** Oracle `*ora groom`: ADR-0040..0045 into `docs/DECISIONS.md`, superseded ADRs marked, USER_GUIDE and CHANGELOG, lessons, chat archive after launch. (*Owner: Oracle | Verification: artifact rubrics pass; `bobp chat-report --moniker SPRINT_19`.*)
- [ ] **Task C.4:** Smith `*user test`, retros, backlog. (*Owner: Smith, all | Verification: UAT rubric verdict; each persona's retro in `agents/CHAT.md`.*)
- [ ] **Task C.5:** Cypher `*pm launch`; merge and push only when the owner asks. (*Owner: Cypher | Verification: launch recorded in `agents/CHAT.md`.*)
