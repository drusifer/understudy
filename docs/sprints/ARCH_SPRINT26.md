# Architecture Document: Sprint 26, see and drive the machine

*   **Status**: Draft — awaiting Smith Gate 2
*   **Author**: Morpheus
*   **Last Updated**: 2026-11-03
*   **Scope**: Sprint 26 Architecture (stories: `USER_STORIES_SPRINT26.md`; decision: `OWNER_DECISIONS_SPRINT22.md` 16)

---

## 1. Executive Summary & System Overview

The console can start, replay-from-captures and stop runs, and draws a run's statechart and stages, but it cannot hold a run, cannot play a finished run's story back, and shows no decision in detail (`decision` events are written since Sprint 23 and nothing reads them). This sprint adds three things, all reading or writing the run folder:

1. **A control file** the runner checks before each top-level stage (hold, step, resume), with `paused` and `resumed` events.
2. **A replay cursor**: Python computes the run as it was after event N from `events.jsonl`; the page draws it with play, pause, step, step back and a scrubber.
3. **A decision view**: Python lists a run's `decision` events and shows one in full; in a replay, selecting one moves the cursor.

No new dependency, language or make target.

## 2. System Context & Boundaries

* **In:** the owner at the console (browser); the runner process; the run folder (`.understudy/runs/run-*/`, git-ignored).
* **Boundary:** the console process writes `control.json` into a run folder it has authority over; the runner process reads it. They share only the file (ADR-0044 pattern: processes talk through the run folder).
* **Out of scope:** the YAML editor, holding a stage in flight, remote control.

## 3. Component & Container Architecture

### Component Inventory

| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `src/sketch/control.py` (new) | The control file: `read_control(dir)` and `write_control(dir, ...)` (atomic replace); `Hold`, the runner's gate: `await hold.before(stage)` waits while held | run folder, clock | `paused` / `resumed` events |
| `src/sketch/run.py` | Calls the gate before each top-level stage; `--pause` writes the first hold | stage names | events |
| `src/sketch/cli.py` | `run --watch [--pause]`: starts the console on 127.0.0.1 in a thread for that run, prints its address; refuses `--pause` alone | args | console + run |
| `src/dashboard/runs.py` | `Launcher.control(run, action)`: hold, step, resume for a run it started (or the `--watch` run) | run id, action | `control.json` |
| `src/dashboard/server.py` | `POST /api/pause`, `/api/step`, `/api/resume` (same secret, same-origin, small body as start and stop); `GET /api/runs/<id>/replay?at=N`, `/api/runs/<id>/decisions` | request | JSON |
| `src/dashboard/replay.py` (new) | `replay(dir, at)`: the run after event N (state, stages, gauges, printed lines, lit state, hold, ending) from the events alone; `decisions(dir)` | run folder | dicts |
| `src/dashboard/view.py` | state `paused` (last event `paused`, not resumed) instead of `stalled` | events | state |
| `src/dashboard/page.js`, `controls.js`, CSS | pause, step, resume buttons; replay bar (play, pause, step, step back, scrubber, "event N of M"); decision list and panel | JSON | DOM (text only) |

## 4. Runtime Interaction & Critical Flows

