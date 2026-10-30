# Epic: Python port of understudy, and a new sketch model

* **Status**: Slice A (the coffee proof of concept) delivered in Sprint 19, 2026-10-30: `understudy run` and `check` are the Python commands and the old Node player is deleted. Slices B to D remain. Appetite set by the owner 2026-10-29: 4 sprints, sliced A-D (section 2). Smith Gate 1 (problem) approved. The epic was REVISED the same day after the owner reshaped the sketch model (`DESIGN_SKETCH_MODEL.md`): this is no longer a straight port. Domain model written (`docs/DOMAIN.md`), Tank feasibility passed and Smith Gate 2 approved on 2026-10-29. The epic is shaped; syntax placeholders (section 5, row 6) are settled in the Sprint 19 architecture.
* **Owner decision (2026-10-27)**: Python for all of understudy; Node replaced outright, no back-compat, no dual runtime (`agents/cypher/platform_decision_2026-10-27.md`).
* **Rules**: no back-compat, YAGNY, DRY, use libraries, Jev chooses and never writes.

## 1. Problem

understudy is split across two runtimes. The ETL (Sprints 16-18) is Python: python-statemachine YAML controller, SQLMesh on DuckDB, MCP source servers, `typesafe-sdk`. The player (sketch loader, XState turn machine, targets, dashboard server, CLI) is Node: about 6,000 lines of server code and 4,500 lines of tests. Two toolchains, two lockfiles, two test runners, two Jev SDKs and two statechart libraries mean every change is paid for twice.

A second problem sits underneath: the player is built to *play an app* like a person (look, choose a tool, play it), driven by one built-in `turn:` machine. The owner's direction is a **platform for automation**: users write down how they decide, and understudy runs it. That needs a different sketch model, so the port is also the moment to change it, once.

**Outcome:** one Python runtime; sketches that are the owner's own pipelines (user-written state machines, `decide` logic, ETL, weights), with Jev reserved for qualitative judgements; the browser side of the dashboard stays JavaScript and CSS.

## 2. Appetite

**4 sprints** (owner, 2026-10-29), each ending in something runnable. Revised slices:

| Sprint | Slice | Ends with |
|---|---|---|
| A (Sprint 19) | Proof of concept: the coffee example end to end. Sketch loader, Python main loop running the user's python-statemachine YAML, file sources and sinks, the decider contract and weighted blend, filters, a subsketch, outputs. | `coffee_week` runs on a Jev double and a live Jev, and produces `ingredients.jsonl` |
| B | Translate the remaining examples into the new model (evening with a seating subsketch, then cli, http, web, mcp); the play-an-app targets become sources, sinks and Jev `ask`. | all examples run from Python, each making the same decisions as before with a Jev double |
| C | Dashboard and watch servers (HTTP + SSE), flow layout, rack, settings, over the new model. | console and watch page served by Python |
| D | Delete the Node code, `package.json`, eslint and the Node test runner; Python-only SDLC. | one toolchain |

**Purge list (owner, 2026-10-29: "make sure the dups are purged as part of this epic").** There is to be one kind of sketch, one runtime, one of everything when the epic ends. The epic is not done until slice D has deleted or merged each of these, and slice D's gate is that this list is empty:

