# Sketches: the reference

A **sketch** is one YAML file in which you write down how you decide something. understudy reads the files you name, runs your rules, and writes the result. Counting and converting are SQL on DuckDB; your judgement is `decide` trees with weights; Jev is used only for a qualitative reading of text you supply, against a rubric you write.

TLDR:
    A sketch names `sources` (files in), `sinks` (files out), `outcomes` (what can be decided), `data` (your facts) and a `machine` (your pipeline).
    Each state in the machine names a stage with `do:` (a `map` action, a `reduce` action such as `blend`, a `sketch` file, or a `sink`).
    A decide tree, lookup, subsketch or Jev reading produces weighted rows; `blend` is a weighted average per dimension; `forbid` drops options and always wins.
    Conditions are plain YAML: `segment: { eq: students }`, `temp: { in: [80:90] }`, `and` / `or` / `not`.
    Jev is a source: `kind: jev` with a rubric (`instructions` + `criteria`) and the `state` it reads; reading it gives a probability per level.
    Every non-file read is captured; `--replay` runs offline from the capture. `understudy check` finds mistakes before anything runs.
    Worked example: `tests/fixtures/coffee/coffee_week.yaml` and `weather_change.yaml`. Design notes: `docs/sprints/DESIGN_SKETCH_MODEL.md`.

## The file

```yaml
name: coffee_week                  # required
description: ...                   # optional

sources:                           # what goes in; every one is read-only
  sales: last_week_sales.jsonl     # a bare path is a JSONL file, relative to this file
sinks:                             # what comes out: a file name inside the run folder
  ingredients: ingredients.jsonl
outcomes:                          # what can be decided: dimension -> its options
  temp: [hot, iced]
  size: [small, medium, large]
data:                              # your facts: anything the stages read by name
  segments: [ { name: students, share: 0.30, age_max: 24 }, ... ]
machine:                           # your pipeline
  initial: weather
  states: { ... }
```

Paths are relative to the sketch file. `--source <name>.path=<file>` replaces one file source for a single run; the sketch file is not changed.

## The machine

A state is final (`final: true`) or names one stage and where to go next:

```yaml
states:
  split_trade:
    do: { map: { action: split_by_share } }   # the stage: a type, and which one
    with: { source: sales, field: drinks, segments: segments }   # its params
    then: match_orders              # the next state
  count:
    do: ...
    transitions:                    # or: the first matching transition wins
      - if: { drinks: { lt: 500 } } # a condition over the stage's result
        to: quiet_week
      - to: busy_week               # no `if` means always
```

The machine is a python-statemachine; the loop runs the stage each state names and the machine picks the next state. A failed stage ends the run and publishes nothing. A state is checked to exist, and every state must be able to reach a final one.

### Stages

A state's `do:` names a stage **type** as a key (a closed set the schema owns) and says which one with that type's one field. Names and files are always values, never keys. `with:` sits beside `do:` for every type and passes its params.

| `do:` | field | meaning |
|---|---|---|
| `map` | `action` | rows in, rows out: a library operation written in Python with `@stage` (below) |
| `reduce` | `action` | many rows to fewer (`blend`, `max`, `min`), written the same way |
| `sink` | `name` | write the rows of the previous stage to a declared sink |
| `sketch` | `file` | run another sketch (`<file>.yaml` beside this one) |

