# Design: the sketch model for the Python port

* **Status**: AGREED with the owner in conversation, 2026-10-29. Not yet reviewed by Smith/Morpheus; not built. Basis of the Python port epic (`EPIC_PYTHON_PORT.md`) and of the coffee proof of concept.
* **Rules**: no back-compat, YAGNY, DRY, no new language (SQL on DuckDB; `python-statemachine` YAML), Jev chooses and never writes.

## 1. What changed in our thinking

* **There is no single state machine for all sketches.** Users build and compose their own state machines for the task at hand. The old built-in `turn:` machine (tags, invoke/onDone, the look/play loop) goes away; Spike 1 (`SPIKE_PYTHON_STATEMACHINE.md`) found those features do not map onto python-statemachine, and nothing needs them now.
* **The main loop is plain Python.** It feeds sources to the user's machine as events and runs the step the current state names. No built-in loop machine (YAGNY).
* **Understudy is a platform for automation, not a chat bot.** A sketch models a decision the way the owner of the shop would make it.
* **The owner knows how to decide.** The sketch lets them write their deterministic logic down; ETL and weights do the quantitative analysis; Jev is saved for qualitative assessment.

## 2. Division of labour

| Role | Does | Where it lives |
|---|---|---|
| Machine | control flow: which stage runs next, branching on the data | the sketch's `machine` (python-statemachine YAML) |
| ETL and SQL | quantitative analysis: totals, splits, adjacency, conversions | stages (`etl.*`, `convert.*`), DuckDB |
| `decide` trees | the owner's deterministic logic | `decide:` (if / then / else, SQL conditions) |
| Weights | how much each decider or source counts, as expressions over properties of its input | `weight:` |
| Jev | qualitative judgement only: reads supplied text against a rubric and picks a level, or picks one of the owner's listed options | `ask:` / `score:` nodes |

Jev never produces an amount. Its probabilities become weights, and the owner's rules decide what they mean.

**A Jev step is worth having only if** (a) it reads text or other material the sketch supplies (it has no memory of the shop), and (b) it answers against a rubric of defined levels. Ideas that failed this test and are not in the PoC: local events with no rubric, "how much would students like the special" (no data to ground it). A possible later use: a source of customer feedback comments, judged per drink on a four-level rubric, nudging that drink's weight.

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
* **Everything implements the same contract:** a `decide` tree (its leaves carry weights), an ETL lookup, a subsketch, and Jev's `ask` (its probabilities).
* **One combination rule: the weighted blend.** The engine runs each decider, takes the weighted average of their rows (weights normalised) and goes on. Example: one source says iced 0.30 (weight 0.8), another 0.90 (0.3), the owner's rule 1.00 (0.2); the blend is 0.54 iced.
* **There is no scoring formula.** The old evening engine multiplied `position ^ weight` factors (ADR-0018, ADR-0030); that is dropped. Vetoes are explicit `if`/`else` filters the owner can read, not hidden zeros.
* **Ordered lists and slices:** a list is always an order, first is best, and its position scores `(n - i) / n` (E, F, D give 1, 0.67, 0.33; unlisted 0). An interval is a Python-style slice written as a **quoted** string (`"70:100"`, `"0.3:1"`; unquoted `70:100` is a base-60 number in YAML 1.1), scored linearly and clamped, either direction. These give a leaf its weight.

## 4. Filtering and empty results

* A filter is a SQL condition that drops rows. It can sit on the input rows, on a decider's output (`forbid`), or on the aggregate (`where expected_count >= 1`).
* After a `forbid`, the surviving weights are renormalised. `forbid` always wins over a preference.
* **If a filter empties every row for an input row, the run fails** (default), naming the rule and the input row. The owner can opt in per stage to `on_empty: fallback` (a default row), `skip` (the row adds nothing) or `walk_away` (finish successfully with outcome `none`).

## 5. Sources, sinks, subsketches

