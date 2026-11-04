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

---

## [2026-11-01] Command output is copied into the team chat: never print a secret

> **Tags:** #security #tooling #Switch

### Context
The console's access secret was first printed to the terminal when the console started, as the old Node console's token address had been.

### The Issue
`bobp make <target>` captures a command's output and posts its tail to `agents/CHAT.md`, which is tracked and pushed. A secret printed by `bobp make dashboard` would have been published to the repository when the console stopped. (SEC-008; found in Switch's review of the phase, not by a test.)

### The Solution
The secret is saved to a file only its owner can read (`.understudy/dashboard.secret`, mode 0600, git-ignored) and the output names the file. A test asserts the secret never appears in the output and that the file is ignored by git.

### The Rule (The "Lesson")
In this project standard output and error are public. Nothing secret goes to either; save it to an ignored, private file and print where it is.

### References
- **Files:** `src/dashboard/server.py` (`announce`, `save_secret`), `agents/switch/findings/2026-11-01-secret-printed-to-captured-output.md`

---

## [2026-11-01] Look at the real data's shape before you show it

> **Tags:** #privacy #testing #Trin

### Context
The Jev list shows each read's levels and probabilities. The fixtures' levels were words like `much_colder`.

### The Issue
In the owner's real household run, refund candidates are named by a date and an amount. The first version of the list would have sent those to everyone on the network. No unit test could know: the fixtures were invented. Trin saw it by masking the real captures' level names (letters to `a`, digits to `9`) and counting shapes, without reading any value.

### The Solution
Captures record whether their levels come from the owner's data; the list shows `option N` unless the sketch's own words, or the caller holds the secret. The payload of the real run was re-checked: zero levels with a date or an amount.

### The Rule (The "Lesson")
Before a screen shows something drawn from the owner's real files, look at its shape in the real data (masked, as counts) and decide what may leave the machine.

### References
- **Files:** `src/dashboard/reads.py`, `tests/python/test_dashboard_reads.py` (`PrivacyTest`), `agents/switch/findings/2026-11-01-jev-list-shows-transaction-details.md`

---

## [2026-11-01] Check an instrument on an answer you know before you trust what it reports

> **Tags:** #testing #usability #Trin

### Context
UND-80 asked for text contrast of 4.5:1 in every theme and mode. A test measures it from the pixels the browser draws.

### The Issue
The first four versions of the measuring code gave wrong answers: it counted anti-aliased text pixels, then a button's border, then a status dot and a checkbox inside the element as "the background", and once read the text color after hiding the text. Each gave a long list of failures, some real and some not, and the numbers moved when the code changed, not when the page did.

### The Solution
Make the text invisible and stop animations while measuring, screenshot only the element's interior, ignore child controls, read the color first; and, for each surprising figure, save the screenshot and look at it. The final list of 25 real failures was fixed and the test now passes in all six looks.

### The Rule (The "Lesson")
When a new measurement reports something surprising, test the measurement on one case you can judge by eye before changing the thing it measures.

### References
- **Files:** `tests/browser/test_console.py` (`ContrastTest`, `decode_png`, `backdrops`)

---

## [2026-11-01] Open the template and the skill before you write the artifact

> **Tags:** #process #Bob #Cypher

### Context
Sprint 21 and the first drafts of Sprint 22 were written from memory of earlier sprint files.

### The Issue
The stories lacked the template's acceptance-criteria blocks, out-of-scope and open-questions sections and used the retired A/S/W rubric line; no PRD template existed so no PRD did; Cypher's skill steps (Switch and Tank criteria, state, lessons first) were skipped. The owner had to ask three times ("are you using Bob protocol?", "the templates?", "Cypher's skills?") before the process was followed.

### The Solution
Read `agents/templates/<artifact>` and the persona's `SKILL.md` first, every time; write to the template; apply its check before the handoff. A missing template is itself a finding (the PRD template was added).

### The Rule (The "Lesson")
The first tool call for any artifact is reading its template; the first for any persona is reading its skill.

### References
- **Files:** `agents/templates/_template_PRD.md`, `docs/sprints/USER_STORIES_SPRINT22.md`, `docs/sprints/RETRO_SPRINT21.md`

---

## [2026-11-02] Run a new rule against the whole real file, not the account you tuned it on

> **Tags:** #testing #household #Neo #Trin

### Context
Sprint 23 made a record a transfer only when its Monarch Category is `Transfer` or `Credit Card Payment`. The fixture and the Ridgewood account both agreed with the rule, and Ridgewood matched the owner's numbers to the cent.

### Observation and Cause
Outside Ridgewood the same file labels other card payments "Food & Dining: Credit Card Payment" and Venmo "Transportation: Transfers". Those were transfers by the old pairing and stopped being transfers under the new rule: 169 positive records worth $240,596 now count as refunds or credits. Confirmed cause: the rule was checked on the one account the owner cared about; the other accounts were never read.

