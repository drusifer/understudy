# understudy

A platform for automating decisions the way their owner would make them.

You write one YAML **play**: its **stage** (the props it takes and the files it reads and writes), what can
be decided, your rules as `if` / `then` / `else` trees with weights, and a **scene** of **beats** that connects
them. understudy, the actor who stands in for you, performs it.
Counting and converting are SQL on DuckDB, your judgement is the decision tree, and **Jev** (the
TypeSafe judgement model) is kept for the one thing a rule cannot read: a qualitative judgement
about text you supply, against a rubric you write. Jev only chooses among levels you list and gives
probabilities; it never writes a value.

The first play is a coffee shop. From last week's total sales and a rough picture of the
customers (students, commuters, night workers), it works out how much to order for next week. A
weather play it calls has Jev compare the Farmers' Almanac's descriptions of last week and next week;
the owner's own weights turn that into more or fewer iced drinks.

```text
$ bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"
beat weather
beat weather_change.judge
beat weather_change.give
beat split_trade
beat match_orders
beat to_ingredients
beat write
wrote .understudy/runs/run-20261030T041744-28ee3978/ingredients.jsonl      {"amount": 32000, "ingredient": "coffee_beans", "unit": "g"}
```

Every live Jev read is captured, so a run can be replayed offline: `--replay` needs no key and no
network, and two replays are byte-identical.

> **Status:** the move to Python and this model is done (the [epic](docs/sprints/EPIC_PYTHON_PORT.md)):
> one runtime, one kind of play. `understudy dashboard` serves a console over your runs: watch them, see inside them and Jev's answers, and start, replay and stop them (no login: keep it on a network you trust).

## Quick start

Needs CPython 3.12.15 (uv installs it), uv 0.13.0, `make`, the
`bobp` CLI (Bob Protocol tooling - it wraps every make target and captures its output in
`build/build.out`), and, for a live run that asks Jev, a TypeSafe API key.

```sh
bobp make install                                                  # locked environments, inside the project
bobp make run ARGS="check tests/fixtures/coffee/coffee_week.yaml"  # check a play, run nothing
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay"   # offline, the real answer
export TYPESAFE_API_KEY=...                                        # for a live run
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"    # live: one Jev request, captured
```

The household example (`examples/household/household.yaml`) is an ordinary play. It reads Monarch and
Amex exports as CSV files, merges a charge seen in both into one record, links the two halves of a card
payment, links refunds to their originals, and asks Jev to judge payees, choose among a refund's candidate
charges, and place merchants in a category in use or name a new one from the MCC list. It writes
`records.jsonl` and some counts under `.understudy/runs/<run-id>/` (git-ignored and private; `bobp make clean` leaves it alone):

```sh
bobp make run ARGS="run examples/household/household.yaml --with monarch=inputs/monarch.csv --with amex=inputs/amex.csv --with amex_account=Platinum"
```

Use `--with since=2026-01-01` to set the period and `--with amex_account=<text>` to name the Monarch card
account (a part of its name); `--out <folder>` chooses the output folder.

Always go through `bobp make <target>` - it is the front door for people and agents alike.
`bobp make help` lists the targets.

## Documentation

| Read | When you want to |
|---|---|
| [docs/PRD.md](docs/PRD.md) | what understudy is for, who it serves, what it must do and what is planned |
| [docs/ARCH.md](docs/ARCH.md) · [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md) | how the system is put together, and how it is tested |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | install, run the coffee example, read the output, replay offline, write a play, fix errors |
| [docs/PLAYS.md](docs/PLAYS.md) | the reference: the stage, the scene and its beats, the actions, deciding and conditions, Jev, calling a play, capture and replay; [schema/play.schema.json](schema/play.schema.json) for editors |
| [docs/DOMAIN.md](docs/DOMAIN.md) | the vocabulary and the rules that always hold |
| [docs/sprints/DESIGN_SKETCH_MODEL.md](docs/sprints/DESIGN_SKETCH_MODEL.md) · [docs/sprints/STORY_ARCH_SPRINT28.md](docs/sprints/STORY_ARCH_SPRINT28.md) | how the model was shaped (as sketches), and how it became plays |
| [docs/DECISIONS.md](docs/DECISIONS.md) | why it is built this way (ADRs) |
| [docs/SDLC.md](docs/SDLC.md) | how the project is built, tested, changed and released |
| [CHANGELOG.md](CHANGELOG.md) · [docs/BACKLOG.md](docs/BACKLOG.md) | what shipped · what is next |

Sprint documents are in [docs/sprints/](docs/sprints/).

## Repository layout

```text
bin/understudy        the command (a shell script that starts the Python package)
src/play/              the play package: loader, check, machine, decide, blend, actions (stages*.py), sources (file, Jev, capture), run, cli
src/jev.py             the one Jev wrapper (shared)    src/paths.py   the output-path policy (shared)
src/machine_runner.py  the one loop that performs a scene's flow
src/dashboard/         the console: server.py (what the page shows) and its browser files (page.html, page.js, CSS, fonts)
schema/                JSON Schema for plays
tests/                 Python unittest suites, fixtures (coffee, household)
examples/              evening (a night out) and household (the transaction cleanup)
docs/                  user and project documentation
agents/                the Bob Protocol team (personas, state, chat) - see AGENTS.md
```

## Development

```sh
bobp make test        # unit tests - never calls Jev
bobp make test-py ARGS="test_play*.py"     # only the files matching a pattern
bobp make lint        # ruff
bobp make dashboard   # the console over .understudy/runs, http://<this machine>:4180/ (listens on 0.0.0.0, no login)
bobp make security-scan      # gitleaks and pip-audit (network)
bobp make test-browser       # the console in a real Chromium (after 'bobp make install-browser')
bobp make check       # test + lint + gitleaks secret scan (the gate)
```

Change process, branching and releases: [docs/SDLC.md](docs/SDLC.md). This repo is worked on
by a multi-persona agent team; their entry point is [AGENTS.md](AGENTS.md).

## License

GPL-3.0 — see [LICENSE](LICENSE).
