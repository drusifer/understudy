# UAT Plan: Sprint 19, the coffee proof of concept

* **Owner**: Trin
* **Date**: 2026-10-29
* **Branch**: `sprint-19`
* **Status**: In progress; Phase 2 verified

## 1. Scope

* **User stories covered:** `UND-60` to `UND-67`, verified phase by phase as each is built. Live Jev judgement (UND-67) is verified once at sprint close with the owner's go-ahead.
* **Environment:** CPython 3.12.15, `ruamel.yaml` 0.19.1, `jsonschema` 4.26.0, `python-statemachine` 3.2.2. Invented fixtures only (`tests/fixtures/coffee/`); no private data and no live Jev call before UND-67.
* **Method:** `bobp make test-py ARGS="test_sketch*.py"` (focused) and, at phase gates, `bobp make test-py` and `bobp make lint`.

## 2. Phase 2: load and check a sketch (UND-61)

### `UAT-UND-61-01` The whole sketch is checked
* **Story/AC:** UND-61 AC 1.
* **Command:** `bobp make test-py ARGS="test_sketch*.py"` (`CheckTests`).
* **Expected:** `coffee_week.yaml` and its `weather_change.yaml` subsketch have no problems; a deliberately broken copy of each of these is refused: unknown stage, unknown sink, missing source file, a machine with no final state, a decider that is not a sketch state, a call to a missing subsketch file, a Jev source reading an unknown source, segment shares that do not add up to 1.
* **Result:** Pass. 21 tests, 0 failures; 14 broken-copy cases each report their problem.

### `UAT-UND-61-02` Every mistake names file, path, value and the nearest good one
* **Story/AC:** UND-61 AC 2.
* **Expected:** each message starts with the sketch file, then the path inside it (for example `machine.states.match_orders.blend[0].decide.then.drink[0].size`), then the bad value and, where one exists, `did you mean`.
* **Result:** Pass for the checked cases: `etl.split_by_shar` suggests `etl.split_by_share`, `larg` suggests `large`, `eqq` suggests `eq`, `ingredientz` suggests `ingredients`, `nonee` suggests `none`, `last_wek` is named at `state.last_week.from`.