1. **Hold:** the owner presses PAUSE → `POST /api/pause {run}` → console checks the secret and that it may control the run → writes `control.json` `{"mode": "hold", "steps": <unchanged>}`. Before the next top-level stage the runner reads it, emits `paused {stage}` once, and waits (0.2 s polls) until the mode is `run` or `steps` exceeds the steps it has used. A stage in flight finishes first.
2. **Step:** `POST /api/step` raises `steps` by one (the count only ever grows, so a resume then a pause never replays old steps); the runner lets exactly that many stages through, emitting `resumed` on release and `paused` again before the next. Step from a run started with `--pause` therefore makes exactly one move.
3. **Resume:** mode `run`.
4. **Start held:** `run --pause` writes `control.json` hold before the first stage, so there is no race with the first stage.
5. **Replay:** the page asks `/api/runs/<id>/replay` for the count, then `?at=N`; Python reads the events (capped as today), cuts at N and derives everything with the same functions as the live view (`stage_tree`, `gauges_of`, `printed`, the chart's lit state). Play is a timer in the page that asks for N+1.
6. **Decision:** `/api/runs/<id>/decisions` returns each `decision` event with its index; the page shows options (weight, `removed_by`), the blend and the pick as text. In a replay, selecting one sets the cursor to that index.

## 5. Interface & Contract Specifications

* **`control.json`** (in the run folder): `{"mode": "run" | "hold", "steps": <int ≥ 0>}`. Absent, unreadable, over 1 KiB or malformed means `run` (a bad file never wedges a run). Written by the console only, atomically.
* **New events:** `paused` `{stage}` (the stage about to run), `resumed` `{stage}`. A log without them reads as before.
* **POST** `/api/pause`, `/api/step`, `/api/resume`: body `{"run": "<id>"}` (matches `run-[0-9A-Za-z-]+`); 200 `{"run": id, "mode": ...}`; 404 `that run was not started by this console, or it has finished`; 401/403 as start and stop.
* **GET** `/api/runs/<id>/replay` → `{events: M, ...}`; `?at=N` (0 ≤ N ≤ M) → `{at, of, state, stages, gauges, printed, lit, hold, ended}`; an unreadable log → 422 with one line.
* **GET** `/api/runs/<id>/decisions` → `[{index, stage, dimension, pick, probability, options: [{name, weight, removed_by}]}]`.
* **CLI:** `understudy run <sketch> --watch [--pause]`; `--pause` alone exits 2: `--pause needs --watch`.

## 6. Cross-Cutting Concepts & Resilience

### Failure Modes & Error Handling
| Failure Mode | Trigger / Condition | System Behavior | User / Client Impact | Blast Radius |
|---|---|---|---|---|
| `Bad control file` | Missing, over 1 KiB or not JSON | Treated as `run` | The run goes on | None |
| `Run gone` | Control sent for a finished or foreign run | 404 with a plain message | One line on the page | None |
| `Held and stopped` | STOP or Ctrl-C while held | The wait is interrupted; the run ends as stopped | As today | One run |
| `Held forever` | Owner leaves it held | Reads `paused`, never `stalled`; nothing is lost | Page says paused before `<stage>` | One run |
| `Unreadable log` | Line not JSON, or no events | Replay refused with one line naming it | One line | One view |
| `Decision incomplete` | A `decision` line lacks fields | Shown with what it has and what is missing | Partial detail | One decision |
| `Port busy` | `--watch` cannot bind | Exit 2 with one line | Pick another port | None |

### Security & Privacy
* **Trust boundary:** the control channel is a new way to affect a running process. It is reachable only through the console's POSTs, which require the access secret (constant time), a same-origin request and a body under 8 KiB, as start and stop do (SEC-005, SEC-006). The run id is matched against `run-[0-9A-Za-z-]+` and resolved under the runs root; the control file is written only inside that run's folder.
* **`--watch` binds 127.0.0.1 only**, unlike `dashboard` (all interfaces), because the run it opens has no one else to serve.
* **Sensitive data:** replay and decisions show what `events.jsonl` already holds (names and weights, no row data); text from a log is set as text, never as markup.

## 7. Technical Stack & SDLC / Build Impact

* **Languages & Runtime:** Python 3.12 (standard library `http.server`, `asyncio`, `json`), plain JavaScript and CSS for the page.
* **Build-Environment Check (CRITICAL):**
  * Does this design add a new language, package manager, runtime version, or external tool? **No**
  * All dependencies follow `docs/SDLC.md` change classes; no Tank Phase 0.

## 8. Architectural Decisions (ADRs) & Technical Debt

### Decision Records
* ADR-0058 (to record): a run is held between top-level stages through a control file in its run folder, read by the runner, written only by the console; a bad file means run. Alternatives rejected: a socket or signal (more surface, harder to test, lost on restart); holding inside a stage (would stop Jev mid-request).
* ADR-0059 (to record): replay is computed in Python from `events.jsonl` up to event N with the live view's own functions; the page only draws and times it. Alternatives rejected: replaying in the page (two implementations of the view); storing snapshots (duplicates the log).

### Acknowledged Technical Debt & Trade-offs
* A stage cannot be held in flight; a long stage (a 7-minute Jev categorization) finishes before a pause takes effect. The page says `pausing after <stage>` meanwhile.
* Replay re-derives the view for each event (O(events) per step); fine for the logs seen so far (thousands of events), to revisit if a log passes 100,000 events.
* `run --watch` serves one run; `dashboard` stays the way to watch many.
