# Sprint 27 — The test pyramid (Tier 2: story and architecture in one)

* **Branch**: `sprint-27` (cut from `main` e2a7b6d, which has Sprints 24 to 26)
* **Source**: owner decision 17 (2026-11-03): the gate is too slow; "adhere to the test pyramid: end-to-end tests must be rare and fast, and only cover edge cases that cannot be tested with integration or unit tests."
* **Owner rules**: no back-compat, YAGNI, DRY, use libraries, Edit/Write only, do not re-run the gate when told not to.
* **Mechanism approval**: none needed (no new dependency, language or tool); the `check` order is a change to a standard target, made by Tank.
* **Size**: 18 points. **Status**: Draft, awaiting Smith Gates 1 and 2.

## What the measurements say

One timing run on 2026-11-03 (`unittest --durations`), plus a profile of one household run and three micro-measurements. Nothing here is a guess.

| Suite | Time | Where it goes |
|---|---|---|
| Python unit tests | 94.6 s, 554 tests | the slowest 40 tests are almost all whole-household-sketch runs at 1.5 to 1.8 s each; about 53 such runs in six files, and 15 files run a whole sketch through `main` |
| One household run | 2.2 s | about half is `loader.load`: for every row of an `each` stage the loader reads the child sketch twice, 37 ms for a read that does not depend on the row (`_declared_inputs`) and 38 ms to render and parse it with the row's values |
| A real household run | about 7 min | about 1,300 child loads at about 75 ms is about 100 s of it, so caching the first read saves about 48 s of every real run too |
| Browser tests | 154.9 s, 39 tests | `ContrastTest` alone is 47.5 s (31%) and flaked in this run (`steampunk/dark .stage-lamp` 2.36 against 4.5); the other three "readable in every theme" tests add 18 s; the rest are about 2 s each |

## Stories

