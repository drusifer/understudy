# What the old console did, and where it stands now

*   **By**: Cypher, from `CHANGELOG.md` sprints 4-15, `docs/design/DASHBOARD.md` and the owner's note of 2026-11-01 ("we're missing a bunch of user stories that the old version supported like the diagrams and step by step").
*   **Why this exists**: Sprint 21 rebuilt the console watch-only and deleted the old controls (decision: assumption 1 of `USER_STORIES_SPRINT21.md`). `UX_GAPS_SPRINT22.md` looked at what the new one does badly; this lists what the old one did that the new one **does not do at all**.

## The old features, one by one

| # | Old feature (sprint) | Now | Decision proposed | Story |
|---|---|---|---|---|
| 1 | **Statechart diagram**: states as boxes in layers, finals double-bordered, labelled arrows, the current state lit, the transition just taken highlighted (S4, S6, S14) | gone; a flat list of stage lamps | **Restore**, drawn from the sketch's `machine` | UND-82 |
| 2 | **Step by step**: STEP makes one move then waits; PAUSE holds before the next move; RESUME; STOP; Ctrl-C works while paused; no Jev call while paused (S4, S12) | gone; a run cannot be held | **Restore**, between stages | UND-83 |
| 3 | **Replay a finished run from its log**: play, pause, step through each state change, click a decision to jump to it (S4 `watch <log>`) | gone (`--replay` today re-runs from Jev captures; it does not replay the story) | **Restore** as a timeline over `events.jsonl` | UND-84 |
| 4 | **Decision detail**: every decision's options, the rules that removed or held options, scores, the pick and its confidence, shown line by line; score tables with 1.0 printed as `11` (S4-S6) | gone; the log has only start and done | **Restore** for `decide` stages and Jev reads | UND-85 (rules), UND-78 (Jev) |
| 5 | **The log is the whole story**: `start` (sketch, statechart), a `state` line per transition, an `ended` line with the reason (S4) | `events.jsonl` has five kinds and no state or decision lines | **Prerequisite for 1-4**: a richer event stream | UND-81 |
| 6 | **Edit the sketch in the console**: the printer opens on a latch; the bay behind it holds the whole YAML with a cheat sheet; saved as you type, checked first, refused text says why and is not saved, comments kept, the diagram redraws as you type, read-only while a run plays (S6, S8) | gone | **Restore** the editor and the check; the cheat sheet is rewritten for the new model | UND-86 |
| 7 | **Typed inputs as controls**: a pointer dial for a choice, analog faders for weights (Nixie readout), a stepper for a count, switches for on/off, set before the run, defaults restored by POWER (S6, S7) | the new sketch has `--with name=value` text and no declared kinds | **Owner decides** (question below): the new model has no typed inputs | UND-87 (if wanted) |
| 8 | **Weights' power ring and decision-power bar**: each weight's colour and share, the blended colour on the decision edge (S6, S14) | the new model blends deciders per dimension; nothing shows it | **Replace**: show each decider's weight and the blend in the decision detail, not a ring | inside UND-85 |
| 9 | **Five real gauges**: steps of limit, Jev's confidence, shortlist left, Jev scores asked and reused, idle time (S15) | four gauges (stages, failed, Jev requests, elapsed); no confidence, no asked-vs-reused, no idle | **Restore two** that have data: Jev confidence of the last read, asked vs reused (captures); drop shortlist and idle (no such concept now) | UND-78 |
| 10 | **Rack of sketches in a folder, play and stop from the page** (S6) | rack of runs only | already in Sprint 22 | UND-79 |
| 11 | **`run --watch`**: start a run and have a live page for it at once (S4) | run and dashboard are separate commands | **Restore** as `understudy run --watch`, opening the console on that run | UND-83 |
| 12 | **Access panels** to edit one factor's range, order, question, default (S6) | gone | **Replace** by the YAML editor (row 6); per-factor panels dropped | (none) |
| 13 | **POWER toggle**: dims the console; off then on resets sketches to factory defaults (S6) | removed in Sprint 21 | **Drop** (decorative; "factory defaults" was for the editor, which now has git) | (none) |
| 14 | **JSON Schema for editor help** (S10) | `schema/decision_sketch.schema.json` exists | keep; point the console's editor at it | UND-86 |
| 15 | **Themes, light/dark, mobile, fonts, local only** (S9, S11) | kept | done | (none) |
| 16 | **Play-an-app targets** (process, page, http, mcp) and their live views | deleted by owner decision (one kind of sketch) | stays deleted | (none) |

## Checked against the old story files (added after the owner asked "did you read the user stories?")

The table above was first built from the changelog and the design doc. Reading the acceptance criteria of `USER_STORIES_SPRINT4.md` (UND-13 to 16), `SPRINT6` (UND-27 to 32), `SPRINT8` (UND-35), `SPRINT12` (UND-39), `SPRINT14` (UND-41) and `SPRINT15` (UND-42) confirmed every row and added these details, now written into the stories:

