# Sprint 4 Acceptance Test Plan (UAT): Watch the understudy live

*   **Owner**: Trin (per phase) / Smith (end to end) · **Date**: 2026-10-15 · **Branch**: `sprint-4` at `d3a2708`
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT4.md` · **Status**: PASSED — Smith approved

## 1. Scope of Acceptance Testing

UND-13 (the log as an event stream), UND-14 (live watch page), UND-15 (pause / step / resume),
UND-16 (replay), UND-17 (docs), through the real `understudy` command and a real browser
(Playwright's headless Chromium driving the page). Live runs use real Jev, capped at 20 steps.
Out of scope: probability distributions, controls beyond pause/step/resume, remote viewing
without a port forward (stories' Out of Scope).

## 2. Preconditions & Test Environment Setup

| Item | Value |
|---|---|
| Machine | Raspberry Pi (linux arm64), Node v24, Playwright 1.62.1 Chromium (headless) |
| Setup | `bobp make install` from clean (Tank's sdlc-check, d3a2708) |
| Key | `TYPESAFE_API_KEY` set for live runs |
| Page driver | during the sprint, scratch Playwright scripts (against AGENTS.md principle 1 - owner caught it, 2026-10-16); now committed as `tests/browser/watchPage.test.js`, run with `bobp make test-browser` (headless Chromium, Jev double, no key): live pause/step/reload/resume, pause while idle then stall, Ctrl-C while paused, replay. The Phase 2 layout finding is a geometry test in `make test` (`tests/turnGraph.test.js`, labels never cover a state or each other) |
| Evidence | outputs posted to `agents/CHAT.md`; screenshot `docs/images/watch.png` (real `examples/mcp` run) |

## 3. Scenario-Driven Acceptance Test Cases

### `UAT-UND13-01`: every log tells the whole story
`bobp make test-live` → five examples `done`; each log's first line is `start`; 10-14 `state`
lines per run (≥1 per step); the CLI example's waits folded into `idle_looks`; step and final
lines keep their sprint 3 fields (test pins the key lists). **PASS**.

### `UAT-UND14-01`: watch a live run
`run examples/mcp --watch` → address on stderr before the first move; in Chromium the highlight
followed each state change within ~50 ms; the feed showed offered options with the pick
highlighted, confidence, MCP arguments (`film=f1, count=2`), the tool's answer; status `done`,
"done after 3 steps". **PASS**. Same for `examples/web` (page target - its own headless browser
alongside) and `examples/http` (`status 200` answers). **PASS**.

### `UAT-UND14-02`: join late, reload, change nothing
Reload after step 1 rebuilt the history and kept following (live). A page joining mid-run sees
exactly the run's lines in order (test). `--watch` stdout equals a plain run's, times aside
(test). **PASS**.

### `UAT-UND15-01`: pause, step, resume
`run examples/http --watch --pause` → stderr `paused - step or resume from the page, or Ctrl-C`;
page `paused before step 1` at `choosing`, Pause off / Step and Resume on; 12 s paused with no
stall; Step ×2 = one move each; all controls off after `done`. No Jev call while paused (test,
250 ms paused against a 60 ms limit). **PASS**.

### `UAT-UND16-01`: replay a finished run
`understudy watch <boxoffice-mcp log>` → address printed; `replay - step 0 of 3`; Step forward
walks `waiting -> looking` on `OBSERVE`; clicking step 2 jumps there (step 3 faded); Step back;
Play runs to "done after 3 steps"; Ctrl-C exit 0. **PASS** after the Phase 5 finding (frames per
line, not per step).

### `UAT-UND17-01`: docs
README opening + screenshot, USER_GUIDE §5 (live, pause/step, replay, SSH), SKETCHES §7 event
lines, troubleshooting rows, command reference, ADR-0014..0016; every documented command gives
the documented line; image links resolve. **PASS**.

## 4. Negative & Error Handling Test Cases

| ID | Scenario | Expected (exit) | Result |
|---|---|---|---|
| `UAT-ERR-01` | `--port` taken | `port N is in use - choose another with --port` (2), judge and app never started (test) | PASS |
| `UAT-ERR-02` | `--pause` / `--port` without `--watch` | `--pause needs --watch (...)` / `--port needs --watch (...)` (2) | PASS |
| `UAT-ERR-03` | bad `--port 99999` | `--port must be a port number from 1 to 65535` (2) | PASS |
| `UAT-ERR-04` | Ctrl-C while paused | page + log `interrupted: stopped by Ctrl-C while paused, after 0 steps`, no move, exit 1 | PASS |
| `UAT-ERR-05` | replay a log with no start line | `no start line - replay needs a log written by understudy run (sprint 4 or later)` (2) | PASS |
| `UAT-ERR-06` | replay a non-JSON file | `line 1 is not JSON - this is not a run log` (2) | PASS |
| `UAT-ERR-07` | replay a log cut short | last frame says `log ends without a final line (the run was killed?)` (test) | PASS |
| `UAT-ERR-08` | wrong token / other path | 404; only the page's files served (test) | PASS |
| `UAT-ERR-09` | control in replay | 409 (test) | PASS |

## 5. Defect Summary & Gate Outcome

| Defect ID | Severity | Description | Assignee | Status |
|---|---|---|---|---|
| `DEF-10` | Minor | statechart labels squeezed under boxes; back-edge labels collided (Phase 2 visual check) | Neo | Resolved (7e878cb) |
| `DEF-11` | Major | replay frames per step always showed `waiting`; state changes not walkable | Neo | Resolved (26e6b03) |
| `DEF-12` | Minor | a failed run's ending read `stalled: stalled: ...` (outcome prefixed to a message that has it) | Neo | Resolved at close; retested by replaying the stalled log |

### `UAT-SMITH-01`: pause a running run while the app is idle, then watch it fail (end to end)
`examples/web` copied without its `showing` end, `run --watch`: after step 3 (app idle, nothing
to press) clicked **Pause** → `paused before step 4`; 13 s paused, not stalled; **Resume** →
`stalled` exactly 10 s later, exit 1; page: status `ended: stalled` in red, the full reason under
the decisions (after DEF-12: said once), controls off; `finished` drawn apart (nothing reaches
it). **PASS**.

**Gate outcome**: PASSED - Smith approved. rubric UAT: COVER=S STEPS=A FAIL=S DATA=A EVID=S.
