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
