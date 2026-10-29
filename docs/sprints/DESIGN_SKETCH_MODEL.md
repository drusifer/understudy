# Design: the sketch model for the Python port

* **Status**: AGREED with the owner in conversation, 2026-10-29. Not yet reviewed by Smith/Morpheus; not built. Basis of the Python port epic (`EPIC_PYTHON_PORT.md`) and of the coffee proof of concept.
* **Rules**: no back-compat, YAGNY, DRY, no new language (SQL on DuckDB; `python-statemachine` YAML), Jev chooses and never writes.

## 1. What changed in our thinking

* **There is no single state machine for all sketches.** Users build and compose their own state machines for the task at hand. The old built-in `turn:` machine (tags, invoke/onDone, the look/play loop) goes away; Spike 1 (`SPIKE_PYTHON_STATEMACHINE.md`) found those features do not map onto python-statemachine, and nothing needs them now.
* **The main loop is plain Python.** It feeds sources to the user's machine as events and runs the step the current state names. No built-in loop machine (YAGNY).
* **Understudy is a platform for automation, not a chat bot.** A sketch models a decision the way the owner of the shop would make it.

## 2. Division of labour

| Role | Does | Where it lives |
|---|---|---|
| Machine | control flow: which stage runs next, branching on the data | the sketch's `machine` (python-statemachine YAML) |
| ETL and SQL | quantitative analysis: counts, trends, adjacency, conversions | stages (`etl.*`, `convert.*`), DuckDB |
| `decide` trees | the owner's deterministic logic | `decide:` (if / then / else, SQL conditions) |
| Weights | how much each decider or source counts, as expressions over properties of its input | `weight:` |
| Jev | qualitative judgement only: picks one of the owner's listed options, or gives probabilities | `ask:` nodes |

Jev never produces an amount. Its probabilities become weights, and the owner's rules decide what they mean.

## 3. The decider contract

**One row in, rows out.** Each output row is a full combination of outcome values plus a `weight`; the weights for one input row sum to 1.

```jsonl
{"temp": "iced", "size": "large",  "milk": "oat",   "weight": 0.30}
{"temp": "iced", "size": "medium", "milk": "oat",   "weight": 0.24}
{"temp": "hot",  "size": "medium", "milk": "whole", "weight": 0.46}
```

* **Outcomes are declared** by the sketch; a decider cannot invent a key. Unknown dimension or option is an error naming the decider, the bad key and the nearest valid one. Missing option means weight 0.
* **A dimension is either an enumeration** (`temp: [hot, iced]`; a boolean is a two-option list) **or discrete numeric steps** (`sugar_spoons: { range: [0, 3], step: 1 }`, which expands to a list). No free-form number, no free text.
* **Candidates may come from source rows** instead of a fixed list (`outcomes: { showing: { from: showings, key: id } }`); the keys are then read at run time and still checked.
* **Everything implements the same contract:** a `decide` tree (its leaf is the weights), an ETL lookup (history), a subsketch (weather), and Jev's `ask` (its probabilities).
* **One combination rule: the weighted blend.** The engine runs each decider, takes the weighted average of their rows (weights normalised) and goes on. Example: history says iced 0.30 (weight 0.8), weather 0.90 (0.3), the owner's rule 1.00 (0.2); the blend is 0.54 iced, so 40 students give about 22 iced and 18 hot.
* **There is no scoring formula.** The old evening engine multiplied `position ^ weight` factors (ADR-0018, ADR-0030); that is dropped. Vetoes are explicit `if`/`else` filters the owner can read, not hidden zeros.
* **Ordered lists and slices:** a list is always an order, first is best, and its position scores `(n - i) / n` (E, F, D give 1, 0.67, 0.33; unlisted 0). An interval is a Python-style slice written as a **quoted** string (`"70:100"`, `"0.3:1"`; unquoted `70:100` is a base-60 number in YAML 1.1), scored linearly and clamped, either direction. These give a leaf its weight.

## 4. Filtering and empty results

* A filter is a SQL condition that drops rows. It can sit on the input rows, on a decider's output (`forbid`), or on the aggregate (`where expected_count >= 1`).
* After a `forbid`, the surviving weights are renormalised. `forbid` always wins over a preference.
* **If a filter empties every row for an input row, the run fails** (default), naming the rule and the input row. The owner can opt in per stage to `on_empty: fallback` (a default row), `skip` (the row adds nothing) or `walk_away` (finish successfully with outcome `none`).

## 5. Sources, sinks, subsketches