| `do:` | `with` | What it does |
|---|---|---|
| `map: { action: split_by_share }` | `source`, `field`, `segments` | splits a total (the sum of `field` over the source's rows) across `data.<segments>` by each segment's `share`: rows `{segment, share, age_min, age_max, drinks}` |
| `map: { action: join_weights }` | `probabilities`, `weights` | joins a Jev source's probability per level with `data.<weights>` (level to option weights) into weighted rows on the dimension the sketch lists in `outputs` |
| `map: { action: recipes }` | `recipes`, `packs` | turns drink counts into ingredient amounts from `data.<recipes>` (rows `{<dimension>: <option>, ingredient, amount, unit}`), rounded up to whole packs from `data.<packs>` |
| `map: { action: where }` | `source`, `keep` | the rows that satisfy the condition `keep` (the same explicit conditions as everywhere) |
| `map: { action: join }` | `source`, `other`, `on`, `other_on` | each row plus the fields of the row of `other` whose `other_on` (default `on`) equals its `on`; a row with no match is dropped |
| `map: { action: expect }` | `probabilities`, `values`, `into` | one row `{<into>: number}`: your numbers per level (`data.<values>`) averaged by a Jev reading's probabilities |
| `map: { action: unpair }` | `source` | flat rows from an `each` result: each `{input, output}` pair becomes the input row plus each row it output |
| `map: { action: adjacent_runs }` | `source`, `group`, `order`, `length`, `match` | every run of `length` consecutive `order` numbers in a `group`, from the rows that `match` (E3 E4 E5 gives E3-4 and E4-5 for 2): `{<group>, first, last, run}` |
| `map: { action: prefer_order }` | `rows`, `field`, `order`, `into` | adds `into`: 1.0 for the first value of `order`, less for the next, 0 for one not listed |
| `map: { action: prefer_middle }` | `rows`, `extent`, `group`, `order`, `into`, `match` | adds `into` to runs: 1.0 centered in their group, 0.0 at its end |
| `map: { action: weigh }` | `source`, `by`, `into` | adds `into`: the sum of the `by` fields, each times its weight |
| `reduce: { action: max }`, `min` | `source`, `field`, `take` | the `take` rows (default 1) with the highest (lowest) `field`, best first |
| `reduce: { action: any }` | `source` | one row, `{any: true}` if the source has any row, `{any: false}` if none (for a guard) |
| `sink: { name: <sink> }` | | writes the rows of the stage before it to the sink file |
| `sketch: { file: <file> }` | | runs `<file>.yaml` beside this one as a nested run and gives back the weighted rows its `outputs` name; `with:` passes it values (see Subsketches) |
| `reduce: { action: blend }` | `entries`, `forbid`, `on_empty`, `shortlist` | see Deciding, below |

`understudy check` refuses an unknown stage and suggests the nearest, and checks each `with` key.

## Deciding

`blend` is a **reduce** stage: it takes weighted entries and reduces them to one distribution per row the stage before it produced (a segment, say), sharing out the outcomes:

```yaml
match_orders:
  do: { reduce: { action: blend } }
  with:
    entries:
      - decide:                     # your tree; weight defaults to 1
          if: { segment: { eq: students } }
          then:
            drink:                  # a leaf: weighted rows that add up to 1
              - { temp: iced, size: large,  weight: 0.5 }
              - { temp: hot,  size: medium, weight: 0.5 }
          else:
            drink: [ { temp: hot, size: medium, weight: 1.0 } ]
      - from: weather               # a state that calls a subsketch
        weight:
          if: { segment: { eq: night_workers } }
          then: 0                   # night shift ignores the weather
          else: 0.3
    forbid:                         # hard rules: drop options, always win
      - when: { age_max: { le: 17 } }
        drop: { caffeine: { ne: none } }
    on_empty: fail                  # fail (default), skip, or fallback
  then: to_ingredients
```

* **Weighted rows** come from one input row. A row names only the dimensions it has an opinion on.
* **The blend** averages each dimension over the entries that name it, weighted by the entry's `weight` (a number, or `if`/`then`/`else`; a missing `else` is 0). A weight of 0 means no say.
* **`forbid`** drops the options a matching rule forbids and renormalises. If that leaves a row with no option in a dimension, the run fails naming the rule and the row, unless the stage says `on_empty: skip` (drop that dimension) or `fallback` (spread over the allowed options).
* Options must be declared under `outcomes`; the checker refuses a typo and suggests the nearest, and the run checks rows that came from a source.

### Conditions

```yaml
segment: { eq: students }            # eq ne lt le gt ge
job:     { in: [nurse, driver] }     # in not_in: a list ...
temp:    { in: [80:90] }             # ... or a slice: 80 included, 90 excluded
merchant: { has: coffee }            # has: the field contains the value (text or list)
or:                                  # and or not combine; several fields in one mapping mean and
  - { genre: { eq: horror }, tomato: { ge: 70 } }
  - { tomato: { gt: 90 } }
```

`lt le gt ge` order numbers, and also dates, times and datetimes, which [dateparser](https://dateparser.readthedocs.io) reads from text: `starts: { ge: "17:00" }` keeps a showing at `"19:30"` and drops one at `"15:00"`, and `on: { lt: "2026-11-01" }` compares dates. A bare time is placed on a fixed day, so a time is always compared as a time.

A field a row does not have never matches. A condition compares a field with a fixed value, never with another field. Sketches are read as YAML 1.2, so `70:30` stays text.

## Jev

Jev only chooses among options you list and gives probabilities; it never writes values. Ask it through a source:

```yaml
sources:
  weather_change:
    kind: jev
    question: choice
    instructions: Compare next week's description with last week's. How much warmer or colder is next week?
    criteria:                        # the rubric: each level and what it means
      much_colder: Clearly and markedly colder than last week.
      colder: Noticeably cooler.
      same: About the same.
      warmer: Noticeably milder.
      much_warmer: Clearly and markedly warmer.
    state:                           # the data Jev reads, from other sources
      last_week: { from: last_week }
      next_week: { from: next_week }
```

Reading it returns one row per level, `{level, probability}`. Your weights per level live in `data`, and Jev never sees them. A live read needs `TYPESAFE_API_KEY`.

## A stage as a source

A source is a named set of rows. Besides a file and a Jev reading, a source can be **computed by a stage** (`kind: stage`), declared with the same `do:` and `with:` a state has:

```yaml
sources:
  seats: seats.jsonl
  runs:
    kind: stage
    do: { map: { action: adjacent_runs } }
    with: { source: seats, group: row, order: number, length: 2, match: { free: true } }
```

A source can also be a sketch repeated per row: `scored: { kind: stage, do: { sketch: { file: review_score } }, each: films }` is the list of `{input, output}` pairs (see `each`), ready for `map.unpair`.

Anything that reads `runs` by name (another stage's `source:`, a Jev source's `state:`, an outcome's `{ from, key }`) triggers it. It runs once, on the first read, and the rows are remembered. Only `map` and `reduce` stages can compute a source. `understudy check` refuses a source that reads itself, an unknown action, and a `source:` param that names no source. Stage sources are deterministic, so only Jev readings are captured for a replay.

## Subsketches

`do: { sketch: { file: weather_change } }` runs `weather_change.yaml` from the same folder, sharing the run folder and the sources. It declares what it gives back on its final state:

```yaml
done:
  final: true
  outputs: [temp]                    # the outcome it gives weights on
```

The parent names it in a `blend` (`from: weather`, the state that calls it). The checker refuses an output the parent has not declared under `outcomes`.

Any sketch can be run on its own or called by another, and one sketch can be called many times.

## Values in: Jinja2 and `with`

Every sketch file is a Jinja2 template over standard YAML 1.2; a file with no `{{ }}` or `{% %}` reads as it always did. A value comes from the command line (`--with`), or from a calling state's `with:`, and the file writes its own default:

```yaml
- when: { length: { lt: {{ tickets | default(2) }} } }
```

```sh
understudy run evening.yaml --with tickets=3
```

```yaml
seat:
  do: { sketch: { file: seating } }
  with: { tickets: {{ tickets | default(2) }} }   # filled in when the parent is loaded
```

* A child sees only what its call passes; the parent's values are not visible to it.
* A variable with no default and no value fails: `needs a value for 'tickets': pass --with tickets=<value>, or write {{ tickets | default(…) }}`.
* A `--with` or `with` name the receiving file does not use is refused, with the nearest name it does use.
* `understudy check` reads the sketch after Jinja has filled it in.

## Adding a stage

A stage is one Python function, registered with `@stage`. Its signature is the contract of the YAML, so there is nothing else to keep in step:

```python
@stage("map.split_by_share")
async def split_by_share(context, source: Source, field: str, segments: Data) -> list[dict]: ...
```

```yaml
do: { map: { action: split_by_share } }
with: { source: sales, field: drinks, segments: segments }
```

* Each parameter after `context` is a `with:` key; one with no default is required.
* The annotation says what the value is: `Source` names a source of the sketch, `Data` names a key under `data`, and `str`, `int` or `float` is a plain value.
* `understudy check` reads the same signature, so a missing, unknown or wrongly typed `with:` key is refused before anything runs, with the nearest valid name.
* The function returns rows; the next stage reads them as `context.last`.

## Options that exist only in data

An outcome's options are normally listed. When they exist only in a file, say where to read them:

```yaml
outcomes:
  showing: { from: showings, key: title }      # the title of every row of the `showings` source
```

A weighted row may name any of those titles; one the file does not have is refused with the nearest (`showing='Alein', not a declared option (did you mean 'Alien'?)`). A `blend` can keep only its best few options, and Jev can then choose among them:

```yaml
rank:
  do: { reduce: { action: blend } }
  with:
    entries: [ ... ]
    shortlist: 5                                # keep the five heaviest options per outcome
pick:
  kind: jev
  question: choice
  instructions: Choose the showing you would enjoy most.
  options: { from: ranked, key: title }         # the `title` of every row of the source `ranked` (a file or a stage source)
  state: {}
```

Only the shortlisted options are offered to Jev, so its answer can only be one of them. `{ from, key }` is written the same way both times.

## Repeating a sketch: `each`

There are no hidden loops: a list given to a source, stage or sketch is one input. To repeat a sketch once per row of a source, say so on the state that calls it:

```yaml
score_films:
  each: films                   # a source: the rows to go through
  do: { sketch: { file: review_score } }   # each only repeats a sketch
  then: rank
```

The row's fields are the child's variables (`{{ title }}`), beside anything the call's `with:` passes. The result is one list of pairs, a row with what the child output for it:

```json
[ { "input": { "title": "It Follows" }, "output": [ { "audience": "loved", "weight": 0.9 } ] }, ... ]
```

Each row's Jev answers are captured under the child's name and the row's position, so a replay needs no live call. `understudy check` reads the child with its row values left empty, so it checks the child's shape, not its values.

## How a run ends

A guard (`if:` on a transition) tests the fields of a stage's result when that result is a mapping or a **single row**, which is what a scalar reducer such as `reduce.any` returns. So a sketch can route on "is there anything?":

```yaml
found:
  do: { reduce: { action: any } }
  with: { source: scored }
  transitions:
    - if: { any: { eq: false } }
      to: nothing_fits
    - to: best
```

A final state may carry an `outcome:`, a name for the way the run ended:

```yaml
nothing_fits:
  final: true
  outcome: none
```

The run still exits 0. It records the outcome in `run.json` and the last event, and prints `outcome: walked_away` as its last line.

## Capture and replay

Every live read of a non-file source (Jev today) is captured, after it completes, under `.understudy/cache/<run-id>/` (git-ignored; the last 5 runs are kept). `--replay` runs from the capture and never goes live: no key, no network.

```sh
understudy run coffee_week.yaml                       # live; captures
understudy run coffee_week.yaml --replay              # the latest run that captured every non-file source
understudy run coffee_week.yaml --replay=<run-id>     # a named run
understudy run coffee_week.yaml --replay=tests/fixtures/coffee/replay   # a folder of captures
```

A replay says so on its first line (`replay: reading captures from <folder>, no live calls`). If no run covers every source, it stops and names the missing one. If the sketch or rubric changed since the capture, the run prints one line and records `stale: true`, and carries on. `summary.json` records `mode` (`live` or `replay`).

## What a run writes

`build/runs/run-<stamp>-<id>/`, or the folder you give with `--out` (refused under `data/` or any tracked folder):

* your sink files, written last, so a failed run publishes none;
* `summary.json`: counts only (total, per segment, the shares, the weather weights, Jev requests, `mode`, `stale`);
* `run.json` (each stage complete or failed), `events.jsonl` (one JSON line per run event), `run.duckdb`.

Exit codes: 0 done, 1 a stage failed after the run started, 2 refused before starting (a wrong sketch, a missing file, a missing key, a replay with nothing to replay). Every failure ends with one `understudy: <message>` line, never a traceback.

## Checking

`understudy check <sketch.yaml>` loads and checks the sketch and starts nothing. It reports every mistake as the file, the path inside it, what is wrong and the nearest valid value, for example `machine.states.split_trade.do.map.action: unknown stage 'map.split_by_shar' (did you mean 'map.split_by_share'?)`. [schema/decision_sketch.schema.json](../schema/decision_sketch.schema.json) describes the shape for editors.
