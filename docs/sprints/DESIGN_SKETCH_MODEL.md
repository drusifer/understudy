# Design: the sketch model for the Python port

* **Status**: DESIGN NOTES from the owner conversation of 2026-10-29. Not decided, not built. Input to the Python port epic (`EPIC_PYTHON_PORT.md`) and to the first slice's stories.
* **Rules**: no back-compat, YAGNY, DRY, no new language (SQL on DuckDB; `python-statemachine` YAML), Jev chooses and never writes.

## 1. What changed in our thinking

* **There is no single state machine for all sketches.** Users build and compose their own state machines for the task at hand. Spike 1 (`SPIKE_PYTHON_STATEMACHINE.md`) found that `tags`, state `description` and `invoke`/`onDone` do not map onto python-statemachine; they only existed to carry the old built-in `turn:` plumbing, so the problem mostly goes away.
* **The main loop is plain Python.** It feeds sources to the user's machine as events and runs the step the current state names. No built-in loop machine (YAGNY).
* **The platform is for automation, not chat.** Understudy models a decision: the owner writes down how they decide.

## 2. Division of labour

| Role | Does | Where it lives |
|---|---|---|
| Machine | control flow: which stage runs next, branching on the data | the sketch's `machine` (python-statemachine YAML) |
| ETL and SQL | quantitative analysis: counts, trends, conversions | stages (`etl.*`, `convert.*`), DuckDB |
| `decide` trees | the owner's deterministic logic | `decide:` (if/then/else, SQL conditions) |
| Weights | how much to trust each input, computed from properties of the input | `weight:` expressions on a stage |
| Jev | qualitative judgement only: picks one of the owner's listed options, or gives a probability | `ask:` nodes and named qualitative facts |

Jev never produces an amount; the owner's rules decide what a Jev answer means.

## 3. Worked example: weekly coffee ingredients

Owner's logic: (1) count last week's customers by type; (2) match types to preferred orders with `decide` logic (for example under 18 gets no caffeine); (3) convert probable orders to ingredient counts and output. A `weather_change` subsketch compares next week's weather with last week's and feeds the choice of hot versus iced.

### `weather_change.yaml` (subsketch)

```yaml
name: weather_change
description: Next week's weather compared with the previous week's.

sources:
  next:
    kind: mcp
    server: ./weather_server
    params: { place: Burlington VT, week: next }
  previous:
    kind: mcp
    server: ./weather_server
    params: { place: Burlington VT, week: previous }

inputs:
  place: text

sinks:
  forecast: { kind: result }      # returned to the caller
  diff:     { kind: result }

machine:
  initial: compare
  states:
    compare:
      do: etl.week_over_week      # SQL over both sources
      then: done
    done:
      final: true
```

### `coffee_week.yaml`

```yaml
name: coffee_week
description: >
  From last week's customers, work out what to order for next week.

sources:
  customers: last_week_customers.jsonl     # a bare path means kind: file, format: jsonl

sinks:
  ingredients:
    kind: file
    path: out/ingredients.jsonl

data:
  place: Burlington VT
  recipes:
    - { drink: size:medium,    ingredient: coffee_beans,  amount: 18,  unit: g }
    - { drink: milk:oat,       ingredient: oat_milk,      amount: 200, unit: ml }
    - { drink: flavor:vanilla, ingredient: vanilla_syrup, amount: 15,  unit: ml }
  packs:
    coffee_beans: 1000
    oat_milk: 1000

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
      do: etl.count_by_type           # SQL: how many of each type last week
      weight:
        history: 0.8 if weeks >= 4 else 0.4
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
      adjust:
        if: weather.diff.avg_high > 5
        then:
          shift: { temp: iced }
          weight: 0.3
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

## 4. Decisions so far (owner, 2026-10-29)

1. A state machine per sketch, written by the user; the loop that runs it is Python code.
2. Decisions are written as nested `if` / `then` / `else` (not a flat rule list). A node is one of: a SQL condition with `then`/`else`; an `ask` (Jev picks one of the listed branches); or an outcome (`drink`, `use`).
3. The machine chooses which stages apply; a stage is ETL, a `decide` tree or a conversion. Weights attach to a stage and are expressions over properties of its input.
4. A sketch may use a **subsketch**: its own inputs and outputs, bound by the parent through `with:`; the parent sees only the named outputs (`weather.diff.avg_high`).
5. **Sources and sinks** are named in the sketch with `kind`, `path`/`server` and `params` written in place. **No separate `bind` section.** Interface for every kind: `describe()` and `read(params)` returning JSONL, paged; a sink is `write(params, jsonl)`. The Sprint 17 MCP source servers are the first instance.
6. **Defaults:** the `kind` supplies its own defaults (a bare path is a JSONL file; an MCP source defaults the tool and paging); a source may default its params and a caller overrides only what differs. A required value with no sensible default must fail with a clear error. **No `extends`** (decided against: YAGNY).
7. Tests override a source from the command line (`--source customers.path=fixtures/x.jsonl`); the sketch file does not change.

## 5. Open questions

* How `weight` combines with a `then` outcome (the example is a placeholder).
* How the subsketch's outputs are named and exposed to the parent (`weather.diff...`, `kind: result` are guesses).
* Whether `next:` (an outcome that also continues to another test) is needed, or a leaf always ends its branch.
* Rule order and conflicts: `forbid` should always win over `prefer`.
* Which condition language: SQL expressions over named fields (assumed) versus something smaller.
* Event payloads: confirm the Python loop can pass a stage's result to guards (Spike 1, open item 2).
* How this model absorbs the old play-an-app sketches (process, http, mcp, page targets): presumably as sources and sinks plus a Jev `ask` step; to be settled in slice A.

## 6. Next

Fold these decisions into the epic's domain model (Morpheus), then plan slice A around this shape instead of porting the old `turn:` machine.