* **Sources and sinks are named in the sketch**, with `kind`, `path`/`server` and `params` in place. **No separate `bind` section and no `extends`.** Every kind implements `describe()` and `read(params)` (JSONL, paged); a sink implements `write(params, jsonl)`. The Sprint 17 MCP source servers are the first instance.
* **Sources are read-only.** A side effect (booking, a hold) is a stage `do:`, never a source.
* **Defaults:** a bare path is a JSONL file; each `kind` supplies its own defaults; a source may default its params and a caller overrides only what differs. A required value with no sensible default fails with a clear error.
* **Tests override sources from the command line** (`--source customers.path=fixtures/x.jsonl`); the sketch file does not change.
* **A subsketch** has its own inputs, sources and outputs. The parent passes inputs with `with:` and sees only the named outputs. **A subsketch's inputs appear on the dashboard only if the parent lists them** (`expose: [row, centre]`); the author of the parent decides.
* **Data gaps** are filled by exposing more from the source or by an ETL stage (for example adjacent free seats from a seat map, in SQL).

## 6. Worked example: weekly coffee ingredients (the proof of concept)

The owner's logic: (1) count last week's customers by type; (2) match types to preferred orders with `decide` logic (under 18 gets no caffeine); (3) convert probable orders to ingredient counts and output. A `weather_change` subsketch compares next week's weather with last week's and feeds the hot versus iced shift.

### `weather_change.yaml` (subsketch)

```yaml
name: weather_change
description: Next week's weather compared with the previous week's.

inputs:
  place: text

sources:
  next:
    kind: mcp
    server: ./weather_server
    params: { place: inputs.place, week: next }
  previous:
    kind: mcp
    server: ./weather_server
    params: { place: inputs.place, week: previous }

machine:
  initial: compare
  states:
    compare:
      do: etl.week_over_week      # SQL over both sources
      then: done
    done:
      final: true
      outputs: [forecast, diff]
```

### `coffee_week.yaml`

```yaml
name: coffee_week
description: From last week's customers, work out what to order for next week.

sources:
  customers: last_week_customers.jsonl

sinks:
  ingredients:
    kind: file
    path: out/ingredients.jsonl

outcomes:
  temp:     [hot, iced]
  size:     [small, medium, large]
  caffeine: [none, regular, high]

data:
  place: Burlington VT
  recipes:
    - { when: "size = 'medium'", ingredient: coffee_beans, amount: 18, unit: g }
  packs:
    coffee_beans: 1000

questions:
  customer_type:
    choose: [commuter, student, night_worker, other]
    instructions: Which of these best describes this customer?

machine:
  initial: weather
  states:
    weather:
      do: sketch.weather_change
      with: { place: data.place }
      then: count_customers

    count_customers:
      do: etl.count_by_type
      transitions:
        - if: customers < 20
          to: quiet_week
        - to: match_orders

    quiet_week:
      do: etl.repeat_last_week
      then: to_ingredients

    match_orders:
      decide:
        if: age < 18
        then:
          drink: { size: small, caffeine: none }
        else:
          if: job in ('nurse', 'driver')
          then:
            drink: { size: large, caffeine: high }
          else:
            ask: customer_type
            then:
              commuter:     { drink: { size: medium, temp: hot } }
              student:      { drink: { size: large, temp: iced } }
              night_worker: { drink: { size: large, temp: hot } }
              other:        { drink: { size: medium } }
      forbid:
        - when: age < 18
          drop: "caffeine <> 'none'"
      evidence:
        history:
          weight: 0.8 if weeks >= 4 else 0.4
        weather:
          weight: 0.3 if weather.diff.avg_high > 5 else 0.0
      then: to_ingredients

    to_ingredients:
      do: convert.recipes
      rounding: { pack: data.packs }
      then: write

    write:
      do: sink.ingredients
      then: done

    done:
      final: true
```

## 7. The evening example in this model

* `gates` become filters; the evenings switch stays as a `when:`. `scores` become deciders whose leaves take weights from ordered lists and slices. `shortlist` keeps the top 5 by blended weight. `pick` is a final `ask`. `target`, `calls` and `turn:` are gone.
* **Seating is a subsketch** (`seating.yaml`): inputs `showing`, `tickets`, `row`, `centre`; a read-only `seats` source; an ETL stage that turns the seat map into candidate blocks of adjacent free seats at least `tickets` long; a `decide` stage; a final `ask`; a `reserve` stage that is the only side effect; outputs the `hold`. The parent pays only with `hold: seating.hold`, so Jev can never pay for something it invented. A subsketch that finds nothing finishes with outcome `none`, and the parent routes that to `walk_away`.

## 8. Open questions

* The `evidence:` / `weight` syntax and how the blend is stated in a stage (the example above is a placeholder).
* How a subsketch names and exposes its outputs to the parent (`weather.diff...`, `outputs:` are guesses).
* Whether `next:` (an outcome that also continues to another test) is needed, or a leaf always ends its branch.
* Which condition language: SQL expressions over named fields (assumed) versus something smaller; how `ask` branches are written.
* Event payloads: confirm the Python loop can pass a stage's result to guards (Spike 1, open item 2).
* How the other old examples (cli, http, web, mcp) translate; they are slice B, after the proof of concept.
