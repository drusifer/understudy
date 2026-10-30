# Project Lessons Learned

This file contains critical lessons and rules derived from past errors, technical discoveries, and architectural decisions. All agents MUST review this file before starting new implementation or architectural tasks.

---

## [2026-10-15] Test doubles must behave like the thing they replace

> **Tags:** #testing #jev #Neo

### Context
Sprint 1 phase 1 made `play` refuse off-list picks (ADR-0004). Two moved recard seat tests failed.

### The Issue
Their Jev double always answered `build`, even when only `pass` was offered - something real Jev cannot do. The tests had been passing only because of recard's silent fallback.

### The Solution
The double now picks only from `request.questions.<key>.criteria`, like Jev.

### The Rule (The "Lesson")
A judge double MUST choose only among the options in the request. When a behaviour change breaks a test, first ask whether the test's double was impossible, before changing the code back.

### References
- **Commit:** 5da0ab4
- **Files:** `tests/jevSeat.test.js`, `src/library.mjs`

## [2026-10-15] A race test must fail without its fix

> **Tags:** #testing #targets #Trin

### Context
Phase 5: a program can print its end and exit between two looks; the run loop now looks once more before calling it `app-exited`.

### The Issue
The first test for it passed WITHOUT the fix: the seat's own after-step look consumed the single stale view, so the race never happened in the test.

### The Solution
Made the stale view last two looks and verified the test fails with `git stash -- src/run.mjs`, passes with the fix.

### The Rule (The "Lesson")
For every race or timing fix, run its test once against the unfixed code and see it fail. Count every hidden read (after-step `markSeen` looks too) when faking "stale for N looks".

### References
- **Commit:** 36af7f8
- **Files:** `tests/run.test.js`, `src/run.mjs`

## [2026-10-15] Never rename identifiers with a blanket sed

> **Tags:** #tooling #lint #Neo

### Context
Phase 2: lint asked for `env` -> `environment`; a `sed s/\benv\b/environment/g` was used.

### The Issue
It also rewrote `process.env` to `process.environment` (undefined) and a `spawnSync` option key - caught only because a test spawned the real command.

### The Solution
Fixed by hand; option keys and Node APIs restored.

### The Rule (The "Lesson")
Rename variables with an edit scoped to the declarations and uses (or VIA), never a word-boundary sed over a file: property names and platform APIs share the word.

### References
- **Commit:** e02f5d3
- **Files:** `src/cli.mjs`, `tests/cli.test.js`

## [2026-10-15] A CLI target's view must be what a person sees

> **Tags:** #targets #adapters #Morpheus

### Context
Phase 5: the process target first exposed raw stdout. Program output after an input ran onto the prompt line (`prompt> hello ann`) because pipes do not echo.

### The Issue
Adapters reading that view could not tell answers from output, and a look before the program replied still showed the old question - an adapter could answer it twice.

### The Solution
The target echoes each input where it was typed and reports `sent`; the CLI adapter only says `asking` while questions printed > inputs sent.

### The Rule (The "Lesson")
A target's view should match what a person would see, and carry enough bookkeeping (`seq`, `sent`) for an adapter to know a question is still unanswered.

### References
- **Commit:** 36af7f8
- **Files:** `src/targets/process.mjs`, `examples/cli/adapter.mjs`

## [2026-10-15] A test for a hang must be bounded itself

> **Tags:** #testing #run-loop #Neo #Trin

### Context
Sprint 2 phase 1: the stall test was written first (TDD), before the stall rule existed.

### The Issue
Without the rule the test's run never ends - so the whole `make test` hung until the 300 s tool
timeout, and the background job had to be stopped by hand.

### The Solution
Stopped the job, implemented the rule, and ran the suite with an outer `timeout` while
iterating on liveness code.

### The Rule (The "Lesson")
When writing a test for "does not hang" behaviour, run it under a bound first (`timeout 120 node
--test ...` or `--test-timeout`), so a red test fails instead of hanging. Never leave a suite that
can wait forever as the only signal.

