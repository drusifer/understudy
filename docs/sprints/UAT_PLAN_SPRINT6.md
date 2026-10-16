# Sprint 6 Acceptance Test Plan (UAT): The dashboard, with atmosphere

*   **Author**: Trin
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT6.md` (UND-27..33) · **Arch**: `docs/sprints/ARCH_SPRINT6.md` · **Design**: `docs/design/DASHBOARD.md`
*   **Status**: In progress

## 1. Scope
Every acceptance criterion of UND-27..33, per phase, then end to end by Smith at close. Live Jev runs are optional (the dashboard runs sketches through the same `runSketch`); browser tests use a Jev double.

## 2. Preconditions
`bobp make install`, `bobp make install-browser` for browser tests. Throwaway folders under `build/uat/`.

## 3. Cases

| Case | Story / AC | Evidence | Result |
|---|---|---|---|
| UAT-UND-28-03/04 | switch input, `when:`, `--input together=off` | `tests/inputs.test.js`, `tests/engine.test.js` | PASS (Phase 1) |
| UAT-UND-27-01..05 | rack, greyed sketches, refusals, port/host/token | `tests/dashboard.test.js`, `tests/cli.test.js`; CLI smoke: URL printed, wrong path 404, Ctrl-C exit 0, non-folder exit 2 | PASS (Phase 2) |
| UAT-UND-29-01..05 | play, stop, refusals, logs | `tests/dashboardRun.test.js` (evening played by a double with mood=romantic centre=1.5; 409 on a second Play; STOP → interrupted, also when pressed while servers start; refusal printed; log written); page in Phase 4 | PASS (Phase 3, server) |
| UAT-UND-28-01/02/05 | dial, faders, keyboard | `tests/dashboardPage.test.js`; headless Chromium screenshots (build/uat/dash-1.png): evening dial, 4 coloured faders with Nixies (11 at top), READY green, square PLAY; CLI sketch played and printed; native buttons/range inputs with labels | PASS (Phase 4) |
| UAT-UND-30-01..04 | tube | `tests/tube.test.js`; screenshot build/uat/dash-tube.png: every evening state and edge labelled (OBSERVE, done + guards, STEP), finals inside, booked glowing at the end, colour ring + blended decision edge + orb with shares | PASS (Phase 5) |
| UAT-UND-31-01..03 | printer | `tests/dashboardPage.test.js`; screenshot build/uat/dash-printer.png: steps, removals, score tables with 11, ticket, outcome; paper scrolls back | PASS (Phase 5) |
| UAT-UND-32-01..05 | panels, saving, factory reset | `tests/settings.test.js` (only edited lines change, comments kept, check passes; refusals write nothing; allow-list; factory copy before first edit, restore), `tests/dashboardRun.test.js` (409 while running, power off stops); browser (build/uat/panels.png): range saved, invalid marked with reason, mood rename + default, power cycle restored | PASS (Phase 6) |
| UAT-UND-33-01..03 | docs, browser test, evening switch | Phase 7 | pending |

## 4. Defects
- Phase 1: none. 259 unit tests, lint clean.
- Phase 3: found and fixed in phase - a STOP pressed while the servers were starting was lost (the run listens for Ctrl-C only once started); the runner now delivers it on the start line. 268 tests.
