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

### UAT-78-1: A replayed run shows the answers it replayed, with two Jev gauges
- **Linked criterion:** UND-78 AC1, AC3, AC4
- **Preconditions and data:** the committed coffee capture replayed with `--replay=tests/fixtures/coffee/replay` into a scratch folder
- **Steps:** open the console on that folder; read the Jev summary; open the list and the first read
- **Expected observable outcome:** `1 read, 0 unsure`; the read names its source, its top level `much_colder` at 0.95 and 5 levels; gauges SURE 0.95 and ASKED `0·1` (none asked, one reused)
- **Actual outcome:** exactly that; the old capture has no question, so none is shown (expected)
- **Verdict:** PASS
- **Evidence / issue:** session output 2026-11-01

### UAT-78-2: The real household run: 932 reads, the unsure ones can be isolated
- **Linked criterion:** UND-78 AC1, AC2, AC4
- **Preconditions and data:** the owner's real run on this machine; counts only are recorded
- **Steps:** choose the run; read the summary; open the list; tick "unsure only"
- **Expected observable outcome:** the count of reads and of unsure reads; the filter shows exactly the unsure ones; gauges SURE and ASKED `932·0`
- **Actual outcome:** 932 reads, 481 unsure (top level below 0.7 or `none_of_these`); the filter showed 481; ASKED `932·0`; SURE 0.64
- **Verdict:** PASS
- **Evidence / issue:** this is the first measurement of how often Jev is unsure on the real data; reported to the owner as counts. Found: refund candidates are named by date and amount (SEC-007), so the first build sent them to the network; fixed with `levels_from_data` and re-verified: 0 level names with a date or an amount in the payload

### UAT-78-3: A run without captures says why on its summary line (rejection paths)
- **Linked criterion:** UND-78 AC3, AC5, AC6
- **Preconditions and data:** an older coffee run whose captures were pruned; a run that never asked Jev; a capture folder with one file missing its other half
- **Steps:** choose each run; read the summary line
- **Expected observable outcome:** `captures no longer kept for this run`; `this run did not ask Jev`; the broken half named while the rest lists
- **Actual outcome:** the first run showed the note only inside the closed list (hard to find), moved to the summary line and rechecked; the others as expected (broken half by unit test)
- **Verdict:** PASS after fix
- **Evidence / issue:** `test_a_run_whose_captures_were_pruned_says_so`, `test_a_run_that_never_asked_jev_says_so`, `test_a_capture_missing_its_other_half_is_named_and_the_rest_still_lists`

### UAT-79-1: Every refusal on the design's list, from outside (23 requests against a running console)
- **Linked criterion:** UND-79 AC2, AC3, AC5, AC8, AC9; SEC-005, SEC-006, SEC-008, SEC-009
- **Preconditions and data:** `understudy dashboard <scratch runs> --sketches <scratch sketches>`; the sketches folder holds a copy of the coffee sketch and a symlink named `link.yaml` pointing at `/etc/hostname`; the committed coffee capture copied into the cache under a fixture run id for the replay, removed afterwards
- **Steps:** the request list in `uat5.py` (scratch folder): list; session; POST with no secret, a wrong one, a foreign `Origin`, a 20 KB body, a body that is not an object; sketch names `../../../etc/hostname`, `/etc/hostname`, `link.yaml`, `coffee/../../x.yaml`; an unknown `--with` name; a replay id `../../etc`; `Content-Length: -1` and `abc`; DELETE; an unknown POST path; a real replay start; stop of a finished run, of a run it never started, and of `../../x`
- **Expected observable outcome:** 401 (no or wrong secret), 403 (foreign origin, sketches outside the folder, the symlink), 413, 400, 400, 501, 404; the list offers the coffee sketch only (the symlink is greyed out); the real start answers started, finishes `done` in the watched folder; the secret is not in the output and its file is mode 0600
- **Actual outcome:** 23 of 23 as expected; two defects found by this attack and fixed before it passed: the secret was printed to captured output (SEC-008) and a negative Content-Length waited (SEC-009); a symlink that leaves the folder was listed (fixed: not listed)
- **Verdict:** PASS after fixes
- **Evidence / issue:** `uat5.out` in the session scratch folder; tests `AnnounceTest`, `test_a_negative_or_unreadable_content_length_is_400_not_a_wait_for_more_data`, `test_a_symlink_that_leaves_the_folder_is_not_listed_at_all`