| Old acceptance criterion | Folded into |
|---|---|
| UND-27 AC2: a sketch that fails `check` is listed greyed out with its check message and cannot be played | UND-79 (Sprint 22) |
| UND-27 AC4: a folder with no sketches or a path that is not a folder is refused before anything starts | UND-79, UND-80 |
| UND-27 AC1/5, UND-14 AC1: the old console URL carried a **token** (`/d/<token>/`) and a wrong token was a 404: a precedent for the access control UND-79 needs | UND-79 design (Switch) |
| UND-29 AC3-4: when a run ends the controls unlock and the outcome shows; a run that cannot start (no `TYPESAFE_API_KEY`) says why on the page | UND-79, UND-76 |
| UND-14 AC5: the page says how the run ended (`done after 3 steps`, or the outcome and message) | UND-76 |
| UND-14 AC2: the highlight moves within one second of a state change | UND-82 |
| UND-15 AC3-5: while paused the page says `paused before <stage>` and what is about to run; a paused run is never stopped by a time limit; Ctrl-C stops a paused run at once | UND-83 |
| UND-15 AC6: `--pause` without `--watch` is refused with a message | UND-83 |
| UND-16 AC2-4: replay has **step back** as well as forward, replays the whole log including its ending, and refuses a log it cannot read | UND-84 |
| UND-28 AC5, UND-39 AC5: every control reachable by keyboard with an accessible name and value | UND-80, every new control |
| UND-31 AC3: the printer can be scrolled back and the newest line stays visible | already kept |
| UND-35 AC4: the editor is read-only while a run plays, and Play uses the saved file | UND-86 |
| UND-39 AC1: STEP from idle starts the run and makes exactly one move | UND-83 |

## Re-planning

The old features need information the new event stream does not carry, so the order changes:

* **Sprint 22** (drafted, 29 pts): trust the console, see inside a run, Jev panel, start runs, CLI contract. Unchanged except UND-78 also takes the two restored gauges.
* **Sprint 23, "the machine you can see and drive"** (about 31 pts): UND-81 event stream v2 (5), UND-82 statechart diagram (8), UND-83 pause, step, resume, stop and `run --watch` (8), UND-84 replay a finished run from its log (5), UND-85 decision detail (5).
* **Sprint 24, "edit and tune in the console"** (about 8-16 pts): UND-86 YAML editor with check (8), and UND-87 typed inputs (8) only if the owner wants them.

## Stories (to be refined at Sprint 23 planning; Smith's Gate 1 then)

**UND-81 The run tells its story** (5). The event stream gains `machine` (the states and events at start), `state_entered` (state, event that caused it), `decision` (stage, options, what removed or held each, weights, the blend, the pick) and `jev_read` (question, options, probabilities, choice, from capture or live), and the `run_finished` line says why a failed run stopped. Old consumers lose nothing; unknown kinds still print. Tests use a Jev double and compare lines.

**UND-82 See the statechart** (8). The console draws the sketch's machine as a layered flow: states as boxes from the initial one downward, finals double-bordered, arrows labelled with their event; the current state is lit while a run goes and the transition just taken is highlighted; a finished run shows its path. Clicking a state scrolls the printer to its lines. Layout is computed in Python or by a vendored browser library; no Node build.

**UND-83 Hold and step a run** (8). Pause holds before the next stage; Step lets one stage through and waits; Resume; Stop. Nothing asks Jev while paused. Ctrl-C stops a paused run at once. `understudy run --watch [--pause]` starts the run and opens the console on it. Needs Switch's gate with UND-79 (same control channel).

**UND-84 Replay a story** (5). Choose a finished run and play its events back with play, pause, step and a scrubber; the diagram, printer and gauges follow the cursor; clicking a printed decision jumps to it. Works offline from `events.jsonl` alone.

**UND-85 See the decision** (5). For a `decide` stage: the options, each rule that removed or held one with its reason, each decider's weight, the blended result and the pick; a score of 1.0 may print as `11` (owner's old convention, kept only if the owner still wants it).

**UND-86 Edit the sketch** (8). The printer's latch opens the sketch's YAML with a cheat sheet for the new model; text is checked as you type and saved only if it passes, with the problem shown otherwise; comments and layout are kept; the diagram redraws; read-only while a run is going; editing is behind the same access token as starting runs.

**UND-87 Typed inputs** (8, only if wanted). A sketch declares inputs with a kind (`choose`, `weight` range, `count`, `switch`) and a default; the console shows a dial, fader, stepper or switch for each and passes them as `--with`. Needs a model change (a `inputs:` block, schema, check, docs).

## Question for the owner

Do you still want **typed inputs** (the dial, faders, stepper and switches) in the new model, or are plain `--with name=value` boxes enough? It is the one old feature that needs the sketch model itself to change. (Everything else above only needs a richer event stream and the console.)
