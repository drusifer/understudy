# Sketches: the reference

A **sketch** is one YAML file in which you write down how you decide something. understudy reads the files you name, runs your rules, and writes the result. Counting and converting are SQL on DuckDB; your judgement is `decide` trees with weights; Jev is used only for a qualitative reading of text you supply, against a rubric you write.

TLDR:
    A sketch names `sources` (files in), `sinks` (files out), `outcomes` (what can be decided), `data` (your facts) and a `machine` (your pipeline).
    Each state in the machine names a stage: ETL, a `blend` of weighted rows, a `sketch.<file>` subsketch, or a `sink`.
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
    do: etl.split_by_share          # a stage
    with: { source: sales, field: drinks, segments: segments }
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

| `do` | `with` | What it does |
|---|---|---|
| `etl.split_by_share` | `source`, `field`, `segments` | splits a total (the sum of `field` over the source's rows) across `data.<segments>` by each segment's `share`: rows `{segment, share, age_min, age_max, drinks}` |
| `etl.join_weights` | `probabilities`, `weights` | joins a Jev source's probability per level with `data.<weights>` (level to option weights) into weighted rows on the dimension the sketch lists in `outputs` |
| `convert.recipes` | `recipes`, `packs` | turns drink counts into ingredient amounts from `data.<recipes>` (rows `{<dimension>: <option>, ingredient, amount, unit}`), rounded up to whole packs from `data.<packs>` |
| `sink.<name>` | | writes the rows of the stage before it to the sink file |
| `sketch.<file>` | | runs `<file>.yaml` beside this one as a nested run and gives back the weighted rows its `outputs` name; `with:` passes it values (see Subsketches) |
| (a state with `blend:`) | | see below |

`understudy check` refuses an unknown stage and suggests the nearest, and checks each `with` key.

## Deciding

A state with `blend:` decides, for every row the stage before it produced (a segment, say), how the outcomes are shared:

```yaml
match_orders:
  blend:
    - decide:                       # your tree; weight defaults to 1
        if: { segment: { eq: students } }
        then:
          drink:                    # a leaf: weighted rows that add up to 1
            - { temp: iced, size: large,  weight: 0.5 }
            - { temp: hot,  size: medium, weight: 0.5 }
        else:
          drink: [ { temp: hot, size: medium, weight: 1.0 } ]
    - from: weather                 # a state that calls a subsketch
      weight:
        if: { segment: { eq: night_workers } }
        then: 0                     # night shift ignores the weather
        else: 0.3
  forbid:                           # hard rules: drop options, always win
    - when: { age_max: { le: 17 } }
      drop: { caffeine: { ne: none } }
  on_empty: fail                    # fail (default), skip, or fallback
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

## Subsketches

`do: sketch.weather_change` runs `weather_change.yaml` from the same folder, sharing the run folder and the sources. It declares what it gives back on its final state:

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
  do: sketch.seating
  with: { tickets: {{ tickets | default(2) }} }   # filled in when the parent is loaded
```

* A child sees only what its call passes; the parent's values are not visible to it.
* A variable with no default and no value fails: `needs a value for 'tickets': pass --with tickets=<value>, or write {{ tickets | default(…) }}`.
* A `--with` or `with` name the receiving file does not use is refused, with the nearest name it does use.
* `understudy check` reads the sketch after Jinja has filled it in.

## Repeating a sketch: `each`

There are no hidden loops: a list given to a source, stage or sketch is one input. To repeat a sketch once per row of a source, say so on the state that calls it:

```yaml
score_films:
  each: films                   # a source: the rows to go through
  do: sketch.review_score       # each only repeats a sketch
  then: rank
```

The row's fields are the child's variables (`{{ title }}`), beside anything the call's `with:` passes. The result is one list of pairs, a row with what the child output for it:

```json
[ { "input": { "title": "It Follows" }, "output": [ { "audience": "loved", "weight": 0.9 } ] }, ... ]
```

Each row's Jev answers are captured under the child's name and the row's position, so a replay needs no live call. `understudy check` reads the child with its row values left empty, so it checks the child's shape, not its values.

## How a run ends

A final state may carry an `outcome:`, a name for the way the run ended:

```yaml
nothing_suits:
  final: true
  outcome: walked_away
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

`understudy check <sketch.yaml>` loads and checks the sketch and starts nothing. It reports every mistake as the file, the path inside it, what is wrong and the nearest valid value, for example `machine.states.split_trade.do: unknown stage 'etl.split_by_shar' (did you mean 'etl.split_by_share'?)`. [schema/decision_sketch.schema.json](../schema/decision_sketch.schema.json) describes the shape for editors.
