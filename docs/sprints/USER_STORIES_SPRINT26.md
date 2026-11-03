# Sprint 26 User Stories: see and drive the machine

*   **Planning Size** (optional): 18 points
*   **Branch**: `sprint-26` (cut from `main`, which has Sprints 24 and 25)
*   **Source**: Owner, 2026-11-03 (`OWNER_DECISIONS_SPRINT22.md` 16: pause and step a run, replay a finished run's story, and see each Jev decision in detail); `OLD_VERSION_PARITY.md` rows 2, 3, 4 and 11 and the old criteria folded into UND-83 to UND-85
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

When this sprint is done, the owner can hold a run before its next stage, let it make one move at a time and resume it, from the console or from `understudy run --watch --pause`; can replay a finished run's story with play, pause, step, step back and a scrubber; and can open any decision to see its options, the rules that removed or held them, the weights, the blend and the pick.

**Order.** UND-83 first (the run must be holdable before anything is watched live). UND-84 reads the same event story as UND-83 writes. UND-85 builds on UND-84's cursor (clicking a decision jumps to it).

## Assumptions made for the owner

1. A run is held **between** stages, never inside one: a stage that is already running (including its Jev requests) finishes first. "Nothing asks Jev while paused" holds because Jev is only asked inside stages.
2. The console already starts and stops runs it launched (Sprint 22). Pause, step and resume work the same way: only on runs this console started, with the same secret and same-origin checks. A run started from a terminal is held with `--pause` and driven from the console it opens with `--watch`.
3. Held state is written to the run's event story (`paused` and `resumed` lines), so replay shows when a run was held.
4. Replay works from `events.jsonl` alone, offline; a run's printed lines, stage list, gauges and diagram at a point in time are computed in Python from the events up to that point (ADR-0054: logic in Python, the page draws it).
5. The old "score of 1.0 may print as `11`" convention is **not** restored (the owner has not asked for it); scores print as numbers.
6. Not in this sprint: Venmo and Zelle, the YAML editor, household cleanup.

---

## STORY-UND-83: Hold and step a run
**Points:** 8

**As the** owner,
**I want** to hold a run before its next stage, let it make one move, and resume it,
**so that** I can watch a run decide step by step without Jev being asked in between.

### Acceptance Criteria
1. `understudy run <sketch> --watch` starts a console on 127.0.0.1 for that run and prints its address; `--pause` starts the run held before its first stage. `--pause` without `--watch` is refused with a message, before anything starts.
2. The console shows PAUSE, STEP, RESUME and STOP for a running run it started. PAUSE holds the run before the next stage (the stage in flight finishes first); the page says `paused before <stage>` and names what is about to run.
3. STEP lets exactly one stage through, then holds again; RESUME runs on; STOP ends the run as today. STEP from a run held at the start makes exactly one move.
4. While held, no Jev request is made and no stage starts; a held run is never ended by a time limit (it reads as paused, not stalled), and Ctrl-C on a held run stops it at once.
5. Each hold and release is written to `events.jsonl` (`paused` with the stage about to run, `resumed`), and a log without them still reads as before.
6. PAUSE, STEP, RESUME and STOP are reachable by keyboard with accessible names, and need the same secret and same-origin request as START and STOP; a run this console did not start is refused with a plain message.

---

## STORY-UND-84: Replay a story
**Points:** 5

**As the** owner,
**I want** to play a finished run's events back with play, pause, step, step back and a scrubber,
**so that** I can see how it went without running it again.

### Acceptance Criteria
1. Choosing a finished (or stopped, or failed) run offers REPLAY; the page then shows the run as it was after event N: the diagram with that state lit, the stage list, the gauges and the printed lines up to N.
2. PLAY advances automatically, PAUSE holds, STEP and STEP BACK move one event, and a scrubber jumps to any event; the position is shown as "event N of M".
3. Replay includes the run's ending (how it ended) and any hold; it reads `events.jsonl` alone and makes no Jev request and no change to the run.
4. A log that cannot be read (a line that is not JSON, or no events) is refused with one plain line naming the problem; a log written before Sprint 23 replays what it has.
5. Every replay control is reachable by keyboard with an accessible name and value.

---

## STORY-UND-85: See the decision
**Points:** 5

**As the** owner,
**I want** to open a decision and see its options, what removed or held them, the weights and the pick,
**so that** I can tell why the run chose what it chose.

### Acceptance Criteria
1. A run with `decision` events lists them in the console (stage, dimension, pick); opening one shows each option with its final weight, the rule that removed it or the shortlist that held it (`removed_by`), the blend, and the pick with its probability.
2. In a replay, clicking a decision (in the list or in the printed lines) moves the cursor to that event.
3. A run with no decisions says so; a decision whose log line is incomplete shows what it has and says what is missing, never an error page.
4. Names from a sketch or a log are shown as text, never as markup.

---

## Out of scope

* The YAML editor (UND-86), Venmo and Zelle, household cleanup (owner, decision 16).
* Holding a stage in flight, or pausing a run from another computer.
* Stepping through the rows inside a stage.
