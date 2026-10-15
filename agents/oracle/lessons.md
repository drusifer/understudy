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
