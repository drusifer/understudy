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
