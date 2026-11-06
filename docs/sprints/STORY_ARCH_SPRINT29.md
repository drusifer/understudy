# Sprint 29: See the whole play, and step through it (Tier 2: story and architecture in one)

* **Branch**: `sprint-29` (cut from `main` 158edd4)
* **Source**: owner, decision 39 (Sprint 28 retro) and decision 43 (2026-11-05, asked as a multiple choice; the owner picked both parts).
* **Owner rules**: no back-compat, YAGNI, DRY, use libraries, Edit/Write only for edits, American spelling, run only the tests that changed while building (the unit suite once per phase, the browser suite once at the end).
* **Mechanism approval**: none needed (no new dependency, language, tool or make target).
* **Size**: about 18 points. **Status**: Draft for Smith's gate.

## Goal

The console draws the **whole play**, not only the scene's flow: the stage's pieces, the beats, and which beats read which pieces. A person can open a play, **hold it before its first beat** (or at a beat they pick), and **step** from beat to beat, seeing at each step what the beat read and what it wrote.

## What exists (so nothing is built twice)

* The scene chart (`src/dashboard/chart.py`, ADR-0054) lays out the flow beats from the first line of a run's events (`run_started.beats`, `.transitions`) and lights the current beat. It draws no pieces and no beat performed when read.
* PAUSE, STEP and RESUME (ADR-0058) work on a run that is going: `control.json` holds the runner before its next flow beat. A run can already start held (`run_sketch(pause=True)`), but the console does not offer it, and a hold stops only at flow beats, in order.
* The replay bar steps through a finished run's events (`replay.js`).

## Assumptions made for the owner

* **The plan diagram comes from the play file, not from a run.** The console can draw a play before any run exists (so you can look at it, and choose where to hold). A run then lights it up from its events, as the chart does today.
* **A beat performed when read (no `to:`)** is drawn as a beat hanging off the beats that read it, with a dashed outline, so the diagram tells the flow apart from the beats that wait to be read (ADR-0061).
* **Hold-at-beat means "hold before beat X starts".** Any flow beat can be chosen. A beat performed when read cannot be held at on its own (it runs inside the beat that reads it); stepping shows it in the step of that reader.
* **Pieces shown at a step are summaries, not data dumps**: file name, row count, and the first few rows' keys, never the rows themselves (the console must not show private household data to anything but the person at the page; the page is already local and secret-guarded, but a full dump of 2,000 records is not a step view).
* **The old pause/step/resume controls stay as they are**; hold-at-beat adds to the same `control.json` rather than a second mechanism.

---

## UND-111: The whole-play diagram
**Points:** 6 · **Owner:** Neo

**As** the owner reading a play I did not write today,
**I want** to see its stage pieces, its beats and the arrows between them in one picture,
**so that** I can tell what feeds what without reading the YAML.