### `UAT-UND-61-03` An undeclared option never gets through
* **Story/AC:** UND-61 AC 3.
* **Expected:** an option or dimension not in `outcomes` is refused at check time when it is written in the sketch (a leaf row, a `forbid` rule, a subsketch's `returns`).
* **Result:** Pass at check time. The run-time half (a decider whose rows come from a source) is verified in Phase 7 with the weather subsketch, because that is the first stage that reads rows from a source.

### `UAT-UND-61-04` A missing source file stops everything
* **Story/AC:** UND-61 AC 4.
* **Expected:** a missing file source is a problem at `sources.<name>` before any stage; no run folder content or output exists.
* **Result:** Pass at check time (`test_a_missing_source_file_is_refused`). "No output file is created" is verified end to end in Phase 4, when the run folder exists.

### `UAT-UND-61-05` Slices are text, and a bad override is refused
* **Story/AC:** UND-61 AC 5; UND-60 AC 3.
* **Expected:** `70:100` is accepted in a condition and `70:30` stays the text `'70:30'` (PyYAML would make it 4230); `--source` replaces one file for the load only and an undeclared name is refused.
* **Result:** Pass. `data: { band: 70:30 }` loads as `'70:30'`; the override test shows the sketch file is unchanged and a second load sees the original path; `--source salez=...` is refused naming `salez`.

### Phase 2 gate evidence
* `bobp make test-py ARGS="test_sketch*.py"`: `Ran 21 tests ... OK`. `bobp make lint`: ruff clean over `src/sketch` and `tests/python`.
* No live Jev call and no private data.
* `rubric UAT: COVER=A STEPS=A FAIL=A DATA=A EVID=A`.

**Phase 2 UAT verdict: PASSED.**

## 3. Phase 3: decide, blend, forbid (UND-63)

### `UAT-UND-63-01` A tree gives each segment its weighted rows, as written
* **Story/AC:** UND-63 AC 1.
* **Command:** `bobp make test-py ARGS="test_sketch*.py"` (`DecideTests`, `ConditionTests`).
* **Expected:** students reach the 0.5 / 0.2 / 0.3 leaf and the weights are used as written; night workers reach their own leaf; any other segment reaches the else leaf; a branch with no `else` is no opinion.
* **Result:** Pass. Every operator (`eq ne lt le gt ge in not_in has`), `and`/`or`/`not`, several fields meaning `and`, and slices (80 in, 90 out of `80:90`) behave as specified; a field a row lacks never matches.

### `UAT-UND-63-02` A forbid rule drops and renormalises, and always wins
* **Story/AC:** UND-63 AC 2.
* **Expected:** under-18 segments lose every caffeine option; the survivors add up to 1; a rule that does not apply changes nothing.
* **Result:** Pass. `{none: 0.5, high: 0.5}` becomes `{none: 1}` for teens. A grid test over 64 combinations of leaf weights and decider weights never leaves `high` in a teen's caffeine and every dimension adds up to 1.

### `UAT-UND-63-03` An emptied row fails, or opts in to skip or fallback
* **Story/AC:** UND-63 AC 3.
* **Expected:** by default the run fails naming the rule and the segment; `on_empty: skip` removes the dimension; `on_empty: fallback` spreads over the options the rule allows and fails if none is allowed.
* **Result:** Pass. Message: `forbid rule 0 left teens with no option for 'caffeine'`. Found and fixed during build: an option kept with weight 0 caused a division by zero; zero-weight options are now dropped before renormalising.

### `UAT-UND-63-04` Unknown dimension or option in a leaf
* **Story/AC:** UND-63 AC 4.
* **Result:** Pass at check time (Phase 2: `larg` suggests `large`).

### `UAT-UND-63-05` A weight is a number or if/then/else per segment
* **Story/AC:** UND-63 AC 5.
* **Expected:** `0 if night_workers else 0.3` per segment; nested ifs; a missing `else` is 0; no text is parsed.
* **Result:** Pass. Students get the weather nudge (blend of tree and weather by 1 : 0.3), night workers stay on hot coffee exactly (weather weight 0).

### Phase 3 gate evidence
* `Ran 39 tests ... OK` (Phases 2 and 3); ruff clean. Design decisions made during the build and recorded in `DESIGN_SKETCH_MODEL.md`: the blend works per dimension; `walk_away` is not in this sprint's `on_empty` values.
* `rubric UAT: COVER=A STEPS=A FAIL=S DATA=A EVID=A`.

**Phase 3 UAT verdict: PASSED.**

## 4. Phase 4: run the owner's machine (UND-62, UND-60 AC 1-4)

### `UAT-UND-62-01` The machine is the sketch's own, and the loop follows it
* **Story/AC:** UND-62 AC 1, 2.
* **Command:** `bobp make test-py ARGS="test_sketch*.py"` (`MachineTests` on `tests/fixtures/machine_branch.yaml`).
* **Expected:** a transition guarded by an explicit YAML condition (`drinks: { lt: 500 }`) is taken only when it holds, otherwise the next unguarded one; the stage lines show the path taken.
* **Result:** Pass. 100 drinks run `count, quiet, write`; 900 drinks run `count, busy, write`.

### `UAT-UND-62-02` A failed stage publishes nothing and says where it stopped
* **Story/AC:** UND-62 AC 3, 4.
* **Expected:** exit 1 with the stage named, no output file, earlier stage records kept; the run folder records each stage as complete or failed; a failure after the sink also removes the partial output.
* **Result:** Pass. `run.json` shows `status: failed`, `failed_stage: quiet`, `stages: {count: complete}`; the folder holds only `run.json` and `events.jsonl`; a failure in a stage after the sink leaves no `report.jsonl` and no `.part`.

### `UAT-UND-60-01` `understudy run` and `understudy check` on the command line
* **Story/AC:** UND-60 AC 1, 2, 3, 4.
* **Command:** `bobp make test-py ARGS="test_sketch*.py"` (`CliTests`).
* **Expected:** one line per stage then `wrote <file>`; exit 0 on success, 1 when a stage fails, 2 when the sketch or an input is wrong; the last line is one `understudy:` line, never a traceback; `--source <name>.path=<file>` replaces a file for the run only; `check` starts nothing; output under a tracked folder is refused before starting.
* **Result:** Pass. Wrong sketch: exit 2, `did you mean 'report'`, no run folder; missing input: exit 2 naming `sources.numbers`, nothing created; stage failure: `understudy: boom`, exit 1; `--out src/` refused exit 2 with `cannot write`; the override leaves the sketch file unchanged. The command makes no network call (no source kind that reaches the network exists yet).

### Phase 4 gate evidence
* Full suite: `bobp make test-py` `Ran 134 tests ... OK` (the ETL included); ruff clean.
* DRY: the ETL's stage loop and the sketch's are now one, `src/machine_runner.py` (`run_machine`, `RunRecord`); the ETL passes all of its tests on it.
* `rubric UAT: COVER=A STEPS=A FAIL=S DATA=A EVID=A`.

**Phase 4 UAT verdict: PASSED.**