### UAT-79-2: Stop ends a real process and marks its run stopped
- **Linked criterion:** UND-79 AC5
- **Preconditions and data:** a real child process that sleeps for a minute, started by the launcher
- **Steps:** start; stop; start the same sketch again
- **Expected observable outcome:** the process is gone after Stop; the run's `run.json` says `stopped`; the sketch can be started again
- **Actual outcome:** as expected
- **Verdict:** PASS
- **Evidence / issue:** `RealStopTest`

### UAT-79-3: A second Play and a fifth run are refused (rejection paths)
- **Linked criterion:** UND-79 AC10
- **Preconditions and data:** fake processes that stay alive
- **Steps:** Play the same sketch twice; Play five different sketches
- **Expected observable outcome:** 409 "already running"; 409 "at most 4 runs at once"; after one ends the sketch may start again
- **Actual outcome:** as expected
- **Verdict:** PASS
- **Evidence / issue:** `StartTest`

### UAT-79-4: The start panel in a real browser: locked, wrong secret, right secret
- **Linked criterion:** UND-79 AC1, AC2, AC8
- **Preconditions and data:** a console on a scratch runs folder with `--sketches` holding two copies of the coffee sketch and an unreadable `broken.yaml`; the access secret read from its private file
- **Steps:** open the page; open START A RUN; read the sketch list; try PLAY; type a wrong secret; type the right one
- **Expected observable outcome:** the panel is shown; the list offers both coffee sketches and `broken.yaml - unreadable`; locked, PLAY is disabled with the reason "needs the access secret" and a note that you can watch but not start; a wrong secret says it is not this console's secret and stays locked; the right one unlocks, enables PLAY and clears the box
- **Actual outcome:** exactly that
- **Verdict:** PASS
- **Evidence / issue:** `p6.out` in the session scratch folder

### UAT-79-5: Replay a captured run from the page, watch it finish
- **Linked criterion:** UND-79 AC5, AC6, AC7
- **Preconditions and data:** the committed coffee capture copied into the cache under a fixture run id (removed afterwards); no Jev key needed
- **Steps:** choose the coffee sketch; choose the fixture in "Replay from"; PLAY
- **Expected observable outcome:** a new run appears in the rack, the header reads DONE, and the panel says how it ended
- **Actual outcome:** `run ended: done after 5 stages`; header DONE; the rack gained the run
- **Verdict:** PASS
- **Evidence / issue:** `p6.out`

### UAT-79-6: Stop a real run; a second Play; Stop for a run this console did not start (rejection paths)
- **Linked criterion:** UND-79 AC5, AC7, AC10
- **Preconditions and data:** a real run paused with SIGSTOP right after it made its run folder (so it stays running and ignores SIGTERM); a run folder from another source whose status says running
- **Steps:** PLAY; PLAY again; STOP; choose the foreign run; STOP
- **Expected observable outcome:** started with its run id, header RUNNING, STOP enabled; the second PLAY says "already running as <run>" with an OPEN THAT RUN button; STOP ends the run (after the 3 s grace, then SIGKILL), the header reads STOPPED, STOP disables and PLAY re-enables; STOP on the foreign run says it was not started by this console
- **Actual outcome:** as expected after one fix: a run killed before its first stage finished has no `run.json`, so it kept reading RUNNING; the launcher now writes the stopped state itself (test added)
- **Verdict:** PASS after fix
- **Evidence / issue:** `p6.out`; `test_a_run_stopped_before_its_first_stage_finished_has_no_run_json_yet_and_still_reads_stopped`

