# UAT Plan: Sprint 27, the test pyramid

- **Stories / criteria:** UND-101 to UND-104 in `docs/sprints/STORY_ARCH_SPRINT27.md` (with its amendments)
- **Environment and build:** branch `sprint-27`, local; the fixture exports under `tests/fixtures/household`, the coffee example in replay mode, a real Chromium
- **Date / tester:** 2026-11-03, Trin (Smith for the end-to-end pass)
- **Entry conditions:** a measured baseline (`unittest --durations`): unit 94.6 s for 554 tests, browser 154.9 s for 39 tests with one flake
- **Exit conditions:** each acceptance criterion passes or its miss is stated with the number

## Scenarios

### UAT-27-1: Child sketches load faster (Phase 1)

- **Linked criterion:** UND-101 AC1 to AC3
- **Steps:** run the household on the fixtures and the coffee example in replay mode on `main` (a clean checkout) and on this branch; hash every sink file and `summary.json`; time 30 loads of the household child
- **Expected observable outcome:** identical hashes; a smaller per-row load
- **Actual outcome:** all 13 hashes identical; per-row child load 71.5 ms to 38.6 ms (-46%); a whole household run 1.92 s to 1.68 s (-12%)
- **Verdict:** PASS (the saving is smaller than the profile suggested; recorded in the amendments)
- **Evidence / issue:** chat message "UAT phase 1 passed"

### UAT-27-2: One stage on its own (Phase 2)

- **Linked criterion:** UND-102 AC1, AC3
- **Steps:** break five payment rules in the real sketch (allocate by the bank's date, the 5% flag, the open balance, the top-five list, the pool), one at a time, and run the moved tests; restore from git
- **Expected observable outcome:** every break is caught by at least one moved test
- **Actual outcome:** all five caught; the payments file 5.2 s to 1.1 s with two new tests
- **Verdict:** PASS
- **Evidence / issue:** chat message "UAT phase 2 passed"

### UAT-27-3: The rest of the household rules (Phase 3)

- **Linked criterion:** UND-102 AC2 to AC4
- **Steps:** break one rule per group (the Jev threshold, a link counting, pins asked again, spending categories, the crosswalk flag, the category name) and run the moved tests; count the whole-sketch runs; time the household files
- **Expected observable outcome:** every break caught; at most five whole-sketch runs; 15 s or less
- **Actual outcome:** all six caught (4 to 7 failures each); five whole-sketch runs (the happy path, an empty period, three early refusals); the household files 73 tests in about 57 s became 80 tests in 11.4 s
- **Verdict:** PASS
- **Evidence / issue:** chat message "UAT phase 3 passed"

### UAT-27-4: The browser suite shows only what a browser can (Phase 4)

- **Linked criterion:** UND-103 AC1 to AC4 (as amended)
- **Steps:** time the browser suite; run it again; look for the old `.stage-lamp` flake
- **Expected observable outcome:** 90 s or less, no flake in five runs
- **Actual outcome:** 154.9 s (one flake) became 101.3 s and 99.5 s on two consecutive full runs, 39 of 39 each, no flake
- **Verdict:** PARTIAL: flake gone on the runs made; **time target missed by about 10 s; five runs were not made, two were**
- **Evidence / issue:** contrast stays on real pixels because the themes draw on textures; the remaining time is about 2 s per page test

### UAT-27-5: The gate fails fast and the strategy is written down (Phase 5)

- **Linked criterion:** UND-104 AC1 to AC3
- **Steps:** a deliberate lint error in a scratch file, `bobp make check` before and after the change; one full gate; read `docs/TEST_STRATEGY.md` and `docs/SDLC.md`
- **Expected observable outcome:** a lint error stops the gate in seconds; the unit suite 30 s or less; the budgets and the order recorded
- **Actual outcome:** 31.8 s before, 0.16 s after; unit suite 29.4 s (586 tests); the whole gate 36.3 s with exit 0 (was 96 to 101 s); both documents updated
- **Verdict:** PASS
- **Evidence / issue:** chat messages "Phase 5" and the final check log

## Results and Handoff

- **Passed / failed / blocked:** 4 passed, 1 partial (UAT-27-4: browser time target missed by about 10 s), 0 failed
- **Open issues and impact:** the browser suite is about 100 s against a 90 s target, no flake; it is outside the gate. Two runs, not five. Merging browser tests would cut the rest but loses isolation; left for the owner to decide.
- **Overall verdict:** PASS with one stated miss
