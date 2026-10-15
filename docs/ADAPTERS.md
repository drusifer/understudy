# Writing an adapter

An **understudy** plays an app the way a person would: it looks at the app, works out
whether something is being asked of it, lets Jev pick one of the moves on offer, and makes
that move, until its **part** says it is done. You give it three things, all in one
**example directory**:

```
examples/<app>/
  adapter.mjs           what the app looks like and which moves it offers   (code, small)
  part/turn.yaml        when to look, when to move, when it is over         (a statechart)
  part/questions.yaml   what Jev is asked                                   (TypeSafe questions)
```

Two working examples to copy:

| Example | App | Target | Adapter |
|---|---|---|---|
| [`examples/cli`](../examples/cli) | a coffee counter that asks three questions on the terminal | `process` | 51 lines |
| [`examples/web`](../examples/web) | a three-step sign-up wizard page | `page` | 24 lines |

Their parts are the same shape — neither part names the transport.

```sh
bobp make run ARGS="check examples/cli"       # load and check, start nothing (no key needed)
bobp make run ARGS="run examples/cli"         # play it (needs TYPESAFE_API_KEY)
bobp make run ARGS="library examples/cli"     # every name a part may use, plus the adapter's own
```

---

## 1. The adapter

`adapter.mjs` default-exports one object:

```js
export default {
  name: 'coffee-cli',                        // logs go to build/runs/<name>/
  target: { kind: 'process', command: 'node', args: ['app.mjs'] },
  app: {
    phase(view, context) {},                 // -> a phase name, tested by the part's `phase` guard
    project(view, context, phase) {},        // -> the state object Jev reads
    options(state, phase, context) {},       // -> [{ id, what, value? }] the moves on offer now
    act(move, state, view, context) {},      // -> { actions: [<target action>, ...] }
    propose(option, state, context) {},      // optional: how a move is described to rule questions
  },
  library: { guards: {}, actions: {}, actors: {} },   // optional: names of your own (section 4)
  player: { floor: 0, escalation: 'floor_fallback' },  // optional: see section 3
};
```

`understudy check` refuses an adapter that is missing any of `name`, `target.kind` or the
four required `app` hooks, naming the missing piece.

### `target` — how the app is seen and moved

**`kind: 'process'`** — a command-line program, started in the example directory.

| Field | Meaning |
|---|---|
| `command`, `args` | what to start (`node`, `['app.mjs']`) |

Its **view** is what a person would see in a terminal:

```js
{ lines: ['Welcome to the coffee counter.', '? size [small|medium|large]', '> '],
  seq: 87,            // grows whenever anything new appears
  sent: 0,            // how many moves (input lines) have been sent
  exited: null }      // or { code, signal } once the program has ended
```

`lines` holds every line printed to stdout, including an unfinished last line (a prompt),
with each input echoed where it was typed (`> medium`). Its **action** is
`{ input: 'medium' }` — one line written to stdin. A program has no talk channel.

**`kind: 'page'`** — a web page, served from the example directory on `127.0.0.1` and
opened in headless Chromium (`bobp make install-browser` if it is missing).

| Field | Default | Meaning |
|---|---|---|
| `root` | `.` | the folder to serve, relative to the example directory |
| `page` | `index.html` | the page to open |
| `hook` | `__understudy` | the global the page exposes |

The page cooperates by exposing a hook, as the web example's `app.js` does:

```js
globalThis.__understudy = {
  view: () => ({ screen, seq, buttons: [...] }),   // required; must include a changing `seq`
  act: ({ press }) => { /* click the button */ },  // required; receives your action as-is
  talk: () => [{ name, text }],                    // optional talk channel
  say: (text) => {},                               // optional
};
```

The page's **view** and **action** are whatever your hook returns and accepts. Keep the hook
to reading the page and pressing what is on it, so a run exercises the real app. A page that
has not exposed `view` within 10 s stops the run (exit 1), naming the URL and what the page
showed.

### `app` — what the view means

These are called by the part's library names (section 4), never by you:

- **`phase(view, context)`** — which phase the app is in, e.g. `'asking'`, `'done'`,
  `'waiting'`. The part's `look` actor calls it and its `phase` guard tests the answer.
  *Make it impossible to answer twice:* only say "asking" when there is a question that has
  not been answered yet. The CLI adapter compares the number of questions printed with
  `view.sent`; the web page re-renders synchronously, so its buttons are always current.
- **`project(view, context, phase)`** — the **state** Jev reads: small, named facts
  (`topic`, `choices`, `answered_so_far`). Question prose refers to these by path
  (section 3), so name them well.
- **`options(state, phase, context)`** — the moves on offer right now. Each is
  `{ id, what, value? }`:
  - `id` — unique, `<kind>:<thing>` (`size:medium`, `plan:free`); the **kind** (before the
    `:`) picks the wording from the question's `criteria`.
  - `what` — plain words for the move, used when the question has no wording for its kind.
  - `value` — the concrete value, shown to Jev in backticks after the wording.

  Jev can only ever pick one of these: an off-list answer is never sent (section 5). The
  **last** option is the fallback used when a pick is below the player's confidence floor.
- **`act(move, state, view, context)`** — the target actions that make `move`:
  `{ actions: [{ input: move.value }] }` for a program, `{ actions: [{ press: 'free' }] }`
  for the web example. It may also return `say` (a line for the talk channel) and
  `tracks` (fields to keep in context, read by the `track` action).

