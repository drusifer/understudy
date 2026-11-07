# Sprint 32 Task Board: The beat box

*   **Goal**: Replace the beat tube with a beat box: a chart picture of the current beat's inputs and outputs (gauges, donuts, bars), an iteration stepper for beats that run once per row, Jev and blend options as bars; fold the scattered expanders into the box and a run header.
*   **Tier**: Tier 2. **Points**: about 14. **Branch**: `sprint-32` (cut from `sprint-31`, committed, not yet merged)
*   **Status**: In progress (planned 2026-11-06)
*   **Plan**: `docs/sprints/STORY_ARCH_SPRINT32.md`. Decision 45.

## Stage 0: SDLC Gate

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists. (*Owner: Mouse | Verification: present 2026-11-06*)

## Phase 1: The runner says what flows through a beat (UND-118)

- [x] **Task 1.1:** Tests first, then `src/play/profile.py` (`profile(rows)`: number, text and other columns; at most 6; values cut). **L2**. (*Owner: Neo | Trace: UND-118 AC1 | Verification: `test_play_profile.py`*)
- [x] **Task 1.2:** Tests first, then `columns` on a top-level `beat_completed`'s pieces, the `iteration` event from `_run_each`, `levels` on `jev_read`. **L3**. (*Owner: Neo | Trace: UND-118 AC2-4 | Verification: `test_run_story.py` and a small each-play test*)
- [x] **Task 1.3:** UAT: the real household replay's outputs byte-identical to `build/baseline-sprint28/full`; the log's growth reported. **L2**. (*Owner: Trin | Trace: UND-118 AC5 | Verification: comparison in `agents/CHAT.md`*)
- [x] **Task 1.4:** Security quick pass (what values the log now carries), then code review. **L1**. (*Owner: Switch, Morpheus*)

## Phase 2: The beat box (UND-119)

- [x] **Task 2.1:** `step_details` gains iterations, Jev answers and decisions by beat (live and replay). **L2**. (*Owner: Neo | Trace: UND-119 AC3, 4, 6 | Verification: view and replay tests*)
- [x] **Task 2.2:** `src/dashboard/box.js`: the box (IN, beat, OUT), gauge, donut, bars, the iteration stepper, Jev and decision bars; the tube and step view removed from the page. **L3**. (*Owner: Neo | Trace: UND-119 AC1-5 | Verification: browser tests*)
- [x] **Task 2.3:** UAT on the live console with an evening replay (each pass, Jev bars) and the household plan; contrast test and widths pass. **L2**. (*Owner: Trin | Trace: UND-119*)
- [x] **Task 2.4:** Security quick pass, then code review. **L1**. (*Owner: Switch, Morpheus*)

## Phase 3: One place for the run's details (UND-120)

- [ ] **Task 3.1:** The run header line; remove the DECISIONS and JEV READS expanders and the SUMMARY list; gauges keep their figures; dead script and styles removed; docs. **L2**. (*Owner: Neo, Oracle | Trace: UND-120 AC1-3 | Verification: browser tests, `rg` for dead ids*)
- [ ] **Task 3.2:** UAT, security quick pass, code review. **L1**. (*Owner: Trin, Switch, Morpheus*)

## Stage 3: Closeout

- [ ] **Task C.1:** SDLC check. (*Owner: Tank*)
- [ ] **Task C.2:** Docs groom (USER_GUIDE, PLAYS, ARCH, ADR, changelog, lesson), chat report. (*Owner: Oracle*)
- [ ] **Task C.3:** User test against `docs/sprints/UAT_PLAN_SPRINT32.md`. (*Owner: Smith*)
- [ ] **Task C.4:** Retro. (*Owner: Mouse*)
- [ ] **Task C.5:** Launch. Merge and push only when the owner asks. (*Owner: Cypher*)
