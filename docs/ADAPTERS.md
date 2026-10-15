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

Three working examples to copy:

| Example | App | Target | Adapter |
|---|---|---|---|
| [`examples/cli`](../examples/cli) | a coffee counter that asks three questions on the terminal | `process` | 51 lines |
| [`examples/web`](../examples/web) | a three-step sign-up wizard page, unmodified | `page` | 4 lines (no hooks) |
| [`examples/http`](../examples/http) | a vending machine JSON API | `http` | 36 lines |

Their parts are the same shape — none of them names the transport.

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

`understudy check` refuses an adapter that is missing `name` or `target.kind`, has a
`target` field its kind does not take, or (for `process` and `http`) lacks one of the four
`app` hooks - naming the piece. A **`page` adapter may leave out `app` entirely** and get the
generic page app (below); `check` then says `(page, generic page app)`.

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
opened in headless Chromium (`bobp make install-browser` if it is missing). The page needs
**nothing added to it**: understudy reads it the way a screen reader does.

| Field | Default | Meaning |
|---|---|---|
| `root` | `.` | the folder to serve, relative to the example directory |
| `page` | `index.html` | the page to open |

Its **view** comes from the page's accessibility snapshot:

```js
{ path: '/index.html', title: 'Sign up', seq: 992290554,      // seq changes when the page does
  text: ['Sign up', 'Which plan would you like?'],              // headings, paragraphs, text
  controls: [{ role: 'button', name: 'Free' },                  // what a person could choose
             { role: 'option', name: 'Large', list: 'Size' },
             { role: 'checkbox', name: 'Agree', checked: true }] }
```

`controls` holds the enabled buttons, links, checkboxes, radio buttons and drop-down options
(hidden and disabled ones never appear; text boxes are not offered yet). Its **action** names a
control the same way - `{ role: 'button', name: 'Free' }`, `{ role: 'option', name: 'Large',
list: 'Size' }` - and understudy presses, ticks or picks it. A control gone by the time of the
move stops the run (`control-gone`).

**The generic page app.** With no `app` in the adapter, understudy uses its own:

| Hook | Does |
|---|---|
| `phase` | `'asking'` when the page has a control, else `'waiting'` |
| `project` | `{ page: title, says: text, controls }` - what Jev reads |
| `options` | one per control, id `<role>:<label>` (`button:Pro (paid monthly)`, `option:Size=Large`) |
| `act` | uses that control by role and name |

It cannot know where your app ends, so the **part** says it, with the `showing` guard
(section 2). The web example's whole adapter:

```js
export default { name: 'signup-web', target: { kind: 'page', page: 'index.html' } };
```

**`kind: 'http'`** — a JSON API. A look is a GET of its state; a move is a request.

| Field | Meaning |
|---|---|
| `url` | where it is; `{port}` is replaced by a free port when `command` starts it |
| `state` | the path a look GETs (`/machine`) |
| `command`, `args` | optional: start the server in the example directory (it gets `PORT`); stopped at the end |

Without `command` understudy **attaches** to a service already running at `url` and leaves it
running. Its **view**:

```js
{ status: 200, body: { credit: 0, items: [...] }, seq: 3,
  last: { method: 'POST', path: '/select', status: 402, body: { error: '...' } } | null,
  exited: null }
```

Its **action** is a request, `{ method: 'POST', path: '/coins', body: { coin: 1 } }`. An error
status (4xx/5xx) is the app's answer, not a crash: it is kept in `view.last` and in the step's
log line as `response: { status }`, and the run goes on. A server that never answers (10 s),
exits, or drops the connection ends the run with a named reason.

### `app` — what the view means

These are called by the part's library names (section 4), never by you:

- **`phase(view, context)`** — which phase the app is in, e.g. `'asking'`, `'done'`,
  `'waiting'`. The part's `look` actor calls it and its `phase` guard tests the answer.
  *Make it impossible to answer twice:* only say "asking" when there is a question that has
  not been answered yet. The CLI adapter compares the number of questions printed with
  `view.sent`; the vending machine answers each request before the next look.
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
  `{ actions: [{ input: move.value }] }` for a program, `{ actions: [{ method: 'POST', path:
  '/coins', body: { coin: 1 } }] }` for an API. It may also return `say` (a line for the talk channel) and
  `tracks` (fields to keep in context, read by the `track` action).

---

## 2. The part: `part/turn.yaml`

An XState statechart in YAML, with every guard, action and actor taken from the library
(`understudy library`). The CLI and HTTP examples use this shape:

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

A hookless web part ends by what the page **shows** instead, since the generic page app has no
`done` phase - from `examples/web/part/turn.yaml`:

```yaml
      onDone:
        - { target: finished, guard: { type: showing, params: { text: Welcome aboard } } }
        - { target: answering, guard: { type: phase, params: { is: asking } } }
        - { target: waiting }
```

`showing { text }` is true when any text in the view the last `look` read contains `text`.
Literal text is fine in `turn.yaml` (the no-literals rule is for question prose). Forget it and
the run plays to the last screen and then **stalls**; the message says to add a `showing` guard.

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
last option) or `ask` (ask on the talk channel - none of the three built-in targets has one, so
`ask` is for a target of your own).

## 4. Library names

`understudy library` lists them all with their meanings. The ones most parts need:

| Name | Kind | Does |
|---|---|---|
| `look` | actor | reads the view, outputs `adapter.app.phase(view)` and the view |
| `phase` | guard | `{ is: <name> }` — the last `look` found that phase |
| `showing` | guard | `{ text: <text> }` — the view the last `look` read contains that text |
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
  `confidence`, `state` (and `offList`/`answer` when Jev's first pick was not offered,
  `response` when the app answered the move, e.g. an HTTP status) — then a
  final line `{ "final": true, "outcome": ..., "steps": ..., "state": ... }`. The same lines go
  to `build/runs/<adapter name>/<timestamp>.jsonl`.
- **stderr**: where the log is, then one readable line per step.
- **Off-list answers**: never sent. Jev is asked once more; a second off-list answer stops
  the run.
- **Waiting**: no move offered within 10 s of the start (`no-first-move`) or for 10 s after
  any move (`stalled`) ends the run - for every target.

| Exit | Meaning | Outcomes |
|---|---|---|
| 0 | reached the end state | `done` |
| 1 | started, then could not finish | `step-cap`, `stalled`, `app-exited`, `connection-lost`, `control-gone`, `off-list`, `no-first-move`, `jev-error`, `interrupted` |
| 2 | refused before starting anything | bad arguments, broken part, no `TYPESAFE_API_KEY`, no Chromium |

## 6. A new kind of app

An app that is not a program, a page or a JSON API needs a new **target**: a module in
`src/targets/<kind>.mjs` exporting `startTarget(spec, { directory })`, which resolves an
object with `view()`, `act(action)`, `talk()`, `say(text)`, `describe()`, `exited()` and
`close()`, plus its fields in `TARGET_FIELDS` in `src/part.mjs`. `src/targets/http.mjs` shows
the pattern, including starting a server with `src/targets/program.mjs`. Nothing in parts,
adapters' `app` hooks or the run loop changes.
