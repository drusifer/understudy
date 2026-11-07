# Sprint 32: The beat box (Tier 2: story and architecture in one)

* **Branch**: `sprint-32` (cut from `sprint-31`, which is committed and not yet merged). **Source**: owner, 2026-11-06, decision 45 ("what is the beat tube meant to show", "put something useful there", "consolidate", "show that iteration's data, not the whole list", "a compact bar chart, pie chart or gauge").
* **Owner rules**: no back-compat, Edit/Write only, American spelling, pyramid tests (unit first, browser for what only a browser shows).
* **Mechanism approval**: none (no dependency, route or make target). **Size**: about 14 points, three phases.

## Goal

Replace the beat tube with a **beat box**: for the beat the run is on (or the one you clicked on the diagram), a picture of what goes **in** and what comes **out**, as small charts, and for a beat that runs once per row, **that row's own data** with a stepper through the rows. The scattered expandable panels (step view, decisions, Jev reads, run summary) fold into the box and one run header.

## What exists and what it becomes

| Today | Becomes |
|---|---|
| BEAT TUBE: lamps of started beats and "n of m done" counts | gone (the diagram shows state; the box shows the beat) |
| STEP view (text list under the diagram) | the beat box |
| DECISIONS expander (text, per blend row and dimension) | the box shows the beat's decisions as weight bars |
| JEV READS expander (text) | the box shows each Jev answer as probability bars; the JEV gauges stay |
| SUMMARY list (mode, stale, took, with, wrote, outcome) | one compact run header line above the box |
| Spending card, gauges, printer, diagram | unchanged |

## Assumptions made for the owner

* **What a chart is made from.** The runner profiles each piece a top-level beat read, made or wrote: a **number column** is a gauge (min, mean, max), a **text column** with at most 4 distinct values is a donut, with more it is bars of the 5 commonest values; at most 6 columns per piece, the most informative first (numbers, then short text). Values are cut at 40 characters. The log carries these small summaries, not rows.
* **An iteration** is one pass of a beat that calls a play per row (`each`): the runner logs one `iteration` event per pass with the row (its fields as labeled values, long ones cut) and a profile of what the pass made. The box shows the latest pass and a stepper (previous, next, n of N); it does not hold the run between passes (stepping into passes is a later sprint).
* **Jev and blend** beats show their options as bars (a Jev answer's levels and probabilities; a blend decision's option weights, the pick marked).
* **Decision 44 applies:** level names and values are shown as they are.

---

## UND-118: The runner says what flows through a beat
**Points:** 5 · **Owner:** Neo

**As** the beat box,
**I want** each beat's completion and each pass of a repeated beat to carry small summaries of its data,
**so that** I can draw it without reading files.

### Acceptance Criteria
1. `profile(rows)` (`src/play/profile.py`) returns per column its `kind` (`number`, `text` or `other`), `rows` counted, and for a number `min`, `mean`, `max`; for text `distinct` and the commonest 5 `top` values with counts; at most 6 columns, values cut at 40 characters; an empty list gives no columns.
2. A top-level `beat_completed` carries `columns` inside each `read`, `made` and `wrote` piece; a beat inside a called play carries none (shape only, as now).
3. `_run_each` emits one `iteration` event per pass: `beat`, `index`, `of`, `item` (the row's fields, values cut) and `made` (rows and a profile of what the pass wrote).
4. `jev_read` carries `levels` (up to 8 `[name, probability]` pairs, names cut at 60 characters).
5. The household replay's outputs stay byte-identical to the baseline; the log's size growth is reported.

## UND-119: The beat box
**Points:** 6 · **Owner:** Neo, with Trin

**As** the owner watching or stepping a run,
**I want** a box showing what goes into and comes out of the beat I am looking at,
**so that** I understand what the beat did without reading text lists.

### Acceptance Criteria
1. The BEAT TUBE and the step view are replaced by one **BEAT BOX** in the diagram column's place (below the diagram), following the beat the run is on, or the one clicked on the diagram (click again to follow the run).
2. The box shows the beat's name, action and status (not run yet, running, held, done, failed), then three zones, IN, the beat, OUT: each input and output piece is a card with its name, row count and up to three small charts (gauge, donut, bars) from its profile; a beat with no data says so in a line.
3. A beat that ran once per row shows the iteration chosen by a stepper (previous, next, `n of N`, latest by default while the run goes): the row's labeled values under IN and what that pass made under OUT.
4. A Jev beat shows each answer as horizontal probability bars (the top one marked, `UNSURE` below 0.7); a blend beat shows each decision's option weights as bars with the pick marked.
5. Every chart has a text equivalent (an accessible name and a `title`), keyboard use works on the stepper, and the box reads in the three themes (contrast test) and at the widths of Sprint 30.
6. In a replay the box shows the beat as it was at event N.

## UND-120: One place for the run's details
**Points:** 3 · **Owner:** Neo

**As** the owner,
**I want** the scattered expandable text folded away,
**so that** the page has the diagram, the box, the log and a run header, and nothing hides in an expander.

### Acceptance Criteria
1. The DECISIONS and JEV READS expanders and the SUMMARY list are gone; one run header line says mode, how it ended, how long, files written and, if stale, that the replay is stale.
2. The JEV, SURE and ASKED gauges keep their figures (computed as now); the spending card is unchanged.
3. The docs (USER_GUIDE, PLAYS) describe the box and the header; no dead script or style is left for the removed panels.

---

## Architecture

* **Profile in the runner, not the page.** `profile.py` is a small pure function (the standard library only); `shape()` in `run.py` gains `columns` when the beat is top-level (`_stages(..., profiled=True)`), so nested passes stay light. `record.detail` and the events carry the result; the server's `step_details` (view.py) already passes `read`/`made`/`wrote` through, and gains `iterations` (the `iteration` events by beat) and `jev` (the `jev_read` events by source) and `decisions` by beat from the log, so the replay works with the same code.
* **The box is drawn from `run.steps`** (per beat: `action`, `read`, `made`, `wrote`, `iterations`, `jev`, `decisions`) plus the plan's reads for a beat not yet run. New file `src/dashboard/box.js` holds the box and the chart drawing (SVG built with `svgEl`, text only through `textContent`); `page.js` loses the tube, step view, Jev and decisions drawing (`decisions.js` shrinks to the replay-jump it still needs, or goes).
* **Charts:** `gauge` (a bar with min and max labels and a mean tick), `donut` (up to 4 slices with a legend), `bars` (up to 5, value labels). One function each, no library.
* **Failure modes:** a beat with no profile (an older log, or a nested beat) shows its name and row counts only; a profile with no usable columns shows "no columns to chart".
* **Security:** the log carries values from the owner's data (decision 44) in cut, summarized form; the page writes text through `textContent` only. A quick pass plus a check that the log still carries no more than the profiles and the iteration's row.

## Phases

1. **UND-118** (backend, tests first, byte-identical proof).
2. **UND-119** (the box, charts, stepper; browser tests).
3. **UND-120** (fold the expanders; docs; closeout).

## Out of Scope

Holding the run between passes, editing values, a chart library, changing what a play writes.