### References
- **Commit:** aaf479d
- **Files:** `tests/run.test.js`, `src/run.mjs`

## [2026-10-15] Never chain a commit onto a write that might be refused

> **Tags:** #process #git #Mouse

### Context
Sprint 2 planning: `task.md` was written with the Write tool and committed in the same batch.

### The Issue
The Write was refused (the file had changed since it was read), but the commit ran anyway and
recorded the old sprint 1 board under "Sprint 2 planning".

### The Solution
Archived the sprint 1 board to `docs/sprints/TASKS_SPRINT1.md`, rewrote `task.md`, and amended
the local (unpushed) commit.

### The Rule (The "Lesson")
Commit only after every file edit in the batch is confirmed. If an edit can fail, put the commit
in the next step, and check `git show --stat` lists the files you meant to commit.

### References
- **Commit:** 75ee94b
- **Files:** `task.md`, `docs/sprints/TASKS_SPRINT1.md`

## [2026-10-15] Probe a library's real output before designing around it

> **Tags:** #architecture #playwright #Morpheus

### Context
Sprint 2 architecture: dropping the page hook depended on what Playwright's accessibility
snapshot actually contains.

### The Issue
The design (hidden controls absent, disabled marked, options nested under their list, names
quoted) rested on assumptions about an output format.

### The Solution
A 15-line probe against Playwright 1.62.1 printed a real snapshot before ARCH_SPRINT2 was written;
that snapshot became the parser's recorded test fixture.

### The Rule (The "Lesson")
Before an architecture depends on a library's output shape, run a throwaway probe and paste its
real output into the design and the tests. Record the library version with it.

### References
- **Commit:** 761ea11
- **Files:** `tests/aria.test.js`, `src/targets/aria.mjs`, `docs/sprints/ARCH_SPRINT2.md`

## [2026-10-15] Read what the model can answer before promising what it will do

> **Tags:** #stories #typesafe #Cypher #Morpheus

### Context
Sprint 3 shaping: the owner chose "sketch supplies calls + Jev fills the arguments" for MCP tools.

### The Issue
"Jev fills arguments" reads as free-text generation. TypeSafe's `systemOne` answers only
`noul`, `choice` and `score` questions (`node_modules/@typesafe-ai/sdk/dist/index.d.mts`), so Jev
cannot write a value at all.

### The Solution
Before the stories were written, the SDK's question types were read. The stories turned
"fills" into "chooses from a finite list" (schema, sketch values, last result), said so as an
owner-visible assumption and an open question, and the architecture made it ADR-0013.

### The Rule (The "Lesson")
Before a story promises what a model or library will do, read its declared types or a probe of
its output, and state any narrowing of the owner's words as an assumption the owner can overturn.

### References
- **Files:** `docs/sprints/USER_STORIES_SPRINT3.md` (Assumptions, Open Questions), `docs/DECISIONS.md` ADR-0013

## [2026-10-15] Put an error between the producer and the consumer in the end-to-end test

> **Tags:** #testing #mcp #Neo #Trin

### Context
Sprint 3 Phase 2: tool arguments are chosen from values in "the last result" (a film id from
`list_films` feeds `pick_seats`; a hold from `pick_seats` feeds `pay`).

### The Issue
The happy-path live run passed. The end-to-end test with a refused payment (`cash`) between
`pick_seats` and the second `pay` failed: the error answer became "the last result", the hold
vanished from the candidates, and `pay` could no longer be offered - Jev's next pick was off the
list twice.

### The Solution
Candidates come from the last result that was **not an error**; the stories, the architecture and
ADR-0013 were amended, and a unit test pins it (`tests/mcpApp.test.js`).

### The Rule (The "Lesson")
When state is derived from "the last answer", test a run where an error answer lands between the
answer that produces the state and the move that uses it.

### References
- **Commit:** b7ddba1
- **Files:** `src/apps/mcp.mjs`, `tests/examples.test.js`, `tests/mcpApp.test.js`

## [2026-10-15] An "absence grep" criterion must list its required exceptions up front

> **Tags:** #stories #docs #Cypher #Smith

