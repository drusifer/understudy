# understudy

Stand-ins that play your app the way a person would.

An **understudy** looks at a running app, works out whether something is being asked of it,
lets Jev (the TypeSafe judgment model) pick one of the moves the app
offers, and makes that move — until its **sketch** says it is done. A sketch is one
`sketch.yaml`: what to play, a small statechart, and the questions Jev answers. Code only
where an app needs reading that no built-in app does (`hooks.mjs`). No scripted inputs.

It plays four kinds of app, with the same sketch format:

- **command-line programs** — reads the terminal output, types the answers;
- **web pages** — unmodified: read the way a screen reader does, played in headless Chromium;
- **JSON APIs** — a look is a GET of the app's state, a move is a request;
- **MCP servers** — local (stdio) or remote (HTTP, token headers), named the way Claude names
  them; the tools are the moves and Jev chooses their arguments. No code.

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
bobp make run ARGS="run examples/http"              # play the vending machine API
bobp make run ARGS="run examples/mcp"               # play the box office MCP server
bobp make run ARGS="check examples/cli"             # check a sketch without starting anything (no key needed)
```

Always go through `bobp make <target>` - it is the front door for people and agents alike.
`bobp make help` lists the targets.

## Documentation

| Read | When you want to |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | install, run, read the output, write your first sketch, fix errors |
| [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md) | see the examples taken apart, line by line, with real runs |
| [docs/MCP_GUIDE.md](docs/MCP_GUIDE.md) | point understudy at an MCP server you already have (yours, or one configured for Claude) |
| [docs/SKETCHES.md](docs/SKETCHES.md) | the reference: `sketch.yaml`, the four targets, hooks, library names, exit codes |
| [docs/DECISIONS.md](docs/DECISIONS.md) | why it is built this way (ADRs) |
| [docs/SDLC.md](docs/SDLC.md) | how the project is built, tested, changed and released |
| [CHANGELOG.md](CHANGELOG.md) · [docs/BACKLOG.md](docs/BACKLOG.md) | what shipped · what is next |

Project history: [docs/EXTRACTION_MAP.md](docs/EXTRACTION_MAP.md) (how understudy was lifted
out of recard's game harness) and the sprint documents in
[docs/sprints/](docs/sprints/).

## Repository layout

```text
bin/understudy.mjs     the command
src/                   the core: run loop, sketch loader, statechart, seat, Jev decisions, targets/, apps/
examples/cli/          a terminal coffee counter + its sketch and hooks
examples/web/          a sign-up wizard page (unmodified) + its sketch (no code)
examples/http/         a vending machine JSON API + its sketch and hooks
examples/mcp/          a cinema box office MCP server + its sketch (no code)
examples/mcp-remote/   the same box office by URL and token, named in servers.json
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