---

## 2. The part: `part/turn.yaml`

An XState statechart in YAML, with every guard, action and actor taken from the library
(`understudy library`). Both examples use this shape:

```yaml
initial: waiting
states:
  waiting:
    tags: [safe]                 # stopping here (Ctrl-C) is harmless
    on: { OBSERVE: looking }     # sent on every look at the app
  looking:
    invoke:
      src: look                  # adapter.app.phase(view)
      onDone:
        - { target: answering, guard: { type: phase, params: { is: asking } } }
        - { target: finished, guard: { type: phase, params: { is: done } } }
        - { target: waiting }
  answering:
    tags: [move]                 # "it is my move" - the run takes one step
    on: { STEP: replying }
  replying:
    invoke: { src: play, with: { phase: asking, question: answer }, onDone: waiting }
  finished:
    type: final                  # the run ends here, exit 0
```

| Piece | Meaning |
|---|---|
| `OBSERVE` | sent each time the app is looked at, with `view`, `talk`, `changed`, `quietFor` |
| `STEP` | sent when the run takes a step in a state tagged `move` |
| `QUIT` | sent on Ctrl-C; the machine stops at the next state tagged `safe` |
| tag `move` | it is the understudy's move |
| tag `safe` | stopping here is harmless (at least one must be reachable) |
| `busy` | added for you to every state that invokes something; the run waits it out |
| `type: final` | the end state |
| `left` | reserved — the state a stopped understudy goes to |

Flat states only; no nesting. `understudy check` refuses any unknown state, guard, action,
actor or question, naming the file, the path in it, the bad name and the nearest known name.

## 3. The questions: `part/questions.yaml`

TypeSafe question definitions, one per name the turn file uses:

```yaml
answer:
  type: choice                       # choice | noul | score
  instructions: >-
    You are a person ordering a coffee at a counter. The counter is asking about
    `topic`; `answered_so_far` is what you already chose ...
  criteria:                          # wording per option KIND (the id before ':')
    size: answer this size
    milk: answer this milk choice
```

**No literals in the prose.** Instructions, criteria and levels refer to state by path in
backticks (`topic`, `choices[0]`) and never carry a number or a quoted value — a value in
the question drifts from the value in the state. `check` refuses `Pick 2 items` and
`when it says "ready"`, naming the question.

`player` in the adapter tunes what an unconvincing answer does: `floor` (0–1) is the
confidence below which a pick is not trusted, and `escalation` is `floor_fallback` (play the
last option) or `ask` (ask on the talk channel; page targets with `talk`/`say` only).

## 4. Library names

`understudy library` lists them all with their meanings. The ones most parts need:

| Name | Kind | Does |
|---|---|---|
| `look` | actor | reads the view, outputs `adapter.app.phase(view)` |
| `phase` | guard | `{ is: <name> }` — the last `look` found that phase |
| `play` | actor | `{ phase, question }` — Jev picks from `options`, the move is made |
| `judge` | actor | `{ question }` — a yes/no/unsure Noul about the view |
| `verdict` | guard | `{ is: yes|no|unsure }` — the last judgment |
| `changed`, `quiet` | guards | the view or talk moved since the last look / nothing said for `ms` |
| `count`, `counted`, `track`, `reset` | actions/guard | simple context bookkeeping |

**Your own names** go in the adapter's `library`, each with a one-line `doc` (`check`
refuses one without). They are merged with the generic names; a name defined twice is an
error. From the test fixture:

```js
library: {
  guards: {
    sold_out: { doc: 'the app says the item is sold out', fn: ({ event }) => event.output?.soldOut === true },
  },
},
```

Guards are `fn({ context, event }, params) => boolean`; actions are
`fn(...)` or `assign: ({ context, event }, params) => ({ field: value })`; actors are
`fn: async ({ input }) => output`, where `input` is the state's `with:` plus `context` and
`event`.

## 5. Running

```sh
understudy run <dir> [--steps N]     # default cap 50
```

- **stdout**: one JSON line per step — `step`, `phase`, `options`, `picked`, `move`,
  `confidence`, `state` (and `offList`/`answer` when Jev's first pick was not offered) — then a
  final line `{ "final": true, "outcome": ..., "steps": ..., "state": ... }`. The same lines go
  to `build/runs/<adapter name>/<timestamp>.jsonl`.
- **stderr**: where the log is, then one readable line per step.
- **Off-list answers**: never sent. Jev is asked once more; a second off-list answer stops
  the run.

| Exit | Meaning | Outcomes |
|---|---|---|
| 0 | reached the end state | `done` |
| 1 | started, then could not finish | `step-cap`, `app-exited`, `off-list`, `no-first-move`, `jev-error`, `interrupted` |
| 2 | refused before starting anything | bad arguments, broken part, no `TYPESAFE_API_KEY`, no Chromium |

## 6. A new kind of app

An app that is neither a program nor a page needs a new **target**: a module in
`src/targets/<kind>.mjs` exporting `startTarget(spec, { directory })`, which resolves an
object with `view()`, `act(action)`, `talk()`, `say(text)`, `describe()`, `exited()` and
`close()` — see `src/targets/process.mjs` (about 70 lines). An HTTP target is planned this way:
`view` a GET, `act` a request. Nothing in parts, adapters' `app` hooks or the run loop changes.