### Rule
When you change a rule that classifies every record, run it on the whole real file and count what moved between classes per account, not only the figure you were asked to fix.

### Evidence and Scope
- **References:** `docs/sprints/UAT_PLAN_SPRINT23.md` (UAT-23-1, open issue), ADR-0050
- **Applies when:** a rule, threshold or category list changes how many records fall into each class.

---

## [2026-11-02] A criterion that makes existing data unreadable needs the count of what exists

> **Tags:** #design #console #Cypher #Morpheus

### Context
UND-81 AC5 said a log written before the sprint is shown as an unreadable run (the owner's no-back-compat rule). Nothing in the sprint used the new lines yet.

### Observation and Cause
The `.understudy/runs` folder held nine real runs, all without the new lines, so the criterion would have hidden every one of them from the console for no gain until the Sprint 24 diagram needs the story. The criterion was written and approved without counting what was on disk.

### Rule
Before accepting "old shape is unreadable", list what exists in the old shape and what needs the new one; if the new shape has no reader yet, mark the old data (`story: false`) instead of hiding it, and tell the owner.

### Evidence and Scope
- **References:** `docs/sprints/USER_STORIES_SPRINT23.md` (UND-81 AC5, amended), `src/dashboard/view.py` (`story`)
- **Applies when:** a change removes support for an old file or log shape.

---

## [2026-11-02] A style name you reuse may already be styled by a theme

> **Tags:** #console #css #Neo #Trin

### Context
Sprint 24 added a dial, a switch and a fader to the console and named their CSS classes `dial-option`, `switch` and `fader`.

### Observation and Cause
Every theme file still held rules for those exact names from the old console, whose markup was deleted in Sprint 21. They overrode the new colors, and the readability check found the dial text unreadable in the dark looks. Confirmed cause: the old rules were dead code that nothing had removed; the new names matched them by accident.

### Rule
Before naming a new CSS class, search every theme file for it; if a rule exists for a deleted feature, choose another name and put removing the dead rules on the backlog.

### Evidence and Scope
- **References:** `src/dashboard/controls.js`, `src/dashboard/page.css`, `docs/sprints/UAT_PLAN_SPRINT24.md` (UAT-24-5)
- **Applies when:** adding markup to a page with several theme files after a feature was removed.

---

## [2026-11-02] A target that the first rule cannot reach needs a number before it is approved

> **Tags:** #stories #household #Cypher #Smith

### Context
UND-93 said widening the transfer rule to card-side labels would bring positive records outside Ridgewood under $30,000.

### Observation and Cause
Smith checked the target against the last real run before approving: after the label rule, $153,085 remained, mostly five Amex card payments the earlier categorization had labeled as income. The label cannot reach those; the run's own link between the two halves of a payment can. The story was rejected and reworded with both. Confirmed cause: the target was written without a calculation on the real data.

### Rule
When a story states a figure to hit on real data, work the figure out on the real data first and name what reaches it; Smith recomputes it at the gate.

### Evidence and Scope
- **References:** `docs/sprints/USER_STORIES_SPRINT24.md` (UND-93 AC4), ADR-0052
- **Applies when:** a story or criterion contains a number measured on the owner's data.

---

## [2026-11-03] A rule that stops at the first thing that does not fit depends on the order of ties

> **Tags:** #allocation #household #Neo #Trin

### Context
`map.allocate` stopped a payment's list at the first charge that would pass its amount. On the real Amex file two payments (May, July) were 6% and 7% off, while the same rule on the raw file gave 4.6% and 2.8%.

### Observation and Cause
Two inputs differed: merged records carried the bank's date instead of the card's, and charges of one day came in a different order, so a different charge was the one that did not fit. A test with distinct dates could not show either.

### Rule
When a rule stops at the first item that does not fit, sort ties by a stated key (here smallest first) so the answer does not depend on file order, and use the date of the source the rule is about. Run the stage on the real file before the gate.

### Evidence and Scope
- **References:** ADR-0057, `UAT_PLAN_SPRINT25.md` (UAT-25-5)
- **Applies when:** a stage fills a budget from an ordered list.

---

## [2026-11-03] A replay is refused after any change to the sketch

> **Tags:** #replay #testing #Neo

### Context
Replaying a full live run to check a new stage was refused as stale ("the sketch or its rubric changed") after an edit to an unrelated stage's `with`.

### Observation and Cause
A replay reuses Jev's captured answers only for the sketch version that produced them; the first attempt after Phase 5's edits was stale, the next, after a replay-produced run, worked. A live full run costs about 2,300 requests.

### Rule
For a change that does not touch Jev's questions, replay the newest run made after the last sketch edit; if it is refused, run the small sample live (305 requests) and only then the full data.

### Evidence and Scope
- **References:** `docs/USER_GUIDE.md` (replay), Sprint 25 Phases 5 and 6
- **Applies when:** checking a household change against the full baselines.

---

## [2026-11-03] The gate's cheap checks belong before its slow ones, and a chained command hides the first failure

> **Tags:** #gate #testing #Neo #Tank

### Context
`make check` runs the unit tests (about 96 s) and then lint (well under a second). A line-length error was found only after the tests finished, and a follow-on `;`-chained browser run (about 150 s) then printed an older result.

### Observation and Cause
The order puts the slowest step first and the cheapest last, and chaining with `;` lets a later step's output stand in for an earlier failure. Reading the log files' creation and last-write times gave the real durations.

### Rule
Run the cheapest checks first, chain gate steps with `&&`, and read each step's own result before quoting any "OK". When a gate gets slow, measure it from the logs before choosing a fix; the owner's direction is to move checks down the test pyramid (decision 17).

### Evidence and Scope
- **References:** `OWNER_DECISIONS_SPRINT22.md` 17, `UAT_PLAN_SPRINT26.md` (open issues)
- **Applies when:** a gate step fails late, or a command chains several long steps.

---

## [2026-11-03] A browser test found a race a unit test could not: a late frame after PAUSE

> **Tags:** #replay #browser #Neo #Trin

### Context
The replay's PLAY asked the server for the next event on a timer; PAUSE cleared the timer.

### Observation and Cause
A request already in flight when PAUSE was pressed could still land and move the replay on one more event. Only a real page with real timing showed it.

### Rule
Give any asynchronous view a ticket: every new request or stop bumps it, and a response whose ticket is stale is dropped. Keep the browser test that proves it, and keep such tests few and about timing and drawing only.

### Evidence and Scope
- **References:** `src/dashboard/replay.js` (`replay.ticket`), `tests/browser/test_console.py` (`ReplayBarTest`)
- **Applies when:** a page asks for frames, polls, or plays something back.

---

## [2026-11-03] A slow suite is rarely slow where you think: measure it, then read the slowest list for a pattern

> **Tags:** #testing #performance #Neo #Trin

### Context
The gate took 96 s. The first guess was the number of whole-sketch tests, and a profile said half of each run was the YAML loader.

### Observation and Cause
The profiler inflated the pure-Python loader: the real saving from caching it was 12% a run, not 50%. The slowest-tests list showed the real cause by its pattern: about forty tests of exactly 0.5 s, each waiting for `serve_forever` to notice a stop request. Fixing the poll interval saved about 20 s of the unit suite and 15 s of the browser suite, more than the loader work.

### Rule
Time the suite with `--durations`, look for values that repeat (0.5 s, 1.0 s), and fix those first; check a profile's claim with a plain timing before building on it.

### Evidence and Scope
- **References:** `UAT_PLAN_SPRINT27.md` (UAT-27-1), ADR-0060
- **Applies when:** a test run is slow, or a profile points at a library.

---

## [2026-11-03] Moving a test down a level is proved by breaking the rule it guards

> **Tags:** #testing #pyramid #Neo #Trin

### Context
Fifty-three whole-sketch household runs became tests of single stages with written rows.

### Observation and Cause
A moved test can pass for the wrong reason (a stand-in that matches whatever the code does). Breaking the real rule in the sketch file, one rule per group, and watching a moved test fail showed each still guarded its rule; two of the new payments tests also covered things the old ones never checked.

### Rule
Before a test is moved down, break the rule it guards in a scratch change, see the moved test fail, and restore the file from git. A moved test that cannot fail stays whole.

### Evidence and Scope
- **References:** `UAT_PLAN_SPRINT27.md` (UAT-27-2, UAT-27-3)
- **Applies when:** replacing an end-to-end test with a smaller one.

---

## [2026-11-04] A cache keyed on a file's modification time can serve stale content; key it on the content

> **Tags:** #cache #testing #Neo

### Context
Sprint 27 cached the row-independent read of a sketch by (path, modification time, size). The first push after the merge failed the gate: a test rewrote a file in the same clock tick with an edit of the same length (`mood` to `tone`), and the old content came back.

### Observation and Cause
Two writes in one timestamp tick share a modification time, and a same-length edit shares the size. My own "edited file is read again" test passed earlier only because the writes happened to land in different ticks.

### Rule
Key a cache of a file on what it holds (the text, read each time: microseconds), not on its timestamp. Write the test that forces the collision (same length, modification time set back) before trusting the key, and run the gate before a merge, not only the focused suites.

### Evidence and Scope
- **References:** `tests/python/test_loader_cache.py`, `src/sketch/loader.py` (`_shared_template`), `STORY_ARCH_SPRINT27.md` (amendments)
- **Applies when:** caching anything derived from a file.
