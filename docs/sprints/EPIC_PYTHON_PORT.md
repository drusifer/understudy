# Epic: Python port of understudy

* **Status**: Appetite set by the owner 2026-10-29: 4 sprints, sliced A-D as in section 2. Smith Gate 1 (problem) approved. Sprint 19 = spikes #1-#3 plus slice A planning.
* **Owner decision (2026-10-27)**: Python for all of understudy; Node replaced outright, no back-compat, no dual runtime (`agents/cypher/platform_decision_2026-10-27.md`)
* **Rules**: no back-compat, YAGNY, DRY, use libraries, Jev chooses and never writes

## 1. Problem

understudy is split across two runtimes. The ETL (Sprints 16-18) is Python: python-statemachine YAML controller, SQLMesh on DuckDB, MCP source servers, `typesafe-sdk`. The player (sketch loader, XState turn machine, targets, dashboard server, CLI) is Node: about 6,000 lines of server code and 4,500 lines of tests. Two toolchains, two lockfiles, two test runners, two Jev SDKs and two statechart libraries mean every change is paid for twice, and the dashboard cannot show an ETL run because they share nothing.

**Outcome:** one Python runtime for everything the owner runs; sketches stay no-code `sketch.yaml`; every example still plays with the same decisions; the browser side of the dashboard stays JavaScript and CSS (it runs in the browser either way).

## 2. Appetite

**4 sprints** (owner, 2026-10-29), each ending in something runnable, in this order, so the Node side shrinks every sprint rather than at the end:

| Sprint | Slice | Ends with |
|---|---|---|
| A | Sketch loader + turn machine + Jev seat in Python; the `process` target and CLI `play`/`check` | `examples/cli` plays from Python |
| B | `http`, `mcp`, `page` targets (Python `mcp` SDK, Playwright for Python) and the remaining examples | all six examples play from Python |
| C | Dashboard and watch servers (HTTP + SSE), flow layout, rack, settings | console and watch page served by Python |
| D | Delete the Node code, `package.json`, eslint and the Node test runner; Python-only SDLC | one toolchain |

## 3. No-gos (not built in this epic)

* No Node/Python bridge or dual-run mode (owner: no back-compat). Slices are cut over, not shimmed.
* No new sketch format, no new statechart format, no XML/SCXML. Sketches keep today's shape unless a story proves the Python library cannot express it, and then the sketch changes once, everywhere.
* No browser-side rewrite: `page.mjs` files and the theme CSS stay JavaScript/CSS. The server that serves them is what moves.
* No new features. A port story fails if it adds behaviour; behaviour differences are bugs on one side or the other.
* No rewriting of the ETL (already Python); the dashboard does not gain ETL views in this epic.

## 4. Domain (ubiquitous language, kept from the Node code)

Sketch (a `sketch.yaml`), Target (process, http, mcp, page), Part (what the app offers), Turn (look, choose, play), Seat (the Jev seat), Move, Gate and Weight inputs, Shortlist, Walk-away, Run event stream, Console (dashboard) and Watch page. Names carry over unchanged so docs, examples and sketches do not churn. A Domain document (`_template_DOMAIN.md`) is Morpheus's next step after Gate 1.

## 5. Rabbit holes and spikes (each is a `*spike`, timeboxed, before stories)

| # | Unknown | Evidence so far | Spike |
|---|---|---|---|
| 1 | Does python-statemachine's YAML express the `turn:` machine: `tags` (`move`/`safe`), guards with params, `invoke` of `look`/`play`, `final`? | Sprint 17 used it for the ETL stages but found `tags` missing from its schema. The ETL machine has none of the turn features. | Port `turn:` for `examples/cli`; list what does not map and the smallest change to the sketch or code for each. |
| 2 | Flow layout for the dashboard (elkjs has no mature Python port). | Layout is computed server side today (ADR-0035). | Compare: Python graph layout library, calling elkjs as a build-time/one-shot tool (violates the no-dual-runtime rule, likely out), or a simple layered layout of our own. Decide on screenshots. |
| 3 | `playwright` for the `page` target and browser tests. | Playwright has a first-class Python API. | Small: run the web example's aria snapshot from Python. |
| 4 | Parity of the Jev seat (confidence, probabilities, pick/shortlist). | RETIRED: `typesafe-sdk` returns per-option probabilities (`Chosen.probabilities`) and Noul floats; Sprint 17's `src/etl/jev.py` already wraps them. Reuse that wrapper, do not write a second one (DRY). | none |

## 6. Platform feasibility (Tank)

* Tooling already in place: `uv` + `pyproject.toml` + `uv.lock`, `unittest`, ruff with a strict rule set, `bobp make` as the front door. No new language or package manager. Packages likely to add through the existing lock flow: `playwright` (browser binaries via the existing `install-browser` target), an HTTP server library if the standard library is not enough (decide in the dashboard sprint, prefer the standard library: YAGNY).
* Mechanism changes: removing Node, `package.json`, eslint and `node:test` at the end is a SDLC mechanism change and needs owner approval at Sprint D, not before.
* Risk: a long period where the dashboard console runs on Node while the player runs on Python. Mitigation: the order above keeps the console on the Node side until its inputs (event stream, rows) are Python; the console reads the same JSONL event stream either way.

## 7. Verification principle

Parity is measured, not asserted: for each example, run the Node player and the Python player with the same Jev double and require the same event stream (same moves, same order). The Node run is the oracle until Sprint D deletes it.

## 8. Next

1. Owner sets the appetite (section 2).
2. Smith Gate 1 (problem), Morpheus domain model, spike #1 and #2 (they decide whether the sketch or the dashboard changes shape), Smith Gate 2.
3. Then `*story` for the first slice (Sprint A) and the Sprint 19 plan.
