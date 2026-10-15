# understudy

Stand-ins that play your app the way a person would.

An **understudy** looks at a running app, works out whether something is being asked of it,
lets Jev (the TypeSafe judgment model) pick one of the moves the app
offers, and makes that move — until its **part** says it is done. You write the part as a
small YAML statechart plus the questions Jev answers; a short **adapter** says what the app
looks like and which moves it offers. No scripted inputs.

It plays two kinds of app today, with the same part format:

- **command-line programs** — reads the terminal output, types the answers;
- **web pages** — served locally and played in headless Chromium.

```text
$ bobp make run ARGS="run examples/cli"
understudy: playing coffee-cli (node app.mjs) - log build/runs/coffee-cli/2026-10-15T19-55-29.042Z.jsonl
understudy: step 1 asking -> size:medium (0.95)
understudy: step 2 asking -> milk:whole (0.73)
understudy: step 3 asking -> confirm:order (0.96)
```

## Quick start

Needs Node 24, `make`, the `bobp` CLI (Bob Protocol tooling - it wraps every make target and
captures its output in `build/build.out`), and a TypeSafe API key.

```sh
bobp make install                                   # npm ci - everything stays inside the project
export TYPESAFE_API_KEY=...                    # Jev is required for a run
bobp make run ARGS="run examples/cli"               # play the coffee-counter program
bobp make install-browser                           # once, for web targets (skip if Chromium is installed)
bobp make run ARGS="run examples/web"               # play the sign-up web page
bobp make run ARGS="check examples/cli"             # check a part without starting anything (no key needed)
```

Always go through `bobp make <target>` - it is the front door for people and agents alike.
`bobp make help` lists the targets.

## Documentation

| Read | When you want to |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | install, run, read the output, write your first part, fix errors |
| [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md) | see both examples taken apart, line by line, with a real run |
| [docs/ADAPTERS.md](docs/ADAPTERS.md) | the reference: adapter shape, targets, part files, library names, exit codes |
| [docs/DECISIONS.md](docs/DECISIONS.md) | why it is built this way (ADRs) |
| [docs/SDLC.md](docs/SDLC.md) | how the project is built, tested, changed and released |
| [CHANGELOG.md](CHANGELOG.md) · [docs/BACKLOG.md](docs/BACKLOG.md) | what shipped · what is next |

Project history: [docs/EXTRACTION_MAP.md](docs/EXTRACTION_MAP.md) (how understudy was lifted
out of recard's game harness) and the sprint documents in
[docs/sprints/](docs/sprints/).

## Repository layout

```text
bin/understudy.mjs     the command
src/                   the core: run loop, part loader, statechart, seat, Jev decisions, targets/
examples/cli/          a terminal coffee counter + its adapter and part
examples/web/          a sign-up wizard page + its adapter and part
tests/                 node:test suites (offline: a Jev double, no browser)
docs/                  user and project documentation
seed/                  recard files not yet generalized (not run, not linted)
agents/                the Bob Protocol team (personas, state, chat) - see AGENTS.md
```

## Development

```sh
bobp make test        # unit tests - never calls Jev or launches a browser
bobp make lint        # eslint
bobp make check       # test + lint + gitleaks secret scan (the gate)
bobp make test-live   # plays every example with real Jev (costs API calls)
```

Change process, branching and releases: [docs/SDLC.md](docs/SDLC.md). This repo is worked on
by a multi-persona agent team; their entry point is [AGENTS.md](AGENTS.md).

## License

GPL-3.0 — see [LICENSE](LICENSE).
