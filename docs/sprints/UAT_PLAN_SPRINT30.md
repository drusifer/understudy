# UAT Plan: Sprint 30, a console that uses the desktop

*   **Stories**: UND-114 to UND-116 (`docs/sprints/STORY_ARCH_SPRINT30.md`)
*   **Data**: the owner's live console (evening run and 28 unreadable runs), seeded runs in the browser tests
*   **Status**: Executed 2026-11-06

## Scenarios

| ID | Story / AC | Steps | Expected | Result |
|---|---|---|---|---|
| UAT-30-1 | UND-114 AC1-3 | Live console: load; pick evening in START A RUN; choose the run tab | `DIAGRAM OF RUN <time>` (one diagram), then `PLAN OF evening` in the same place, then the run again | Pass |
| UAT-30-2 | UND-114 AC3-5 | Browser tests: SHOW PLAN, click a flow beat, Enter and Space, PLAY | the hold is set and cleared, sent as `--stop-at`, spent by the start; the step view describes the held beat | Pass |
| UAT-30-3 | UND-115 AC1-3 | Live rack (1 evening run, 28 unreadable); browser test with 12 runs and 3 unreadable | one row; `28 unreadable` button; 8 tabs + `4 older`, `fewer`, the chosen old run stays | Pass |
| UAT-30-4 | UND-116 AC1 | Screenshots at 1920 and 1280 read by Smith | three columns at 1920 (printer, readouts, diagram), two at 1280 (diagram under both) | Pass |
| UAT-30-5 | UND-116 AC2-4 | Browser tests at 390, 1280, 1600, 1920, 2560, 3840 | columns as specified; `scrollWidth <= clientWidth` at every width | Pass |
| UAT-30-6 | all | `bobp make check`, `bobp make test-browser` | 630 unit tests (about 31 s); browser 49/49 | Pass |

## Failure handling

A browser failure caused by a deliberate change is fixed in the test only when the new behavior is right (the contrast test now waits for the plan to settle before measuring).

## Evidence

`agents/CHAT.md` UAT posts, screenshots read during the sprint, `build/build.out`.
