# Sprint 12 Story + Architecture (Tier 2): One move at a time

*   **Total Points**: 3 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-12` (cut from `sprint-11`, which awaits merge with sprint 10)
*   **Source**: owner, 2026-10-17: "add the step feature to go one move at a time" - on the
    dashboard, as the watch page already can (`--watch`, ADR-0016). Recorded in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gates 1 and 2 (2026-10-17)

## STORY-UND-39: Step a run one move at a time from the console
**Points:** 3

**As the** owner,
**I want** to step the understudy one move at a time from the dashboard,
**so that** I can watch each state change on the tube and each decision print before the next move.

### Acceptance Criteria
1. Beside PLAY are two buttons: **STEP** and **PAUSE**. Idle, STEP starts the sketch with the
   controls' values, lets exactly one move through, and pauses before the next; each further STEP
   lets one more move through. Jev is asked nothing while paused.
2. While a run plays, PAUSE pauses it before its next move and reads **RESUME**; RESUME lets it run on.
   STEP is enabled only while paused (and when idle).
3. STOP still stops a run, paused or not (a paused run stops at once, as Ctrl-C does with `--watch`).
4. While paused the tube's caption reads `paused`, and READY's hint says "STEP for the next move,
   RESUME to run on"; time spent paused does not count toward the run's idle limits.
5. Every theme and mode styles the two buttons; keyboard reaches them; a phone fits them.

## Architecture (Morpheus)

- **The run takes a gate** (ADR-0033): `runSketch` gains a `gate` option (a `createGate` from
  `watch/gate.mjs`); the run loop already asks `gate.beforeMove()` before each move. Without it
  nothing changes (OPEN_GATE, or the watch page's gate with `--watch`).
- **Runner**: each run gets a gate whose changes go to the hub as
  `{ event: 'dashboard', paused, waiting }`; `play({ ..., paused: true })` starts paused;
  `pause()`, `step()`, `resume()` (409 when nothing runs or the gate refuses). Console actions
  `pause`, `step`, `resume`.
- **Page**: STEP idle = play paused then step; the buttons follow the `paused` lines.
- Tests: runner (start paused, step one move, resume, stop while paused); browser (STEP takes one
  move; PAUSE/RESUME; STOP while paused).
- Docs: USER_GUIDE, DASHBOARD.

## Out of Scope
- Stepping backwards; replaying a finished run on the dashboard.

rubric STORIES: OUT=S TEST=S FAIL=A SCOPE=A SIZE=A DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=A
