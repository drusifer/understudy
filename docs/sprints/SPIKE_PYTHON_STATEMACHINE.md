# Spike 1: python-statemachine 3.2.2 vs the sketch `turn:` machine

* **Date**: 2026-10-29. **Timebox**: under an hour. **Status**: partial answer, one open item. Disposable code, not kept.
* **Question**: can the XState-shaped `turn:` (`examples/cli/sketch.yaml`) run on python-statemachine's YAML? (Epic: `EPIC_PYTHON_PORT.md`, rabbit hole 1.)
* **Method**: wrote the CLI example's turn as a python-statemachine document, loaded it with `statemachine.io.load(<yaml text>, format="yaml")`, and drove it with a model object that supplies the guards; then fed documents with the other XState features to the validating loader (`validate=True`).

## Findings

| `turn:` feature | Result | Evidence |
|---|---|---|
| States, `initial`, `final` | **Maps** | The ETL's `stages.yaml` and this prototype. |
| Events and targets | **Maps** as a `transitions:` list of `{event, target}` (XState writes `on: { EVENT: target }`) | Prototype ran waiting → looking → answering → replying → waiting → looking → finished and reported terminated. |
| Named guards | **Maps** as `cond: <name>`, resolved to a method on the model; first matching transition wins, a final unguarded transition is the fallback | `phase_is_asking`, `phase_is_done`, then fallback to `waiting` all behaved as the XState `onDone` list does. |
| `tags` (`move`, `safe`) | **Does not map**: the schema rejects state `tags` ("Additional properties are not allowed") | Validating loader. |
| State `description` | **Does not map**: also rejected | Validating loader. |
| `invoke: { src, onDone, onError }` (an actor whose result drives the next transition) | **Does not map**: python-statemachine's `invoke` starts a child statechart (SCXML style); `onDone` is rejected | Validating loader; `invoke.py` docs. |
| Guard `params` (`{ type: phase, params: { is: asking } }`) | **Not tested.** `cond` takes a name or expression; whether parameters can be passed is open | See next steps. |

## Consequences for the port

* The machine itself ports. What does not map is **metadata and effects**, and both can live outside the machine without a new representation:
  * `tags` and `description` become a sibling mapping in the sketch (for example `turn.tags: { waiting: [safe], answering: [move] }`) that our loader reads and strips before handing the rest to python-statemachine. No schema extension.
  * `invoke` becomes the library action on entry plus an event: entering `looking` runs the library's `look`, which sends `looked`; `replying` runs `play` and sends `played`. The Python seat sends the event with the result; transitions guard on it, exactly as today.
* The sketch's `turn:` shape therefore changes once (owner rule: no back-compat, sketches rewritten, not shimmed). The six examples and `docs/SKETCHES.md` change with it, and the JSON Schema for sketches (ADR-0031) is regenerated.
* Library names stay the contract (`understudy library <folder>`); the Python library module supplies guards, actions and actors by the same names.

## Open, to settle in the first slice's story or a half-hour spike

1. Guard parameters: either a parametrised `cond` expression is supported by the evaluator, or each use becomes its own named guard (`phase_asking`). Check `evaluators.py` first. If neither fits, the loader expands `{type, params}` into a bound callable before the machine is built.
2. Event data: confirm `sm.send("looked", result=...)` reaches the guards and actions as the XState event payload does.

## Not covered here (still pending in the epic)

Spike 2 (dashboard flow layout without elkjs) and spike 3 (Playwright for Python against the `page` target).