### UAT-79-7: The secret stays out of addresses, page text and long-lived storage; a phone fits
- **Linked criterion:** UND-79 AC8; SEC-005
- **Preconditions and data:** the same console; every request URL recorded
- **Steps:** unlock, run the flows above, then search the URLs, the page text, `localStorage` and `sessionStorage` for the secret; open a second tab and a 390 px window
- **Expected observable outcome:** the secret appears in no URL, no page text and not in `localStorage`; it is in `sessionStorage` only; every POST carried it in the header; a new tab is locked again; no horizontal scroll on the phone
- **Actual outcome:** URLs false, page text false, localStorage false, sessionStorage true; 5 of 5 POSTs carried the header; the new tab was locked; no horizontal scroll
- **Verdict:** PASS
- **Evidence / issue:** `p6.out`, `p6-phone.png`

### UAT-80-1: Every way the console can fail to start is one plain line (rejection paths)
- **Linked criterion:** UND-80 AC1, UND-79 AC3
- **Preconditions and data:** a port already held by another program; a runs path that is a file; a sketches path that is missing or has no sketches
- **Steps:** `understudy dashboard <runs> --port <busy> --sketches <folder>` and the variants
- **Expected observable outcome:** each prints exactly one `understudy: <message>` line on standard error, exits 2, shows no traceback
- **Actual outcome:** `understudy: port N is already in use; choose another with --port`; `... is not a folder of runs`; `... is not a folder` and `no sketches found in ...`
- **Verdict:** PASS
- **Evidence / issue:** `tests/python/test_cli_console.py::DashboardFailureTest` (before the fix a busy port printed a Python traceback)

### UAT-80-2: Help teaches, `run` names its run, `runs` lists them
- **Linked criterion:** UND-80 AC2, AC3
- **Preconditions and data:** none for help; the committed coffee capture for a replayed run; two run folders for `runs`
- **Steps:** `understudy --help` and `understudy <command> --help`; a replayed `understudy run`; `understudy runs <folder>`, an empty folder and a missing one
- **Expected observable outcome:** every command described with examples and its options explained; the run prints `run: <id>` and `watch it: understudy dashboard <folder>` and still ends on its outputs and outcome; `runs` lists newest first with the state, or says "no runs in <folder>" and exits 0
- **Actual outcome:** as expected; one defect found by existing tests: printing the id after the outcome broke the documented "the outcome is the last line" contract, so the id now comes before the `wrote` lines
- **Verdict:** PASS after fix
- **Evidence / issue:** `HelpTest`, `RunEndsWithTheRunIdTest`, `RunsCommandTest`

### UAT-80-3: Every control can be reached and used with the keyboard alone
- **Linked criterion:** UND-80 AC4
- **Preconditions and data:** a console with a failed run and a sketch to start
- **Steps:** press Tab 80 times from the top of the page and record each element that takes focus, its accessible name and whether focus is visible
- **Expected observable outcome:** the filter, stage menu, failures-only box, jump buttons, secret box, unlock, sketch and replay menus are all reached; none lacks a name; each shows a focus indicator
- **Actual outcome:** all reached, named and visibly focused (the unit tests cannot see this; the browser check does)
- **Verdict:** PASS
- **Evidence / issue:** `tests/browser/test_console.py::KeyboardTest`

### UAT-80-4: Text meets 4.5:1 (3:1 for large text) in all three themes, light and dark
- **Linked criterion:** UND-80 AC5
- **Preconditions and data:** six looks (steampunk, professional, starship, each light and dark) of one screen holding a failed run, the banner, the printer with an empty filter result, the start panel and the Jev line; 28 kinds of text
- **Steps:** for each kind of text in each look, hide the text, screenshot the element, decode the pixels, and compare the text color with every color that fills at least 8% of the interior
- **Expected observable outcome:** no text below its threshold
- **Actual outcome:** the first honest measurement found 25 failures in new and old text (header subtitle and status on the brass plate, rack labels, the ended line, panel headings, the start and Jev headings, the empty-filter note, filter labels, the starship orange); all fixed with theme variables and checked again: 0 failures. Three earlier versions of the measuring code were wrong (counted anti-aliased text, borders and child controls as backdrop) and were corrected until a known-good element read right
- **Verdict:** PASS after fixes
- **Evidence / issue:** `ContrastTest`; no exception was needed, so none is recorded for the owner to accept

