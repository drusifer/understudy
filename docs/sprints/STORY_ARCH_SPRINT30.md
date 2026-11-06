# Sprint 30: A console that uses the desktop (Tier 2: story and architecture in one)

* **Branch**: `sprint-30` (cut from `main` bb866aa)
* **Source**: owner, 2026-11-06, on seeing the console at desktop width ("ux is dogshit", "why two diagrams?", "start with the positions, it is okay to go wider"); backlog section "Console UX pass" in `docs/BACKLOG.md`; decision 44.
* **Owner rules**: no back-compat, YAGNI, DRY, Edit/Write only for edits, American spelling, run only the tests that changed while building (unit suite once per phase, browser suite at the end of each phase that touches the page).
* **Mechanism approval**: none (no new dependency, language or make target). **Size**: about 12 points. **Status**: Approved (Smith, Switch design pass: no new input or surface).

## Goal

The console reads well on a desktop screen (1280 to 2560 px wide, and zoomed out) and still works on a phone: **one diagram** that follows what you last chose, a **short run rack**, and a **run view that uses the width** instead of one tall column.

## Assumptions made for the owner

* **One diagram follows the last choice.** Choosing a run tab shows that run (current beat lit, as now). Changing the Play in the START A RUN panel, or pressing SHOW PLAN, shows that play's plan, where clicking a flow beat sets the hold. Starting a run or choosing a tab goes back to a run. The start panel loses its own diagram.
* **The rack shows the newest runs and folds the rest:** per play, the newest 8 runs; the rest behind a "N older" button. Runs the console cannot read ("unreadable", from before Sprint 29) are in one folded group at the end, closed by default.
* **Layout by width:** 1400 px and up, three columns (printer, run readouts, diagram with step view); 1101 to 1399 px, two columns (printer, readouts) with the diagram full width under them; 1100 px and below, one column (readouts, diagram, printer) as now.
* **The printer's paper is as tall as its lines** (up to the window height), not a fixed tall block with the lines at the bottom.
* **Out of scope:** folding or filtering a big play's diagram (backlog); the themes; any change to what a run records.

---

## UND-114: One diagram, following the last choice
**Points:** 4 · **Owner:** Neo

**As** the owner,
**I want** one diagram on the page that shows the run I chose or the play I picked,
**so that** I am never looking at the same picture twice.

### Acceptance Criteria
1. The START A RUN panel has no diagram. The diagram section (`PLAY DIAGRAM`) is the only one.
2. Choosing a run tab shows that run's diagram with its current beat lit and its step view (as today); the title says which run.
3. Changing the Play select, or pressing SHOW PLAN, shows the plan of the picked play in that same place (title `PLAN OF <play>`); clicking a flow beat there sets and clears the hold exactly as before (START HELD, `hold_at`), and the note says so.
4. Starting a run (PLAY or START HELD) shows the new run; the hold choice is cleared.
5. In plan mode the step view describes the clicked or first beat from the plan alone (action, `with`, what it reads), with no "completed" lists.

## UND-115: A short run rack
**Points:** 3 · **Owner:** Neo

**As** the owner,
**I want** the rack to show the newest runs and fold the rest,
**so that** it takes one or two rows, not four.

### Acceptance Criteria
1. Per play the rack shows its newest 8 runs and a button `N older` that shows the rest (and `fewer` to fold them again); the chosen run is always visible even when it is older.
2. Unreadable runs are one group at the end, folded by default, with a count in its button.
3. The rack's tabs and badges look as they do now; keyboard use (Tab, Enter) works on the new buttons.

## UND-116: The run view uses the width
**Points:** 5 · **Owner:** Neo, with Trin

**As** the owner on a desktop,
**I want** the printer, the readouts and the diagram side by side,
**so that** I see a run without scrolling down a tall column.

### Acceptance Criteria
1. At 1400 px and up: three columns, printer | readouts (tube, gauges, summary, spending, decisions, Jev reads) | diagram and step view. At 1101 to 1399 px: printer | readouts, the diagram under both. At 1100 px and below: one column as now.
2. The printer's paper is as tall as its lines, up to the height of the window; a long log scrolls inside it and stays wound to the newest line.
3. No horizontal scrolling of the page at 390, 1280, 1600, 1920 and 2560 px wide, and at 1920 px with the page zoomed to 50 percent (a 3840 px wide layout).
4. A browser test for each width checks AC1 (the columns) and AC3; the existing browser tests still pass.

---

## Architecture

* **State:** the page keeps `state.view` (`run` or `plan`). `choose(id)` sets `run`; the Play select's change and SHOW PLAN set `plan` and fetch `api/plan?play=` (as `drawPlan` does now, moved to `page.js`'s diagram code); PLAY sets `run` through `choose`. `drawChart(run)` and the plan both end in `drawDiagram` and `drawStep`; the plan is passed to them as a run-like object (`chart`, no `steps`, `state: 'plan'`), so the step view needs no second code path.
* **Markup:** the diagram and step view move out of the tube panel into a `section.diagram-panel` that is a sibling of the printer and the tube panel; the start panel's `#plan` section and its CSS go. SHOW PLAN is one button in the start grid.
* **Rack:** `rack()` groups by play, keeps the newest 8 per play (and the chosen run), and renders `N older` and `fewer` buttons; "unreadable" is the group of runs whose state is `unreadable`. The sets that are open are kept in `state.openGroups` (it exists for the stage tree and is reused by name).
* **Layout:** CSS grid areas on `.stage.watch` by width, as in the assumptions; the printer drops its fixed 612 px window and `flex: 1` stretch for `height: auto; max-height: calc(100vh - 230px)`.
* **Tests (pyramid):** the layout is geometry only a browser shows, so the five widths are browser tests (one page each, no new server work); everything else is the existing tests adjusted (the plan tests move from the start panel to the diagram). No server or event change.
* **Failure modes:** a play whose plan cannot be read shows the one-line reason in the diagram's note (as now); a rack with no runs says so (as now).
* **Security:** no new input or route; the page still writes text through `textContent`. Expected: a quick pass.

## Out of Scope

* Folding or filtering a big play (backlog), themes, run-record changes.