* **Two sketch formats:** the old `sketch.yaml` shape (`target`, `calls`, `values`, `decide` gates/scores, `turn:`, `pick`) and `schema/sketch.schema.json`; only `schema/decision_sketch.schema.json` remains (renamed `sketch.schema.json`).
* **Two commands:** `understudy run` and `understudy check` are the Python commands from Sprint 19 (owner, 2026-10-29), and the old Node `run`/`check` are deleted then; the old `library`, `watch` and `dashboard` commands may be broken until slices B to D rebuild or delete them, and slice D's gate is that none is left.
* **Two runtimes and toolchains:** `src/*.mjs`, `src/targets/`, `src/apps/`, `src/watch/`, `src/dashboard/` server code, `package.json`, `package-lock.json`, eslint, the Node test runner and their make targets and SDLC rows (the dashboard's browser files are rebuilt, not copied: they stay JavaScript/CSS only if the new dashboard still serves them).
* **Old examples** (`examples/cli`, `http`, `web`, `mcp`, `mcp-remote`, `evening`) and their Node tests: each is translated into the new model in slice B or deleted; none survives in the old shape.
* **Duplicate Python:** the Jev wrapper and the output-destination policy each exist once (`src/jev.py`, `src/paths.py`, moved in Sprint 19 phase 1), with `src/etl` and `src/sketch` both importing them; the state machine runner and `GatedJev` likewise shared, not copied.
* **Duplicate decisions and docs:** ADR-0011, ADR-0018 and ADR-0030 marked superseded; `docs/SKETCHES.md` and `docs/MCP_GUIDE.md` rewritten for the new model, not kept beside it.

## 3. No-gos (not built in this epic)

* No Node/Python bridge or dual-run mode (owner: no back-compat). Slices are cut over, not shimmed.
* No built-in loop state machine, no `turn:` tags or invoke, no scoring formula (`position ^ weight`): decisions are `if`/`else` filters plus one weighted blend.
* No new statechart format, no new ETL language, no XML. SQL on DuckDB; python-statemachine YAML.
* No browser-side rewrite: `page.mjs` files and theme CSS stay JavaScript/CSS.
* Sources and sinks are **files only** in this epic (owner, 2026-10-29). MCP and HTTP source kinds are not built; examples that need a live server (evening's box office and ratings, mcp, http) are translated against file fixtures or deferred. The Sprint 17 MCP source servers keep working for the ETL.
* No free-form numeric or free-text outcomes; Jev never writes values.
* Sources are read-only; side effects live in stages only.
* The dashboard does not gain ETL views in this epic.

## 4. Domain (ubiquitous language)

* **Sketch**: a YAML file naming its sources, sinks, outcomes, questions and a `machine`. **Subsketch**: a sketch used as a stage; own inputs and outputs; the parent decides which inputs to expose.
* **Machine / Stage**: the user's python-statemachine YAML; a stage is ETL, a `decide` tree, a conversion, or a subsketch call. The loop that runs it is Python.
* **Source / Sink**: named JSONL in and out with a `kind`; `describe()` and `read(params)`; sinks `write(params, jsonl)`; sources read-only.
* **Outcome / Dimension**: a declared enumeration or discrete numeric steps; candidates may be read from source rows.
* **Decider**: one row in, rows out, each a full combination plus a `weight` (summing to 1). Implemented by a `decide` tree, an ETL lookup, a subsketch or Jev's `ask`.
* **Blend**: the single combination rule, a weighted average of deciders' rows. **Filter / forbid**: drops rows, renormalises; empty result fails unless `on_empty` says `fallback`, `skip` or `walk_away`.
* **Input**: a fader, switch, count or choice the person sets, as today. **Weight**: a number, or an `if` / `then` / `else` over properties of a stage's input. Conditions are explicit YAML (field, operator, value), never text.
* **Jev**: read like any other source (`kind: jev`): a rubric (instructions plus criteria) and the data it reads go in, a probability per option comes out; the probabilities become weights.
* Kept from before, for the dashboard and docs: Console, Watch page, Run event stream.

## 5. Rabbit holes and spikes

| # | Unknown | Evidence so far | Status |
|---|---|---|---|
| 1 | Does python-statemachine's YAML run a user-written machine? | `SPIKE_PYTHON_STATEMACHINE.md`: states, events, named guards work; tags/description/invoke are rejected, but the new model no longer needs them. Open: guard params, event payloads. | Mostly retired; finish inside the PoC |
| 2 | Flow layout for the dashboard (elkjs has no mature Python port). | Not needed until slice C. | Deferred to C |
| 3 | Playwright for Python for browser tests and the `page` target. | Not needed until B/C. | Deferred |
| 4 | Jev probabilities. | RETIRED: `typesafe-sdk` returns per-option probabilities; reuse `src/etl/jev.py`. | Retired |
| 5 | Can the evening example (and the old play-an-app sketches) be expressed in the new model without losing criteria? | Walked through with the owner: all criteria map (filters, ordered lists, slices, ask, seating as a subsketch with ETL for adjacency). | Re-check in slice B |
| 6 | Syntax of stages, blending, conditions, subsketch outputs and Jev questions. | Settled with the owner 2026-10-29 in `DESIGN_SKETCH_MODEL.md` (`blend:`, explicit YAML conditions, `returns: { decider: [...] }`, `kind: jev` source). | Retired; the architecture only writes it down |

## 6. Platform feasibility (Tank)

* Tooling in place: `uv` + `pyproject.toml` + `uv.lock`, `unittest`, ruff with a strict rule set, `bobp make` as the front door. No new language or package manager. Likely additions through the existing lock flow: none for the PoC (python-statemachine, duckdb, mcp, typesafe-sdk are present); `playwright` later.
* Removing Node, `package.json`, eslint and `node:test` at the end is an SDLC mechanism change and needs owner approval at Sprint D.
* Risk: the Node dashboard keeps running the old sketches until slice C, and the old examples are not runnable in the new model until slice B. Mitigation: the Node side stays untouched and shrinks only when its replacement runs; no shims.

## 7. Verification principle

The PoC is verified by decisions, not event streams: `coffee_week` with a Jev double must produce the expected ingredient file for fixed fixtures, and the age rule must never be broken. For slice B, each translated example must make the same decisions as its Node original with the same Jev double (the Node run is the oracle until Sprint D deletes it). The event stream shape is free to change.

Test data for the proof of concept is **invented fixtures** (owner, 2026-10-29): last week's sales and two Almanac descriptions (last week's and next week's), kept under `tests/fixtures/`. Real figures can replace them later without changing the sketch.

Fixture figures (researched 2026-10-29, rough ranges from marketing blogs): about 1,600 drinks a week; 12, 18 and 24 g of beans for a small, medium and large drink (a double espresso is about 18 g); Burlington VT normals for early November of about 45°F high and 31°F low, with last week (late October) milder; the Almanac text is invented in its short style ("Fair but cold, with rain clearing midweek and a hint of snow by the weekend.").

**Live judgement (owner, 2026-10-29):** the proof of concept's acceptance includes **one live Jev judgement** on the Almanac text. Tests use a Jev double; the live run happens once, at sprint close, with the owner's go-ahead.

**Interface (owner, 2026-10-29):** the proof of concept is command line only: `understudy run coffee_week.yaml` prints the stages and writes `ingredients.jsonl`. The dashboard is slice C.

## 8. Next

1. Smith Gate 2 on this revision; Morpheus writes the domain model from section 4 and settles the placeholders in section 5 row 6.
2. Sprint 19 = the coffee proof of concept (slice A): stories, architecture, plan.
3. Sprint 19's retro decides whether slices B-D keep their order.