### UAT-80-5: The written, repeatable browser check
- **Linked criterion:** UND-80 AC6
- **Preconditions and data:** `bobp make install-browser`; Chromium at `/usr/bin/chromium`
- **Steps:** `bobp make test-browser`
- **Expected observable outcome:** rack switching and the failed banner, live following, losing and regaining the server, unlock/play/second play/stop, keyboard and contrast all pass; without the tools every test is skipped with the reason
- **Actual outcome:** 6 tests pass in about a minute
- **Verdict:** PASS
- **Evidence / issue:** `tests/browser/test_console.py`; tool approved by Tank and recorded in `docs/SDLC.md`

### UAT-22-E2E: Smith's end-to-end user test on the real console and the real household run (sprint close)
- **Linked criterion:** UND-76 AC1-4, UND-77 AC1-4, UND-88 AC1-3, UND-78 AC1-2, 4, 7, UND-79 AC1, 4, 8, UND-80 AC2, 4
- **User / task:** the owner, who wants to know how last week's household run went, find what Jev was unsure about, and start the next run without a terminal
- **Preconditions and data:** the finished code on `sprint-22`; the console restarted on port 4180 over the owner's `build/runs` with `--sketches examples`; the real run of 2026-10-31 (made before this sprint); the real access secret read from its file; only counts and shapes are recorded
- **Steps:** open the page; read the rack; choose the household run; read the header, the ended line, the summary, the gauges; filter the printer; open JEV READS locked, then unlock and look again; open START A RUN, choose the household sketch, read its form; open on a phone
- **Expected observable outcome:** a rack grouped by sketch; DONE after 5 stages with 5 lamps and 4 groups; the figures 5/5, 0, 932, 126 s, 0.64 and 932·0; `name_merchant[4]` finds 6 lines; the Jev summary reads 932 reads, 481 unsure; locked, no level name from the owner's data is visible and the page says why; unlocked, they are; the panel lists the evening and the household (the called child sketches are not listed), shows the household's four fields, and PLAY is off until unlocked; the phone shows the status on the first screen with no horizontal scroll
- **Actual outcome:** all as expected. Smith's one finding: locked, the list said "option 3" with no word on why (H1, H9); fixed in this sprint: the list says how many reads have hidden names and how to see them, and the note goes away after unlocking (unit test `test_the_list_says_how_many_reads_have_their_names_hidden...`). Observed and left: this run predates the sprint, so its summary shows "-" for outcome, `with` and `wrote`, which reads the same as "none" (backlog)
- **Verdict:** PASS
- **Evidence / issue:** `p7.js` output in the session scratch folder; `p7-desktop.png`, `p7-phone.png`; `*user bug` filed and triaged in `agents/CHAT.md`

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 6 passed (3 after a fix found in the run); Phase 2: 4 passed (1 after a contrast fix); Phase 3: 3 passed; Phase 4: 3 passed (1 after a fix; 1 privacy defect found and fixed, SEC-007); Phase 5: 3 passed after fixes (SEC-008 and SEC-009 found by the attack and fixed); Phase 6: 4 passed (1 after a fix); Phase 7: 5 passed (2 after fixes); 0 failed, 0 blocked.
- **Open issues and impact:** none for Phase 1. The `with` values in `run.json` are file paths as typed (SEC-004 covers the sketch path, now stored relative).
- **Overall verdict:** PASS: phases 1 to 7 and Smith's end-to-end user test; 0 failed, 0 blocked; the one usability finding is fixed.
- **Handoff evidence:** `agents/CHAT.md` messages "UAT phase N passed" for each phase; screenshots and outputs in the session scratch folder
