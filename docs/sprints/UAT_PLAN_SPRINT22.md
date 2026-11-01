# UAT Plan: Sprint 22, the console you can trust, see into, and start runs from

- **Stories / criteria:** UND-76, UND-77, UND-88, UND-78, UND-79, UND-80 in [USER_STORIES_SPRINT22.md](USER_STORIES_SPRINT22.md); design in [ARCH_SPRINT22.md](ARCH_SPRINT22.md)
- **Environment and build:** Chromium on the dev machine against `bin/understudy dashboard <folder> --port <n>`; branch `sprint-22`; CPython 3.12.15. Fixtures are invented runs written by the test script under the session scratch folder; the owner's real household run (counts only) is used where a scenario says so. Nothing private is printed.
- **Date / tester:** 2026-11-01 / Trin (phase results are added as each phase passes)
- **Entry conditions:** `bobp make check` green for the phase; the phase's Neo task done and handed off
- **Exit conditions:** every acceptance criterion of the phase passes in a real browser or by a written request check; unresolved issues are listed with an owner

## Scenarios

### UAT-76-1: A finished run says it is done and what it wrote
- **Linked criterion:** UND-76 AC1, AC3, AC4
- **Preconditions and data:** a run folder whose `run.json` says complete with outcome `booked`, `with` `tickets=2`, outputs `booking.jsonl` 1 row, replay mode, `stale` false
- **Steps:** 1. start the console on the folder; 2. open the page; 3. choose the run's tab
- **Expected observable outcome:** header reads DONE with a done lamp; the ended line says `done after 2 stages, outcome booked`; the summary lists outcome, mode replay, stale false, took 9s, `tickets=2`, and `booking.jsonl (1 row)`
- **Actual outcome:** exactly that (after the fix for "1 rows")
- **Verdict:** PASS
- **Evidence / issue:** session run 2026-11-01; found and fixed during the run: "1 rows" plural

### UAT-76-2: A failed run shows why, and the banner takes you to the line
- **Linked criterion:** UND-76 AC1, AC2, AC3
- **Preconditions and data:** a run with `status: failed`, `failed_stage: read`, `error: Jev needs a TypeSafe key`, and a matching `stage_failed` event
- **Steps:** 1. choose the run; 2. read the header and the banner; 3. select the banner
- **Expected observable outcome:** header FAILED with a red lamp; the banner names the stage and reason; the printer scrolls to the failed line; the ended line says the same
- **Actual outcome:** as expected; the summary text was nearly invisible on the light steampunk panel (contrast), fixed by using the theme's text colors, then checked again
- **Verdict:** PASS
- **Evidence / issue:** screenshot `p1-failed.png` (before the contrast fix)

### UAT-76-3: A run that stopped answering reads as stalled, with a sensible time
- **Linked criterion:** UND-76 AC1
- **Preconditions and data:** a run with status `running` whose last event is from 2020
- **Steps:** choose the run
- **Expected observable outcome:** header STALLED; a warning banner; the time in days, not a count of minutes
- **Actual outcome:** first "3595242 minutes", fixed to "2496 days"
- **Verdict:** PASS after fix
- **Evidence / issue:** session run; unit test `test_a_stalled_run_says_how_long_in_a_sensible_unit`

### UAT-76-4: A run with no readable files does not break the page (rejection path)
- **Linked criterion:** UND-76 AC7
- **Preconditions and data:** an empty run folder named like a run
- **Steps:** open the page; choose that tab; choose another tab
- **Expected observable outcome:** the tab says `unreadable`; header NO DETAILS and "no details for this run"; other runs still draw
- **Actual outcome:** as expected (tab first read "?", fixed)
- **Verdict:** PASS after fix
- **Evidence / issue:** `test_the_rack_labels_an_unreadable_run_as_such`

### UAT-76-5: The page notices a lost server and recovers by itself
- **Linked criterion:** UND-76 AC5
- **Preconditions and data:** console running, a run chosen
- **Steps:** 1. stop the console; 2. wait nine seconds; 3. start it again; 4. wait eight seconds
- **Expected observable outcome:** a "DISCONNECTED - retrying" strip appears and the page dims; after the restart the strip goes away without a reload
- **Actual outcome:** strip visible and page dimmed while down; cleared after restart
- **Verdict:** PASS
- **Evidence / issue:** screenshot `p1-offline.png`

### UAT-76-6: A phone shows the status first
- **Linked criterion:** UND-76 AC6
- **Preconditions and data:** 390 px wide window
- **Steps:** open the page; read the first screen; press LOOK
- **Expected observable outcome:** the status word is near the top (103 px); theme and mode controls are hidden until LOOK is pressed; no horizontal scroll
- **Actual outcome:** status top 103 px, controls hidden, then visible after LOOK, no horizontal scroll
- **Verdict:** PASS
- **Evidence / issue:** screenshot `p1-mobile.png`

