# UAT Plan: Sprint 26, see and drive the machine

- **Stories / criteria:** UND-83 to UND-85 in `docs/sprints/USER_STORIES_SPRINT26.md`
- **Environment and build:** branch `sprint-26`, local CLI and console; a real household sketch with the fixture exports, the full household run (`run-20261103T223303-93eea554`, 5,027 events), the coffee week run in replay mode (`run-20261104T004414-cde56cea`, 11 decisions), and a real Chromium (`bobp make test-browser`)
- **Date / tester:** 2026-11-03, Trin (Smith for the end-to-end pass)
- **Entry conditions:** unit tests green; Chromium present
- **Exit conditions:** every acceptance criterion passes; unresolved issues listed

## Scenarios

### UAT-26-1: Hold and step the runner (Phase 1)

- **Linked criterion:** UND-83 AC3 to AC5
- **Preconditions and data:** the household sketch on the fixture exports, started held by `run_sketch(pause=True)`; a driver outside the run writes `control.json`
- **Steps:** step once per `paused` event until the run finishes; separately try a bad control file and an ordinary run
- **Expected observable outcome:** exactly one top-level stage per step; `paused` is logged before `stage_started`; a bad file lets the run go on; an ordinary run has no `paused` events
- **Actual outcome:** 16 steps, 16 `paused` and 16 `resumed` events, run finished complete; the other cases as expected
- **Verdict:** PASS
- **Evidence / issue:** chat message "UAT phase 1 passed". A first attempt hung because the driver counted nested stage events as top-level ones (a fault in the driver, not the runner).

### UAT-26-2: Drive a run from the console and the command line (Phase 2)

- **Linked criterion:** UND-83 AC1, AC2, AC4, AC6
- **Preconditions and data:** `understudy run --watch --pause` on a test sketch; the console's HTTP routes; Chromium
- **Steps:** step and resume through the routes; try a run the console did not start, no secret, another origin, `--pause` alone and a busy port; unlock in the page and press the buttons
- **Expected observable outcome:** one move per step; a foreign run refused 404; 401/403 without the secret or from another site; one-line refusals with exit 2; the page reads PAUSED with "paused before `<stage>`", the buttons locked until unlocked and enabled only where they apply
- **Actual outcome:** as expected. Switch's full review found one defect: `--watch` saved its secret in the dashboard's secret file and would have locked a running dashboard's owner out; it now uses `.understudy/watch.secret`.
- **Verdict:** PASS
- **Evidence / issue:** chat messages "UAT phase 2 passed", "security gate (phase 2)"

### UAT-26-3: The run as it was (Phase 3)

- **Linked criterion:** UND-84 AC1, AC3, AC4
- **Preconditions and data:** the coffee week run and the 5,027-event household run
- **Steps:** replay event 1, the middle and the last event; compare the last with the live view; corrupt one line
- **Expected observable outcome:** the last event equals the live view; a corrupt log is refused naming the line
- **Actual outcome:** equal in state, ending, diagram, stages, gauges and lines for both runs; a step on the large log takes 0.03 s; `events.jsonl line 4 is not readable`
- **Verdict:** PASS
- **Evidence / issue:** chat message "UAT phase 3 passed"

### UAT-26-4: Play it back (Phase 4)

- **Linked criterion:** UND-84 AC1, AC2, AC5
- **Preconditions and data:** a finished run in a real Chromium, all three themes in light and dark, a 390 px phone
- **Steps:** open the bar; step, step back, scrub, play to the end, pause, go back to live; open a corrupt log; open a run that is still going
- **Expected observable outcome:** the page follows the cursor; the bar is readable, reachable by keyboard and fits a phone; a corrupt log and a running run are refused plainly
- **Actual outcome:** as expected. A browser test found a real fault: a frame requested before PAUSE could land afterwards; fixed.
- **Verdict:** PASS
- **Evidence / issue:** `bobp make test-browser` 39 of 39

### UAT-26-5: See the decision (Phase 5)

- **Linked criterion:** UND-85 AC1 to AC4
- **Preconditions and data:** the coffee week run (replay mode, 11 decisions); browser fixtures with removed and held options, a missing field and markup in the names
- **Steps:** list the decisions and open them; jump to a decision in a replay from the list and from the printed line; open a run with none
- **Expected observable outcome:** each decision shows its options, weights, what removed or held them and the pick; a jump lands on the decision's event; markup is shown as text
- **Actual outcome:** all 11 coffee decisions land on the event the list gives; the rest as expected in the browser tests
- **Verdict:** PASS
- **Evidence / issue:** this fixture removes no options, so the removed-by and shortlist wording is verified by tests only. The story asked for each decider's weight; the log records only the blended weight, so only that is shown (user guide says so).

## Results and Handoff

- **Passed / failed / blocked:** 5 passed (UAT-26-1 to UAT-26-5); 0 failed, 0 blocked
- **Open issues and impact:** (1) the gate is slow and growing (about 96 s of unit tests, 106 to 153 s of browser tests); owner decision 17 says to move checks down the test pyramid, scheduled for the next sprint. (2) The combined `bobp make check` was not re-run after the last lint fix (line length), at the owner's instruction; the unit tests had passed in the run before it and `bobp make push` runs the full gate before anything leaves the machine.
- **Overall verdict:** PASS
