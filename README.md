# understudy

A platform for automating decisions the way their owner would make them.

You write one YAML **sketch**: where the data comes from, what can be decided, your rules as
`if` / `then` / `else` trees with weights, and the pipeline that connects them. understudy runs it.
Counting and converting are SQL on DuckDB, your judgement is the decision tree, and **Jev** (the
TypeSafe judgement model) is kept for the one thing a rule cannot read: a qualitative judgement
about text you supply, against a rubric you write. Jev only chooses among levels you list and gives
probabilities; it never writes a value.

The first sketch is a coffee shop. From last week's total sales and a rough picture of the
customers (students, commuters, night workers), it works out how much to order for next week. A
weather subsketch has Jev compare the Farmers' Almanac's descriptions of last week and next week;
the owner's own weights turn that into more or fewer iced drinks.

```text
$ bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"
stage weather
stage weather_change.judge
stage split_trade
stage match_orders
stage to_ingredients
stage write
wrote build/runs/run-20261030T041744-28ee3978/ingredients.jsonl      {"amount": 32000, "ingredient": "coffee_beans", "unit": "g"}
```

Every live Jev read is captured, so a run can be replayed offline: `--replay` needs no key and no
network, and two replays are byte-identical.

> **Status:** understudy is mid-way through moving to Python and this model (the
> [epic](docs/sprints/EPIC_PYTHON_PORT.md)). The older "play an app like a person" sketches, the
> six examples and the dashboard are being rebuilt for it; `understudy library`, `watch` and
> `dashboard` say so for now.

## Quick start

Needs CPython 3.12.15 (uv installs it), uv 0.13.0, Node 24 (only for the launcher), `make`, the
`bobp` CLI (Bob Protocol tooling - it wraps every make target and captures its output in
`build/build.out`), and, for a live run that asks Jev, a TypeSafe API key.

```sh
bobp make install                                                  # locked environments, inside the project
bobp make run ARGS="check tests/fixtures/coffee/coffee_week.yaml"  # check a sketch, run nothing
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay"   # offline, the real answer
export TYPESAFE_API_KEY=...                                        # for a live run
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"    # live: one Jev request, captured
```

The local transaction cleanup run reads Monarch and Amex exports through Python MCP source
servers, merges sign-flipped purchases in DuckDB, pairs transfers, links refunds, and asks Jev
to place merchants in the offered categories or name new ones from the MCC list. It writes
`result.jsonl` and `summary.json` under `build/runs/<run-id>/`:

```sh
bobp make run ARGS="etl run --monarch inputs/monarch.csv --amex inputs/amex.csv"
```

Use `--since 2026-01-01` to set the period, `--amex-account <text>` to select the Monarch card
account when detection is unclear, and `--out <folder>` to choose the output folder.

Always go through `bobp make <target>` - it is the front door for people and agents alike.
`bobp make help` lists the targets.

## Documentation

| Read | When you want to |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | install, run the coffee example, read the output, replay offline, write a sketch, fix errors |
| [docs/SKETCHES.md](docs/SKETCHES.md) | the reference: the file, the machine and its stages, deciding and conditions, Jev, subsketches, capture and replay; [schema/decision_sketch.schema.json](schema/decision_sketch.schema.json) for editors |
| [docs/DOMAIN.md](docs/DOMAIN.md) | the vocabulary and the rules that always hold |
| [docs/sprints/DESIGN_SKETCH_MODEL.md](docs/sprints/DESIGN_SKETCH_MODEL.md) | how the model was shaped, and why |
| [docs/DECISIONS.md](docs/DECISIONS.md) | why it is built this way (ADRs) |
| [docs/SDLC.md](docs/SDLC.md) | how the project is built, tested, changed and released |
| [CHANGELOG.md](CHANGELOG.md) · [docs/BACKLOG.md](docs/BACKLOG.md) | what shipped · what is next |

Sprint documents are in [docs/sprints/](docs/sprints/).

## Repository layout

```text
bin/understudy.mjs     the command
src/cli.mjs            the launcher: `run`, `check` and `etl run` start the Python packages
src/sketch/            the sketch package: loader, check, machine, decide, blend, stages, sources (file, Jev, capture), run, cli
src/etl/               the household transaction cleanup (SQLMesh on DuckDB, MCP source servers)
src/jev.py             the one Jev wrapper (shared)    src/paths.py   the output-path policy (shared)
src/machine_runner.py  the one state-machine loop (shared by the ETL and sketches)
src/dashboard/         the dashboard's browser files, kept for the rebuild
schema/                JSON Schema for sketches
tests/                 Python unittest suites, the launcher's node:test, fixtures (tests/fixtures/coffee)
examples/              the older examples, to be rebuilt for the new model
docs/                  user and project documentation
agents/                the Bob Protocol team (personas, state, chat) - see AGENTS.md
```

## Development

```sh
bobp make test        # unit tests (JavaScript launcher, Python, SQLMesh) - never calls Jev
bobp make test-py ARGS="test_sketch*.py"   # only the sketch tests
bobp make lint        # eslint and ruff
bobp make check       # test + lint + gitleaks secret scan (the gate)
```

Change process, branching and releases: [docs/SDLC.md](docs/SDLC.md). This repo is worked on
by a multi-persona agent team; their entry point is [AGENTS.md](AGENTS.md).

## License

GPL-3.0 — see [LICENSE](LICENSE).
