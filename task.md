# Sprint 30 Task Board: A console that uses the desktop

*   **Goal**: One diagram that follows the last choice, a short run rack, and a run view that uses the desktop width (three columns), checked at five widths and at 50 percent zoom.
*   **Tier**: Tier 2 (story and architecture in one document)
*   **Total Points**: about 12
*   **Branch**: `sprint-30` (cut from `main` bb866aa)
*   **Status**: Complete 2026-11-06 (launched); branch `sprint-30` committed, not merged or pushed
*   **Plan**: `docs/sprints/STORY_ARCH_SPRINT30.md`. Backlog: "Console UX pass" in `docs/BACKLOG.md`; decision 44.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-06*)

---

## Sprint Execution Phases

Edit files with Edit/Write only (owner rule: no sed, no scripts). The page is checked in a browser: run the browser suite at the end of each phase. Commit once per reviewed phase: `Phase <N>: <summary>`.

### Phase 1: One diagram (UND-114)
*Phase goal: the diagram and step view are one section outside the tube panel, and follow the last choice (run or plan).*
- [x] **Task 1.1:** Move the diagram and step view into `section.diagram-panel`; remove the start panel's `#plan`; add SHOW PLAN; `state.view`; plan mode through `drawDiagram` and `drawStep` (a run-like object); the plan titles and notes; hold choice from the plan; PLAY returns to the run. Update the browser tests that look in `#plan-wrap`. **L3**. (*Owner: Neo | Trace: UND-114 AC1-5 | Verification: browser tests for plan mode, hold click, return to run*)
- [x] **Task 1.2:** UAT on the live console: pick a play (plan shows), click a beat, START, see the run; choose an old tab and see its diagram. **L1**. (*Owner: Trin | Trace: UND-114 | Verification: verdict in `agents/CHAT.md`*)
- [x] **Task 1.3:** Security quick pass, then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict lines*)

### Phase 2: A short rack (UND-115)
- [x] **Task 2.1:** `rack()` keeps the newest 8 per play and the chosen run, `N older` / `fewer` buttons, a folded unreadable group; keyboard use. **L2**. (*Owner: Neo | Trace: UND-115 AC1-3 | Verification: browser tests with 12 seeded runs and unreadable ones*)
- [x] **Task 2.2:** UAT on the live console's real rack. **L1**. (*Owner: Trin | Trace: UND-115 | Verification: verdict*)
- [x] **Task 2.3:** Security quick pass, then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict lines*)

### Phase 3: The width (UND-116)
- [x] **Task 3.1:** Grid areas by width (three, two, one column); the printer's paper as tall as its lines. **L2**. (*Owner: Neo | Trace: UND-116 AC1-2 | Verification: browser tests*)
- [x] **Task 3.2:** Browser tests at 390, 1280, 1600, 1920, 2560 and 1920 at 50 percent zoom: the columns and no sideways scroll. **L2**. (*Owner: Neo, Trin | Trace: UND-116 AC3-4 | Verification: the new tests pass; the whole suite passes*)
- [x] **Task 3.3:** Screenshots at each width read by Smith; security quick pass; code review. **L1**. (*Owner: Smith, Switch, Morpheus | Trace: UND-116 | Verification: verdict lines*)

---

## Stage 3: Sprint Closeout

- [x] **Task C.1:** SDLC conformance check (`*devops sdlc-check`). (*Owner: Tank | Verification: `bobp make check` exit 0*)
- [x] **Task C.2:** Document grooming (USER_GUIDE, ARCH, changelog, lessons), chat report. (*Owner: Oracle | Verification: docs changed*)
- [x] **Task C.3:** End-to-end user testing against `docs/sprints/UAT_PLAN_SPRINT30.md`. (*Owner: Smith*)
- [x] **Task C.4:** Retrospective (`docs/sprints/RETRO_SPRINT30.md`). (*Owner: Mouse*)
- [x] **Task C.5:** Sprint launch. Merge and push only when the owner asks. (*Owner: Cypher*)
