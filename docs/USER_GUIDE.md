# understudy User Guide

How to install understudy, run a part against an app, read what it did, write a part for
your own app, and fix what goes wrong.

TLDR:
    Setup: `bobp make install`, set `TYPESAFE_API_KEY`, `bobp make install-browser` for web apps.
    Run: `bobp make run ARGS="run <dir>"`; check without running: `ARGS="check <dir>"`.
    Output: one JSON line per step on stdout and in build/runs/<adapter>/; exit 0 / 1 / 2.
    Your own app: copy an example directory, edit adapter.mjs and part/, `check` until OK.
    Web pages need no changes and often no adapter code: the generic page app plays them.
    Reference: docs/ADAPTERS.md. Worked example: docs/WALKTHROUGH.md.

## Contents

1. [Concepts](#1-concepts)
2. [Install](#2-install)
3. [Run an example](#3-run-an-example)
4. [Read the output](#4-read-the-output)
5. [Write a part for your own app](#5-write-a-part-for-your-own-app)
6. [Troubleshooting](#6-troubleshooting)
7. [Command reference](#7-command-reference)

---

## 1. Concepts

| Word | Meaning |
|---|---|
| **understudy** | the stand-in that plays your app: it looks, decides with Jev, and moves |
| **app** | the thing being played - a command-line program, a web page or a JSON API |
| **target** | how understudy sees and moves the app: `process` (stdin/stdout), `page` (headless Chromium, read like a screen reader) or `http` (requests) |
| **adapter** | your small `adapter.mjs`: which phase the app is in, what Jev should know, which moves are on offer, how to make one |
| **part** | `part/turn.yaml` (a statechart: when to look, when to move, when it is over) + `part/questions.yaml` (what Jev is asked) |
| **Jev** | TypeSafe's judgment model; it only ever picks among the moves the adapter offers |
| **example directory** | one folder holding an adapter and a part, e.g. `examples/cli/` |

A run repeats one loop: **look** at the app → if the part says it is the understudy's move,
**ask Jev** to pick one of the offered moves → **make the move** → look again, until the part
reaches its end state.

## 2. Install

You need Node 24, `make`, the `bobp` CLI and a TypeSafe API key.

```sh
bobp make install            # npm ci into node_modules/ - nothing is installed globally
export TYPESAFE_API_KEY=...  # needed by `run` only; `check` and `library` work without it
bobp make install-browser    # only for web apps, and only if no Chromium is installed
```

Check it worked:

```sh
bobp make test                              # expect "fail 0"
bobp make run ARGS="check examples/cli"     # expect "examples/cli: part OK - ..."
```

`bobp make` writes each command's full output to `build/build.out` and posts a status line to
the team chat; the last lines are shown in your terminal.

## 3. Run an example

```sh
bobp make run ARGS="run examples/cli"              # the coffee counter (a program)
bobp make run ARGS="run examples/web"              # the sign-up wizard (an unmodified web page)
bobp make run ARGS="run examples/http"             # the vending machine (a JSON API)
bobp make run ARGS="run examples/cli --steps 5"    # stop after at most 5 moves
bobp make test-live                                # every example, real Jev, 20-step cap
```

Each Jev decision is one paid API call; a cap (`--steps`, default 50) keeps a confused part
from running up a bill. **Ctrl-C** once stops at the next safe point (the run finishes the move
it is in); a second Ctrl-C closes the app at once.

For a guided tour of what happens during those runs, read [WALKTHROUGH.md](WALKTHROUGH.md).

## 4. Read the output

**stderr** - for you to watch:

```text
understudy: playing coffee-cli (node app.mjs) - log build/runs/coffee-cli/2026-10-15T19-55-29.042Z.jsonl
understudy: step 1 asking -> size:medium (0.95)
```

The first line says what is being played and where the log is. Then one line per move:
step number, the phase, the move Jev picked, and its confidence.

**stdout and the log file** - for tools: one JSON object per line, identical in both.

```json
{"step":1,"phase":"asking","options":["size:small","size:medium","size:large"],"picked":"size:medium","move":"size:medium","confidence":0.95,"state":"waiting", "...": "..."}
{"final":true,"outcome":"done","steps":3,"state":"finished"}
```

| Field | Meaning |
|---|---|
| `options` | the moves the adapter offered at this step |
| `picked` / `move` | what Jev chose / what was actually sent (they differ only if a confidence floor fell back) |
| `confidence` | Jev's confidence in the pick, 0-1 |
| `offList`, `answer` | present when Jev's first pick was not on offer; `answer` is what it said (it was asked again) |
| `state` | where the part's statechart is after the step |
| `final` line | always last: `outcome` is `done`, `step-cap`, `app-exited`, `off-list`, `no-first-move`, `jev-error`, `interrupted` or `error` |

**Exit code**: `0` the part reached its end state; `1` the run started but could not finish
(the final line says why); `2` refused before anything started (the message says what to fix).

Logs accumulate in `build/runs/<adapter name>/`; `bobp make clean` removes them.

## 5. Write a part for your own app

The fastest route is to copy the example closest to your app and change it.

**1. Copy an example.**

```sh
cp -r examples/cli examples/myapp     # a program; examples/web for a web page, examples/http for an API
```

**2. Point the target at your app** (`examples/myapp/adapter.mjs`), and give it a new `name`:

```js
name: 'myapp',
target: { kind: 'process', command: 'python3', args: ['myapp.py'] },
// or a web page:  { kind: 'page', root: 'public', page: 'index.html' }
// or an API:      { kind: 'http', command: 'node', args: ['server.mjs'], url: 'http://127.0.0.1:{port}', state: '/status' }
//   (leave out command to play a service that is already running at a fixed url)
```

A program or API server is started in the example directory. A web page is played as it is -
nothing needs adding to it.

**For a web page, you can stop here:** an adapter with only `name` and `target` gets the
generic page app, which offers every button, link, checkbox, radio button and list option a
person could choose. Skip to step 4, and end the part with a `showing` guard (the text your
last screen shows) - see the web example's `part/turn.yaml`.

**3. Teach the adapter to read your app** (programs and APIs). Four functions (details in
[ADAPTERS.md §1](ADAPTERS.md#1-the-adapter)):

- `phase(view)` - return a name such as `'asking'`, `'done'` or `'waiting'`. Only return the
  "it is my move" phase when there is something not yet answered.
- `project(view)` - the facts Jev should see, as a small object with clear names.
- `options(state)` - the moves on offer: `[{ id: 'size:large', what: 'answer large', value: 'large' }]`.
- `act(move)` - how to make one: `{ actions: [{ input: move.value }] }` for a program,
  `{ actions: [{ method: 'POST', path: '/order', body: { ... } }] }` for an API.

**4. Edit the part.** Keep the statechart from the example; change the phase names in the
`phase` guards to the ones your `phase()` returns. Rewrite `part/questions.yaml` so Jev knows
who it is playing and what it wants - refer to your `project()` fields in backticks, and
never put a number or a quoted value in the prose.

**5. Check until it is clean.** `check` starts nothing and needs no key:

```sh
bobp make run ARGS="check examples/myapp"
```

**6. Run it with a small cap**, then raise it:

```sh
bobp make run ARGS="run examples/myapp --steps 3"
```

`bobp make run ARGS="library examples/myapp"` lists every name your part may use, including
any your adapter adds.

## 6. Troubleshooting

Every error is one line starting `understudy:`. The common ones:

| Message | Exit | What to do |
|---|---|---|
| `understudy run needs a TypeSafe key: set TYPESAFE_API_KEY` | 2 | `export TYPESAFE_API_KEY=...` |
| `<dir>: no such directory` / `not a directory` | 2 | give the example directory, e.g. `examples/cli` |
| `<dir>: no adapter.mjs - an example directory needs ...` | 2 | the folder needs `adapter.mjs`, `part/turn.yaml`, `part/questions.yaml` |
| `.../adapter.mjs: app.options must be a function` | 2 | the adapter is missing that hook |
| `.../turn.yaml: states.looking.invoke.src: no actor "lok" - did you mean "look"?` | 2 | fix the name at that path |
| `.../questions.yaml: answer.instructions carries a number in the question...` | 2 | move the value into `project()` and refer to it by path in backticks |
| `.../turn.yaml: not valid YAML - ... at line 4, column 1` | 2 | fix the YAML at that line |
| `--steps must be a positive whole number` | 2 | `--steps 20` |
| `Chromium is not installed - run: bobp make install-browser` | 2 | run it (or install your distribution's Chromium) |
| `stopped after 50 steps without reaching the end state (last state: X)` | 1 | the part never reached `type: final`: check that `phase()` returns your done phase, or raise `--steps` |
| `<command> exited with code N before the end state` | 1 | the app quit or crashed; run it by hand to see why |
| `no first move from <app> within 10 s - ...` | 1 | `phase()` never returned the move phase; for a page, nothing choosable appeared; for an API, nothing answered |
| `stalled: nothing to do for 10 s after step N ... add a showing guard` | 1 | the app stopped offering moves; if that screen is the end, add a `showing` guard for it |
| `lost the connection to <url>: ...` | 1 | the API went away mid-run; check it is still up |
| `step N: could not press button "X" - it is no longer on the page` | 1 | the page changed between the look and the move; usually a page still loading |
| `.../adapter.mjs: target.X is not a <kind> target field (known: ...)` | 2 | remove or rename the field |
| `step N: in phase "X" Jev answered off the list twice (...)` | 1 | the question or options confuse Jev: clarify the instructions or option wording |
| `step N: Jev request failed: ...` | 1 | network or key problem; the SDK's message says which |
| `unexpected error: ...` | 1 | a bug in understudy or the adapter's code - please report it with the command line |

## 7. Command reference

```text
understudy run <dir> [--steps N]   play <dir>'s part against its app (needs TYPESAFE_API_KEY)
understudy check <dir>             check <dir>'s adapter and part without starting anything
understudy library [<dir>]         list every name a part may use, with its meaning
understudy --help
```

Run them as `bobp make run ARGS="<command> ..."`.

| Make target (`bobp make <target>`) | Does |
|---|---|
| `install` | install dependencies (network) |
| `install-browser` | download Chromium for web targets (network) |
| `run` | `ARGS="run|check|library ..."` |
| `test-live` | play every example with real Jev, 20-step cap |
| `test` / `lint` / `check` | unit tests / eslint / the full gate |
| `clean` | remove `build/` (logs included) |