### Context
Sprint 3 UND-12 AC3: `grep` for `adapter.mjs|part/turn|part/questions` must find nothing. Sprint 2
UND-8 AC2 had the same shape for `__understudy`.

### The Issue
Both sprints, the grep could never be empty: UND-9 AC6 *requires* the refusal message to name
`adapter.mjs` and `part/`, and the migration note must name them too. The criterion was amended
during UAT - the second sprint running.

### The Solution
UND-12 AC3 now names its exceptions (the old-layout refusal, its troubleshooting row, the
migration paragraph, history files).

### The Rule (The "Lesson")
When an acceptance criterion says "the old name appears nowhere", list at story time every place
another criterion requires it to stay (refusal messages, migration notes, history), so the test is
a yes/no from the start.

### References
- **Files:** `docs/sprints/USER_STORIES_SPRINT3.md` UND-9 AC6, UND-12 AC3; `docs/sprints/USER_STORIES_SPRINT2.md` UND-8 AC2

## [2026-10-15] Look at a drawing before building on it - tests cannot see overlap

> **Tags:** #ux #layout #Trin #Neo

### Context
Sprint 4 Phase 2: a layered SVG layout of the sketch's statechart, with unit tests (every state
and edge present, boxes not overlapping, paths well-formed).

### The Issue
All tests passed, but the first rendered picture had transition labels squeezed under the next
box and two back-edge labels colliding with a forward curve. Nothing the tests checked was false.

### The Solution
Trin rendered the layout to SVG and screenshotted it in headless Chromium before the page was
built; column gaps became as wide as the longest label crossing them, and back edges arc above
the top row. Re-rendered clean.

### The Rule (The "Lesson")
For anything visual, render it and look at it (a headless screenshot is enough) before building
on it; geometry tests confirm structure, not legibility.

### References
- **Commit:** 7e878cb
- **Files:** `src/watch/layout.mjs`, `tests/turnGraph.test.js`

## [2026-10-15] Replay at the grain of what the user asked to see

> **Tags:** #ux #replay #Trin #Morpheus

### Context
Sprint 4 Phase 5: replay frames first ended at each step line.

### The Issue
A step's own transitions (`choosing -> acting -> waiting`) are logged just before its step line,
so every frame showed `waiting`: replay never showed the move state where Jev decided, nor the
state changes the owner asked to watch.

### The Solution
One frame per log line: Step forward/back walk each state change; clicking a decision jumps to
that step's line.

### The Rule (The "Lesson")
When replaying a record, choose frames at the grain of the thing the user wants to see (here,
state changes), not at the grain that is easiest to count (steps).

### References
- **Commit:** 26e6b03
- **Files:** `src/watch/page.mjs` (`framesOf`), `tests/replay.test.js`

## [2026-10-15] A new wait point needs its own way out

> **Tags:** #architecture #runloop #Morpheus #Neo

### Context
Sprint 4 Phase 4: the pause gate waits in a move state, before the step.

### The Issue
Ctrl-C sends `QUIT`, which only takes effect at a state tagged `safe`; a move state is not safe,
so a paused run would have made its move (a Jev call) before stopping - the opposite of "stop at
once while paused".

### The Solution
Ctrl-C releases a paused gate with `stop`, and the loop ends without stepping (`interrupted`,
"stopped by Ctrl-C while paused"); a running watched run keeps the old behaviour.

### The Rule (The "Lesson")
When adding a place where a loop can wait, check how each existing way of stopping reaches that
place, and give the wait its own exit if they do not.

### References
- **Commit:** 86d9c8c
- **Files:** `src/watch/gate.mjs`, `src/run.mjs`, `tests/watchRun.test.js`

## [2026-10-16] Jev sees only what the view shows - a multi-call plan needs its memory in view

### Context
Sprint 5 Phase 7: the first live run of `examples/evening` (two servers, a decision that needs a
film list, ratings and a seat map before it can act).

### The Issue
It booked correctly but took 24 steps: after each rating call, Jev's view held only that answer
(`last_call`), so it listed the films again before every next rating. The unit tests with a Jev
double never showed it - the double was scripted to prefer the right tool.