### Acceptance Criteria
1. `GET /api/plan?play=<file>` returns the layout of one listed play: nodes for each read piece, write piece, flow beat and beat performed when read; arrows for each `to:`/`transitions:` move (as the chart draws them), each "beat reads piece or beat" (`from:`, a `with:` reference, a Jev beat's state), and each `write` beat to its write piece. The play must be one the launcher lists; any other name is refused 403, as a start is.
2. The page shows it in the chart's place for a play that is chosen and not running, and for a run it shows the same picture with the current beat and the moves taken lit, as the chart does today. The old chart code is replaced by this one (no second chart).
3. A piece is drawn differently from a beat (a rounded tag against a box), a write piece differently from a read piece, a beat performed when read has a dashed outline, a final beat keeps its double border. Each node has a text label and an accessible name.
4. The household play draws without arrows running through boxes (the layout rule of ADR-0054 holds for the new nodes), and a play with no flow (only a stage) says so in one line.
5. The picture for a play with many beats scrolls inside its box, as the chart does.

## UND-112: Start a play held, and hold at a beat
**Points:** 6 · **Owner:** Neo

**As** the owner learning what a play does,
**I want** to start it held before its first beat, or held before a beat I pick on the diagram,
**so that** I watch it one beat at a time from the start instead of racing it.

### Acceptance Criteria
1. The page offers START HELD next to PLAY. The run starts with `control.json` already `hold` and 0 steps, so the first beat waits (event `paused`, naming the first beat); STEP lets one beat through; RESUME lets the rest run.
2. Clicking a flow beat on the diagram while a play is chosen sets "hold before this beat" for the next start (shown on the diagram and in the controls, and cleared by clicking again or by starting). The run goes at full speed up to that beat, then holds there with `paused` naming it.
3. `POST /api/runs` takes the hold choice (`hold: true` or `hold_at: <beat name>`); a name that is not a flow beat of the play is refused 400 naming the beats there are. Both need the console's secret like every other control.
4. The runner holds before a flow beat by name through the existing `Hold` gate (extended with the stop-at beat), not by a second wait loop. A run with no choice behaves exactly as now.
5. A held start on a replay, and a start refused as already running, behave as they do now.

## UND-113: See what each step read and wrote
**Points:** 6 · **Owner:** Neo, with Trin

**As** the owner stepping through a play,
**I want** each beat's step to show the pieces it read and wrote,
**so that** I understand the beat, not only that it ran.

### Acceptance Criteria
1. Every beat's completion event (`beat_completed`) carries `read` (the pieces and beats it read, by name, with their row counts) and `wrote` (the pieces it wrote, with row counts), and the beat that reads a beat performed when read lists it. `docs/PLAYS.md` documents the fields; the event log gains no row data.
2. The page's step view (below the diagram) shows, for the beat chosen on the diagram or the one a run is held at: the beat's action, its `with`, the pieces read (name, rows) and written (name, rows), and the first few record keys of each (not values).
3. In a replay the step view shows the same for event N, from the log alone (no data files read), and a log written before this sprint shows the beat without the lists, with no error (a missing `read` is not an error; no old-run handling is added).
4. The household's captured baseline stays byte-identical in its outputs (excluding `events.jsonl`), so the new fields change only the log.

---

## Architecture

* **One plan, one picture.** A new `src/play/plan.py` turns a loaded `Play` into a graph: nodes (`piece`, `beat`; flags `write`, `flow`, `final`, `waits`) and edges (`move`, `reads`, `writes`). The reads come from the places a beat names a piece: `with.from`, `with.sources`, a `write` beat's name, a Jev beat's state and options pieces, and a `do: { play }` call's `with:` bindings. The same module is what the runner uses to say what a beat read (UND-113), so the diagram and the log cannot disagree.
* **Layout stays server-side.** `chart.py` takes the plan's graph in place of the machine's states and moves; it gains node kinds and a "reads" edge class. `overlay` keeps its job (the current beat and the moves taken, from events). The page only draws what the server returns, as ADR-0054 says. The old `_story_of` first-line story stays only as the run's own record of the flow, and the page lights the plan with it.
* **Where the plan comes from.** `GET /api/plan?play=<file>` loads the listed play (the launcher's list is the only whitelist; no path comes from the client) and returns the layout. A run page uses the same call for the run's play (the first event names the play file), so a run and a chosen play show one picture.
* **Hold-at-beat.** `Hold` takes an optional `stop_at` beat read from `control.json` (`{"mode": "run", "steps": 0, "stop_at": "name"}`; absent means as now). Before each flow beat the gate holds when the mode is `hold`, or when the beat is `stop_at`; reaching `stop_at` switches to `hold` and clears `stop_at` so STEP works from there. `read_control` keeps refusing anything it does not know, so a bad file still means run. The run folder does not exist until the child makes it, so the launcher cannot write the first `control.json`; the child does, as it does for `--pause` today. `run_sketch(pause=)` gains `stop_at=`, and the CLI gains `--stop-at <beat>` beside `--pause`. Both flags are refused today unless `--watch` is given (a held run needs a console); the launcher's child is run by a console already, so the flags are allowed with `--watch` or `--held-by-console` (one flag the launcher passes, decided at implementation, no new surface for a person).
* **What a beat read.** `StageContext.read(name)` already is the one place pieces are read by name; it records name and row count into the context. `beat_completed` carries what the context recorded, plus the write rows count. No data goes into the log.
* **Step view data.** The page gets the step view from the run's events (live or replay), and from the plan alone before a run (action, `with`, what it would read and write). No new data endpoint.
* **Failure modes.** A play that does not load: the plan endpoint says why in one line (the `check` text). A `stop_at` beat that never runs (the scene takes another branch): the run finishes normally; the page says "never reached" when the run ends with the hold unspent. A name that does not match: refused at start (UND-112 AC3).
* **Security.** New input: the play name in the plan URL (checked against the listed plays, never joined to a path from the client) and `hold_at` (checked against the play's beats). The plan carries names and counts, no rows. Expected: a short design pass and a phase review of the plan endpoint, the `hold_at` check and the event fields.
* **Tests (pyramid, ADR-0060).** Unit: `plan.py` on the coffee and household plays; `chart.py` layout (no arrow through a box, new kinds); `Hold` with `stop_at`; the events' `read`/`wrote`. Server: the plan route (listed, unknown, unloadable) and the `hold_at` refusals. One browser test for what only a browser shows: click a beat to hold, start, watch it stop there, step, and see the step view.
* **Order of work.** UND-111 (plan and chart) first because UND-112 and 113 draw on it; then UND-112 (the runner gate and the start); then UND-113 (the events and the step view). The household baseline in `build/baseline-sprint28/` is the identical-output proof for UND-113.

## Out of Scope

* A play editor, moving nodes by hand, or saving a layout.
* Holding at a beat performed when read, and holding inside a called play's beats.
* Showing data values in the step view (counts and keys only).
* Venmo and Zelle, household cleanup, engine-internal renames (backlog).