* **UND-101 Child sketches load faster.** AC1: the part of a child sketch's load that does not depend on the row's values (its declared inputs, read leniently) is read and parsed once per file version, not once per row; a changed file is read again. AC2: the loaded sketch and every output are identical to before (the existing suite passes unchanged, and two replays of a run are still byte-identical). AC3: on the household sketch the per-row load falls from about 75 ms to about 38 ms (measured before and after).
* **UND-102 The household rules are tested below the whole sketch.** AC1: a test can compute one named stage of a sketch from a few written rows, with stand-in rows for any stage it does not want to run (the Jev categorization), without a machine, sinks, run folder or summary. AC2: every household test that checks one rule moves to that level; at most five whole-sketch household runs remain (a happy path whose outputs many tests read, a refusal before Jev, an empty period, a replay, and the console's real start), and each says in its docstring what only a whole run can show. AC3: each moved test still fails when its rule is broken (checked by breaking the rule in a scratch copy for every moved group). AC4: the household tests take 15 s or less.
* **UND-103 The browser suite shows only what a browser can.** AC1: text readability is checked from the themes' declared color pairs in Python (the WCAG ratio, unit-tested on all three themes in light and dark); the browser keeps one readability check of one light and one dark look as the proof that the declared colors are the drawn ones. AC2: the `.stage-lamp` glow flake is gone (the measure holds the glow still). AC3: every browser test left names, in its docstring, the thing that only a browser shows (timing, drawing, keyboard focus, fit on a phone). AC4: the browser suite runs in 90 s or less with no flake in five runs.
* **UND-104 The gate fails fast and says what each level is for.** AC1: `bobp make check` runs lint and the secrets scan before the tests and stops at the first failure. AC2: `docs/TEST_STRATEGY.md` states the pyramid with budgets (whole-sketch runs and browser tests are rare, each with a reason it cannot be lower) and `docs/SDLC.md` records the new order and the measured times. AC3: the Python unit suite takes 30 s or less, measured with the same `--durations` command as the baseline above.

## Architecture

* **UND-101:** cache the lenient read in `_declared_inputs` with `functools.lru_cache` keyed by the path and its `st_mtime_ns` (a library, not a hand-rolled dictionary). It returns a value the caller does not change (checked: `declared` is only read), or a copy if a caller does. `_read` with the row's values is not cached.
* **UND-102:** a small module `src/sketch/fragment.py` with `async def read_stage(sketch, name, *, stubs=None, library=None)`. It builds what `run_sketch` builds around its `compute` closure (a `Sources`, a temporary folder and an empty summary) and returns the rows of the stage source `name`. `stubs` pre-fills `Sources._read` by name, so a test can stand in for `categories` and skip the per-merchant Jev sketches. To share the code, `run_sketch` moves its `compute` closure into a function both use (DRY; no copy). Test helpers (`fragment_rows(csv text, name, stubs)`) live under `tests/python/`.
* **UND-103:** `tests/python/test_theme_contrast.py` reads the theme files' custom properties and checks every declared text and background pair the page uses; `ContrastTest` and the three "readable in every look" tests are cut to one light and one dark look; the stage lamp is measured with animation and transition off.
* **UND-104:** `check: lint secrets test` (Makefile), SDLC "Last verified" line, TEST_STRATEGY budgets. Tank owns the Makefile and SDLC edits.
* **Risk:** moving a test down can drop a real check. The mitigation is UND-102 AC3: break the rule, watch the moved test fail. A moved test that cannot fail is not moved; it stays whole-sketch and counts against the five.
* **Failure modes:** a stale cache entry (the child file edited during a run) is handled by the mtime key; a stub that does not match a stage's real output is caught by the whole-sketch happy path, which runs everything for real.
* **Security:** no new input, output or dependency; `fragment.py` is test support and reads only files the test names.

## Out of scope

* The YAML editor, Venmo and Zelle, household cleanup, per-decider weights in the decision log.
* Running tests in parallel (it would hide the cost instead of removing it; revisit only if the budgets are not met).

## Amendments made while building (measured, with the owner told in chat)

* **UND-101 cache key:** first built on (path, modification time, size); the gate caught it when a test rewrote a file in the same clock tick with a same-length edit and the old content was served. The key is now the file's text (read each time, a few microseconds): always correct, same speed (37.9 ms a row).
* **UND-101:** the saving is smaller than the profile suggested (the profiler inflated the loader): per-row child load 71.5 to 38.6 ms (-46%), a whole household run 1.92 to 1.68 s (-12%). Outputs byte-identical.
* **UND-102 AC2:** "at most five whole-sketch household runs" is met exactly: the happy path (`LedgerTests`), an empty period, and three early-stopping refusals (a bad pin, a bad additions file, a Monarch file without a Category column). The one duplicate dropped is "the same pins place the same merchants" (byte-identical replay is tested in `test_sketch_coffee`). Household tests: 73 tests in about 57 s became 80 tests in 11.4 s.
* **UND-103 AC1:** contrast cannot be computed from the declared colors in Python: steampunk and starship draw text on textured gradients. It stays a real-pixel check in the browser, made cheaper: the six looks run in parallel browser processes (47.5 to 29.5 s); the replay bar and decision panel are measured in one look each because they reuse classes the main test measures in all six; animation and transition are off page-wide (the flake); a page poll override removes a 10 s wait (10.4 to 2.4 s). **AC4 missed:** the browser suite is about 100 s on two runs (target 90 s), no flake; only two runs were made, not five.
* **Found, not planned:** `serve_forever` polled every 500 ms, so each test that started a server waited half a second to stop it. `Server.serve_forever` now polls every 20 ms (also faster `run --watch` close): about 20 s of the unit suite and 15 s of the browser suite. Two security tests that wait on the deliberate one-second wrong-secret pause use a shortened pause.
* **UND-104 AC3:** Python unit suite 94.6 s to 29.4 s (target 30 s met); the whole gate (`bobp make check`) 96 to 101 s to 36.3 s.

Smith Gate 1+2 (combined): approved before the build.