### UAT-77-1: A real 937-event household run shows its groups with counts
- **Linked criterion:** UND-77 AC1, AC5
- **Preconditions and data:** the owner's real household run on this machine (5,074 records; counts and stage names only are read)
- **Steps:** open the console on `build/runs`; choose the household run; read the tube; open the first group
- **Expected observable outcome:** five top-level lamps; under `write_records` four groups with counts (`readings.judge_payee`, `refund_readings.link_refund`, `placements.place_merchant`, `named.name_merchant`); opening one lists its stage with a count
- **Actual outcome:** 5 lamps, 4 groups, `25 of 25 done`, `69 of 69`, `818 of 818`, `7 of 7`; the opened group shows `decide - 25 of 25 done`
- **Verdict:** PASS
- **Evidence / issue:** screenshot `p2-household.png`; found: group text unreadable on the dark glass in light mode and on a light tube; fixed with a `--tube-ink` color per theme and checked in all six theme and mode combinations

### UAT-77-2: A growing run lights its stage in progress and its group counts up
- **Linked criterion:** UND-77 AC2, AC4
- **Preconditions and data:** a run folder whose events and `run.json` the test script appends to while the page is open (running, then finished)
- **Steps:** open the console; read the badge and lamp; append two iterations, one unfinished; wait for the poll; finish the run
- **Expected observable outcome:** badge RUNNING and a running lamp; group `1 of 2 done - running`; after the finish the lamp is complete, the group `2 of 2 done`, and the badge is gone
- **Actual outcome:** exactly that
- **Verdict:** PASS
- **Evidence / issue:** session output 2026-11-01

### UAT-77-3: Gauges draw a needle only for a real fraction; the rack groups and badges
- **Linked criterion:** UND-77 AC3, AC4
- **Preconditions and data:** the real household run and two coffee runs
- **Steps:** count the gauges with and without needles; read the rack
- **Expected observable outcome:** STAGES and FAILED have needles; JEV and ELAPSED show only their figures (`932`, `126s`); the rack shows a `household` group and a `coffee_week` group with the newest run first
- **Actual outcome:** 4 gauges, 2 without a needle, figures `5/5`, `0`, `932`, `126s`; groups `household`, `coffee_week`
- **Verdict:** PASS
- **Evidence / issue:** session output 2026-11-01

### UAT-77-4: A run with no nested stages shows no empty groups (rejection-style case)
- **Linked criterion:** UND-77 AC5
- **Preconditions and data:** unit fixture with two top-level stages only
- **Steps:** `bobp make test-py ARGS="test_dashboard.py"`
- **Expected observable outcome:** the tube is two stages with an empty list of groups
- **Actual outcome:** `test_a_run_with_no_nested_stages_has_no_empty_groups` passes
- **Verdict:** PASS
- **Evidence / issue:** test name above

### UAT-88-1: Find a line among 1,876
- **Linked criterion:** UND-88 AC1, AC3, AC4
- **Preconditions and data:** the real household run (1,876 lines)
- **Steps:** type `name_merchant[4]`; clear it and choose the stage `readings.judge_payee`; type text that matches nothing; press CLEAR FILTERS
- **Expected observable outcome:** 6 lines for the text; 50 lines for the stage (25 starts and 25 completions); "no lines match" with a CLEAR FILTERS button; after clearing all 1,876 lines are back and the field is empty, with no reload
- **Actual outcome:** 6, 50, the message, 1,876 and an empty field; the stage menu offered 9 stages and groups
- **Verdict:** PASS
- **Evidence / issue:** session output 2026-11-01

### UAT-88-2: Failures only, and the jumps (failed run)
- **Linked criterion:** UND-88 AC1, AC2
- **Preconditions and data:** a 63-line failed run (failure on the last line); the household run (no failure)
- **Steps:** press FIRST FAILURE on each; tick failures only; type text that hides the failure and press the failure banner; press START and END
- **Expected observable outcome:** FIRST FAILURE disabled with a reason on the clean run, enabled on the failed one; failures only shows exactly the failed line; the banner clears a hiding filter and shows the line; FIRST FAILURE leaves the failed line fully inside the window; START scrolls to 0 and END to the bottom
- **Actual outcome:** as expected
- **Verdict:** PASS
- **Evidence / issue:** session output 2026-11-01

### UAT-88-3: Lines that arrive while a filter is on are filtered too
- **Linked criterion:** UND-88 AC1
- **Preconditions and data:** a growing run; filter text `wanted`
- **Steps:** append an unwanted stage, a wanted stage and a wanted failure; clear the filter
- **Expected observable outcome:** only the two wanted lines appear; FIRST FAILURE becomes enabled by the live failure; clearing shows all five lines
- **Actual outcome:** 2 lines, button enabled, then 5
- **Verdict:** PASS
- **Evidence / issue:** session output 2026-11-01

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 6 passed (3 after a fix found in the run); Phase 2: 4 passed (1 after a contrast fix); Phase 3: 3 passed; 0 failed, 0 blocked. Phases 4 to 7 not yet run.
- **Open issues and impact:** none for Phase 1. The `with` values in `run.json` are file paths as typed (SEC-004 covers the sketch path, now stored relative).
- **Overall verdict:** Phase 1 PASS
- **Handoff evidence:** `agents/CHAT.md` message "UAT phase 1 passed"