### The Solution
In a deciding sketch, Jev's view also carries what each other tool last said (`earlier`, 1000
characters each). The same live run took 7 steps.

### The Rule (The "Lesson")
When a task needs facts from several calls, put what was already learned in the model's view -
and check the step count of a live run, not only its outcome: a double that knows the plan hides
a model that cannot see it.

### References
- **Commit:** 9966798
- **Files:** `src/apps/mcp.mjs`, `tests/decideApp.test.js`, `docs/MCP_GUIDE.md` §9

## [2026-10-16] A test helper that skips the look hides state the app builds while looking

### Context
Sprint 5 Phases 3 and 5: app tests drove the evening servers with `target.act` and then asked
the app for moves.

### The Issue
The app remembers answers (rows), counts steps (spent values, reused Scores) and asks Jev in
`moves`, `act` and `prepare` - the calls a run makes on every look. Tests that called
`target.act` directly skipped them: answers went unremembered and step counts stayed at 0, so
assertions failed for reasons a run never has.

### The Solution
Test helpers do what a run does: `app.act(move)` to make the action, `target.act`, then a look
(`prepare`, then `moves`).

### The Rule (The "Lesson")
When an object keeps state across a loop, drive it in tests through the same sequence of calls
the loop makes; a shortcut tests a sequence that never happens.

### References
- **Files:** `tests/decideApp.test.js`, `tests/jevScore.test.js`

## [2026-10-16] Look at the page you built, not only its tests

### Context
Sprint 6 Phases 4-5: the dashboard page, built from an approved mockup.

### The Issue
Unit tests passed while the page was wrong in ways only a picture shows: the weight colours did
not appear (CSS custom properties set through `Object.assign(style, ...)` are silently dropped),
and the tube's edge labels piled on top of each other.

### The Solution
A throwaway Playwright script screenshotted the real console after each change; the colours were
fixed with `style.setProperty`, the tube relaid (neighbours along the loop, finals beside their
source), and a committed browser test now plays the evening from the console.

### The Rule (The "Lesson")
For anything visual, look at it rendered after every change - a screenshot is a test only a person
(or a model reading it) can run; keep a committed browser test for what must keep working.

### References
- **Commit:** a6ebcb9, 1108493
- **Files:** `src/dashboard/page.mjs`, `src/dashboard/tube.mjs`, `tests/browser/dashboard.test.js`

## [2026-10-16] Round-tripping a hand-written file through a parser rewrites it

### Context
Sprint 6 Phase 6: access-panel edits saved to `sketch.yaml`.

### The Issue
Editing the YAML Document and re-serialising kept comments but reflowed long lines and re-spaced
every flow list - 16 lines of a 116-line file changed for a one-value edit.

### The Solution
Find the value's source range through the parser and replace only that text; check the result by
loading a copy before writing.

### The Rule (The "Lesson")
When a tool writes into a file people maintain by hand, change only the bytes of the value - and
test that every other line is identical.

### References
- **Commit:** 88287b1
- **Files:** `src/dashboard/settings.mjs`, `tests/settings.test.js`

## [2026-10-27] Check the worktree before saying it is clean, and read a file before overwriting it

> **Tags:** #Process #Git #Cypher

### Context
Sprint 16 planning was restarted from a sprint branch whose worktree looked clean because it sat at the
same commit as `main`. It held ten days of uncommitted work, including the approved stories file.

### The Issue
Cleanliness was inferred from `git worktree list`, never from `git status`. A story file was then written
over without being read first; it was untracked, so git could not restore it, and the stories had to be
rebuilt from other documents.

### The Solution
Ran `git status` in the worktree, found the existing sprint, restored the stories from the architecture,
UAT plan and task board, and moved the new draft to its own file.

### The Rule (The "Lesson")
Before planning in or reporting on a branch or worktree, run `git status` there. Before writing a file that
may exist, Read it; if it is untracked, copy it aside first.