* **For this epic every source and sink is a file** (owner, 2026-10-29). `kind: mcp` (and http) are designed for but not built; the interface below is what a later kind implements. The weather inputs are files (last week's observations, the pasted Almanac text).
* **Sources and sinks are named in the sketch**, with `kind`, `path`/`server` and `params` in place. **No separate `bind` section and no `extends`.** Every kind implements `describe()` and `read(params)` (JSONL, paged); a sink implements `write(params, jsonl)`. The Sprint 17 MCP source servers are the first instance.
* **Sources are read-only.** A side effect (booking, a hold) is a stage `do:`, never a source.
* **Defaults:** a bare path is a JSONL file; each `kind` supplies its own defaults; a source may default its params and a caller overrides only what differs. A required value with no sensible default fails with a clear error.
* **Tests override sources from the command line** (`--source sales.path=fixtures/x.jsonl`); the sketch file does not change.
* **A subsketch** has its own inputs, sources and outputs. The parent passes inputs with `with:` and sees only the named outputs. **A subsketch's inputs appear on the dashboard only if the parent lists them** (`expose: [row, centre]`); the author of the parent decides.
* **Data gaps** are filled by exposing more from the source or by an ETL stage (for example adjacent free seats from a seat map, in SQL).

## 6. Worked example: weekly coffee ingredients (the proof of concept)

The shop owner has only **last week's total sales**, not customer histories, and works from **rough demographics**: groups of customers with a share of the trade. The owner's logic: (1) split the expected drinks by segment; (2) match each segment to the drinks it prefers, as weighted leaves of a `decide` tree, with hard rules such as no caffeine under 18; (3) convert the expected drinks to ingredient counts and output. A `weather_change` subsketch has Jev read the Farmers' Almanac forecast against last week's observed weather and report how much warmer or colder next week will be; that shifts the hot/iced weights.

### `weather_change.yaml` (subsketch)

```yaml
name: weather_change
description: How much warmer or colder next week will be than last week.

inputs:
  place: text

sources:
  last_week: last_week_weather.jsonl  # what the weather actually was: {"day": "Mon", "high": 48, "low": 36, "rain": "none"}
  almanac:                            # what is forecast for next week
    kind: file
    path: next_week_almanac.jsonl     # {"week": "2026-W44", "text": "Chilly and damp, with a hint of snow late in the week."}

questions:
  change:
    score: almanac
    facts: last_week                  # Jev sees last week's numbers alongside the forecast text
    instructions: >
      Compared with last week, how much warmer or colder does this forecast say next week will be?
    levels:
      - Much colder
      - A little colder
      - About the same
      - A little warmer
      - Much warmer

machine:
  initial: judge
  states:
    judge:
      ask: change
      then: done
    done:
      final: true
      outputs: [temp_shift]           # expected level -> how far demand moves between hot and iced
```

### `coffee_week.yaml`

```yaml
name: coffee_week
description: >
  From last week's total sales and a rough picture of who the customers are,
  work out what to order for next week.

sources:
  sales: last_week_sales.jsonl        # one row: {"week": "2026-W43", "drinks": 1200}

sinks:
  ingredients:
    kind: file
    path: out/ingredients.jsonl       # {"ingredient": "coffee_beans", "amount": 3000, "unit": "g"}

outcomes:
  temp:     [hot, iced]
  size:     [small, medium, large]
  caffeine: [none, regular, high]

data:
  place: Burlington VT
  segments:                           # rough demographics, not individuals
    - { name: students,      share: 0.30, age_max: 24 }
    - { name: teens,         share: 0.10, age_max: 17 }
    - { name: commuters,     share: 0.35, age_min: 25 }
    - { name: night_workers, share: 0.15, age_min: 25 }
    - { name: others,        share: 0.10 }
  recipes:
    - { when: "size = 'small'",  ingredient: coffee_beans, amount: 12, unit: g }
    - { when: "size = 'medium'", ingredient: coffee_beans, amount: 18, unit: g }
    - { when: "size = 'large'",  ingredient: coffee_beans, amount: 24, unit: g }
  packs:
    coffee_beans: 1000

machine:
  initial: weather
  states:
    weather:
      do: sketch.weather_change
      with: { place: data.place }
      then: split_trade

    split_trade:                      # SQL: sales.drinks x segment share = drinks per segment
      do: etl.split_by_share
      then: match_orders

    match_orders:                     # one row per SEGMENT
      decide:
        if: segment = 'students'
        then:
          drink:
            - { temp: iced, size: large,  weight: 0.5 }
            - { temp: iced, size: medium, weight: 0.2 }
            - { temp: hot,  size: medium, weight: 0.3 }
        else:
          if: segment = 'night_workers'
          then:
            drink:
              - { temp: hot, size: large, caffeine: high, weight: 1.0 }
          else:
            drink:
              - { temp: hot,  size: medium, weight: 0.6 }
              - { temp: iced, size: medium, weight: 0.4 }
      evidence:                       # ? the weather judgement nudges the temp weights
        weather:
          shift: weather.temp_shift
          weight: 0.3
      forbid:
        - when: age_max <= 17         # teens: the under-18 rule
          drop: "caffeine <> 'none'"  # weights renormalised; an empty result fails the run
      then: to_ingredients

    to_ingredients:
      do: convert.recipes             # sum(weight x segment drinks) per option, times each recipe
      rounding: { pack: data.packs }
      then: write

    write:
      do: sink.ingredients
      then: done

    done:
      final: true
```

**Decisions behind this example (owner, 2026-10-29):**
* Per-customer history is contrived; the input is last week's total sales, and a decider's row is a **segment** with a share of the trade.
* Jev's one job is reading the Almanac forecast against last week's weather on a five-level rubric. Events and "how would students like a special" were rejected: no rubric, no grounding.
* The comparison is **next week's forecast against last week's weather**, not against a seasonal normal.
* Weighted leaves came back: a segment's preference is a set of shares, not one drink.

## 7. The evening example in this model

* `gates` become filters; the evenings switch stays as a `when:`. `scores` become deciders whose leaves take weights from ordered lists and slices. `shortlist` keeps the top 5 by blended weight. `pick` is a final `ask`. `target`, `calls` and `turn:` are gone.
* **Seating is a subsketch** (`seating.yaml`): inputs `showing`, `tickets`, `row`, `centre`; a read-only `seats` source; an ETL stage that turns the seat map into candidate blocks of adjacent free seats at least `tickets` long; a `decide` stage; a final `ask`; a `reserve` stage that is the only side effect; outputs the `hold`. The parent pays only with `hold: seating.hold`, so Jev can never pay for something it invented. A subsketch that finds nothing finishes with outcome `none`, and the parent routes that to `walk_away`.

## 8. Open questions

* How the expected Almanac level becomes `temp_shift`, and the `evidence:` / `weight` syntax (placeholders above).
* Fetching the Almanac text automatically is out of this epic; the owner pastes it into a file each week.
* How a subsketch names and exposes its outputs to the parent (`outputs:` is a guess); how `ask` / `score` branches are written.
* Whether `next:` (an outcome that also continues to another test) is needed, or a leaf always ends its branch.
* Which condition language: SQL expressions over named fields (assumed) versus something smaller.
* Event payloads: confirm the Python loop can pass a stage's result to guards (Spike 1, open item 2).
* How the other old examples (cli, http, web, mcp) translate; they are slice B, after the proof of concept.
