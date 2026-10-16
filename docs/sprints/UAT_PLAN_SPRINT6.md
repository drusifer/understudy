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
| UAT-UND-27-01..05 | rack, greyed sketches, refusals, port/host/token | Phase 2 | pending |
| UAT-UND-29-01..05 | play, stop, refusals, logs | Phase 3 (server), Phase 4 (page) | pending |
| UAT-UND-28-01/02/05 | dial, faders, keyboard | Phase 4 | pending |
| UAT-UND-30-01..04 | tube | Phase 5 | pending |
| UAT-UND-31-01..03 | printer | Phase 5 | pending |
| UAT-UND-32-01..05 | panels, saving, factory reset | Phase 6 | pending |
| UAT-UND-33-01..03 | docs, browser test, evening switch | Phase 7 | pending |

## 4. Defects
- Phase 1: none. 259 unit tests, lint clean.