### References
- **Files:** `docs/sprints/USER_STORIES_SPRINT16.md`, `docs/sprints/USER_STORIES_SPRINT17.md`

## [2026-10-27] Test a matching rule on aggregate real data before writing criteria

> **Tags:** #Process #ETL #Cypher #Morpheus

### Context
Sprint 16's reconciliation pairs rows with the same date and the same amount. The synthetic fixtures passed
and the sprint was accepted.

### The Issue
On the owner's real files it matched 26 rows. The Amex export and Monarch record the same purchase with
opposite signs, so about 4,200 real overlaps were never paired. Nothing before the real-data run could show it.

### The Solution
Counted matches on the real files with signs flipped (aggregates only, no transaction text) and planned the
sign-flipped match, transfers and refunds as Sprint 17.

### The Rule (The "Lesson")
When a story depends on how two real data sources relate, count the candidate matches on the real data
(aggregates only) before writing the acceptance criteria, and give the test fixture the same shape.

### References
- **Files:** `docs/sprints/USER_STORIES_SPRINT17.md`, `docs/sprints/ARCH_SPRINT16.md`

---

## [2026-10-29] A shared preflight check needs the policy, not just the permission

> **Tags:** #privacy #testing #Neo #Trin

### Context
Sprint 17 Phase 5 (UND-54 AC4) said private output must stay out of tracked folders and `data/`. The shared `_check_writable` only tested that the path was a writable directory, so `--out src/` exited 0 (DEF-UND54-01).

### The Issue
The permission check passed every writable path, and the acceptance test for the policy only ran in UAT, after the phase was called complete.

### The Solution
Added `_check_destination_policy`: the resolved path is refused under `data/` or when `git check-ignore` does not ignore it; outside paths and ignored `build/` pass. Boundary tests cover data/, tracked folders, ignored build, outside and a symlink into `src/`.

### The Rule (The "Lesson")
When an acceptance criterion restricts where something may be written, test the forbidden and permitted destinations (including symlinks) with the controller stubbed, in the same task that adds the writable check.

### References
- **Files:** `src/etl/controller.py`, `tests/python/test_etl_cli.py`, `docs/sprints/UAT_PLAN_SPRINT17.md`

---

## [2026-10-30] Share the loop before writing a second one

> **Tags:** #dry #architecture #Neo #Morpheus

### Context
Sprint 19 needed a state-machine loop for sketches. The ETL controller already had one (`_run_stages`), tied to its linear stage list and its own manifest.

### The Issue
Copying the loop would have left two runners to fix and two ways to say "a failed stage publishes nothing"; the owner's rule is no duplicates and the epic's purge list is the exit gate.

### The Solution
Generalised the loop first: `src/machine_runner.py` follows whatever state the machine is in, runs the stage that state names, sends `ok`, and records through a small `RunRecord`. The ETL moved onto it (all of its tests passed unchanged) before the sketch package used it; the Jev wrapper and the output-path policy moved to shared modules the same way, in Phase 1.

### The Rule (The "Lesson")
When a second piece of code needs something the first already does, move it to a shared module and port the first onto it before writing the second; the first's existing tests are the proof the move changed nothing.

### References
- **Files:** `src/machine_runner.py`, `src/jev.py`, `src/paths.py`, `docs/sprints/ARCH_SPRINT19.md`

---

## [2026-10-30] A test that two vocabularies agree beats a comment that they should

> **Tags:** #testing #design #Trin

### Context
The checker needs every stage name a sketch may use (`vocabulary.STAGES`); the runner needs the functions (`stages.LIBRARY`). They are two lists of the same names.

### The Issue
Two lists drift: a stage added to one and not the other would pass the check and fail at run time, or the reverse.

### The Solution
One test asserts `set(LIBRARY) - {"blend"} == set(STAGES)`, so adding a stage to only one side fails the build.

### The Rule (The "Lesson")
When two places must list the same names, keep the lists small and add one test that they are equal.

### References
- **Files:** `src/sketch/vocabulary.py`, `src/sketch/stages.py`, `tests/python/test_sketch_coffee.py`
