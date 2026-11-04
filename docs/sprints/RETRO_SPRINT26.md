# Sprint 26 Retro: see and drive the machine

Delivered: UND-83 hold, step and resume a run (control file, `paused`/`resumed` events, PAUSE/STEP/RESUME, `run --watch [--pause]`), UND-84 replay a finished run (a replay computed in Python, a bar with play, step, step back and a scrubber), UND-85 see the decision (a DECISIONS panel, decision lines in the log, jump to a decision in a replay). Five phases, all gates passed; 545 unit tests, 39 browser tests.

## What went well

* **Each part is small and tested at the right level:** the control file, `replay()` and `decisions()` are plain Python functions with unit tests; the page only draws their answers.
* **Real-file checks again found real faults:** a late frame after PAUSE (a browser test), and `--watch` overwriting the dashboard's secret (Switch's full Phase 2 review).
* **The replay equals the live view** at the last event on a real 5,027-event run, and a step takes 0.03 s.

## What went wrong

* **The gate got slow and I ran it too often:** about eight full gates and three browser runs in one sprint, and a `;`-chained command that hid a lint failure behind an older "OK". The log timestamps show the unit tests are 94 of 96 seconds and the household tests about 60% of that. The owner's direction (decision 17): move checks down the test pyramid.
* **Edit-only slipped twice more** (Neo): a no-op `sed` and a `sed` on a scratch script.
* **The story asked for each decider's weight**, which the log does not record; only the blended weight is shown (noted in the user guide). It should have been checked against the log's shape at Gate 1.

## By persona

* **Neo:** tests first held; lint friction (argument counts, long lines, magic values) cost several reruns. **Trin:** UAT on real runs each phase. **Switch:** a full review of the new control channel paid for itself. **Morpheus:** ADR-0058 and ADR-0059. **Oracle:** two lessons. **Mouse:** five phases of 2 to 5 points, sized right. **Cypher/Smith:** AC4 of UND-83 (paused, not stalled) was the right catch.

## Backlog (feeds `docs/BACKLOG.md`)

* **Sprint 27 candidate, owner decision 17: bring the test pyramid back.** Audit by measured per-test time; keep two or three full-sketch end-to-end tests for the household and move the rest down to stage-level and fragment tests (about 53 whole-sketch runs across six files today, 15 files run a whole sketch through `main`); trim the 39 browser tests to what only a browser can show (timing, drawing, keyboard, contrast); then reorder the gate cheap-first (Tank). (Neo, Trin, Tank)
* The decision log does not record each decider's weight; add it if the owner wants it (story UND-85 AC1). (Morpheus)
* Replay resends every printed line each step; send only the new ones if logs pass about 100,000 events. (Neo)
* The page says "pausing" only in a message while a long stage finishes; show it in the status. (Smith)
* Earlier backlog: YAML editor, Venmo and Zelle, pin the own-account merchants and work down `review.jsonl`, make the Monarch `Category` optional, write `open_balance` 0 when none. (Cypher, Owner)
