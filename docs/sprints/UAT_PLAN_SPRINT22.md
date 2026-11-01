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

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 6 passed (3 after a fix found in the run), 0 failed, 0 blocked. Phases 2 to 7 not yet run.
- **Open issues and impact:** none for Phase 1. The `with` values in `run.json` are file paths as typed (SEC-004 covers the sketch path, now stored relative).
- **Overall verdict:** Phase 1 PASS
- **Handoff evidence:** `agents/CHAT.md` message "UAT phase 1 passed"
