# Sprint 31 Task Board: A big play, folded to its flow

*   **Goal**: A play of more than 40 nodes (household: 152) is drawn as its flow (31 nodes), with a button for everything and back.
*   **Tier**: Tier 2. **Points**: about 4. **Branch**: `sprint-31` (cut from `main` 49f5408)
*   **Status**: Complete 2026-11-06 (launched); branch `sprint-31` committed, not merged or pushed
*   **Plan**: `docs/sprints/STORY_ARCH_SPRINT31.md`. Backlog: "Big plays" in `docs/BACKLOG.md`.

## Stage 0: SDLC Gate

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists. (*Owner: Mouse | Verification: present 2026-11-06*)

## Phase 1: Fold the plan (UND-117)

- [x] **Task 1.1:** Tests first, then `fold` in `src/play/plan.py`, the `view` through `plan_layout`, `overlay`, `describe`, `replay`, the launcher and the routes (400 on an unknown view). **L2**. (*Owner: Neo | Trace: UND-117 AC1-3 | Verification: `test_play_plan.py`, `test_dashboard_chart.py`, `test_launcher.py`*)
- [x] **Task 1.2:** The page: `runUrl`, `state.diagramView`, the view button for a plan, a run and a replay; browser tests (big plan folds and unfolds; a small plan has no button). **L2**. (*Owner: Neo | Trace: UND-117 AC4 | Verification: `bobp make test-browser`*)
- [x] **Task 1.3:** UAT on the live console (household plan: 31 nodes, button to 152 and back); security quick pass; code review. **L1**. (*Owner: Trin, Switch, Morpheus | Verification: verdict lines in `agents/CHAT.md`*)

## Stage 3: Closeout

- [x] **Task C.1:** SDLC check: no manifest or Makefile change; check 637 tests, browser 51/51. (*Owner: Tank*)
- [x] **Task C.2:** Docs: USER_GUIDE, changelog, backlog. (*Owner: Oracle*)
- [x] **Task C.3:** User test (Smith) and retro: the household drawn in 31 nodes reads; the wide fan of arrows from the files is the next rough edge. (*Owner: Smith, Mouse*)
- [x] **Task C.4:** Launch. Merge and push only when the owner asks. (*Owner: Cypher*)
