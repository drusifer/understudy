# Writing a sketch

An **understudy** plays an app the way a person would: it looks at the app, works out
whether something is being asked of it, lets Jev pick one of the moves on offer, and makes
that move, until its sketch says it is done. A **sketch** is one directory with one file in
it that says everything:

```
examples/<app>/
  sketch.yaml     name, target, player settings, questions, and the turn (a statechart)
  hooks.mjs       only for a program or a JSON API: how to read what the app shows
```

Five working examples to copy:

| Example | App | Target | Code in the sketch |
|---|---|---|---|
| [`examples/cli`](../examples/cli) | a coffee counter that asks three questions on the terminal | `process` | `hooks.mjs`, 47 lines |
| [`examples/web`](../examples/web) | a three-step sign-up wizard page, unmodified | `page` | none |
| [`examples/http`](../examples/http) | a vending machine JSON API | `http` | `hooks.mjs`, 32 lines |
| [`examples/mcp`](../examples/mcp) | a cinema box office MCP server, started over stdio | `mcp` | none |
| [`examples/mcp-remote`](../examples/mcp-remote) | the same box office, already running behind a URL and a token | `mcp` | none |

Their turns are the same shape - none of them names the transport.

```sh
bobp make run ARGS="check examples/mcp"       # load and check, start nothing (no key needed)
bobp make run ARGS="run examples/mcp"         # play it (needs TYPESAFE_API_KEY)
bobp make run ARGS="library examples/cli"     # every name a turn may use, plus the hooks' own
```

`<sketch>` in every command is the directory (`examples/cli`) or the file
(`examples/cli/sketch.yaml`). A directory that still has `adapter.mjs` and `part/` from before
sprint 3 is refused: write a `sketch.yaml` instead (section 1 maps the old pieces).

---

## 1. `sketch.yaml`

```yaml
name: coffee-cli                       # required; logs go to build/runs/<name>/
description: >-                        # optional; what the stand-in does, for people
  An understudy orders a coffee at the counter ...
target: { kind: process, command: node, args: [app.mjs] }   # required; section 2
app: hooks.mjs                         # process and http: required (section 3); page: optional; mcp: not allowed
player: { floor: 0.4 }                 # optional; section 5
steps: 30                              # optional step cap; --steps wins; default 50
calls: [...]                           # mcp only; section 2
values: {...}                          # mcp only; section 2
decide: {...}                          # mcp only; section 2, "Deciding"
inputs: {...}                          # optional; section 2, "Deciding" - set with --input
pick: {...}                            # mcp only; section 2, "Deciding"
questions: { ... }                     # required; section 5
turn: { initial: waiting, states: { ... } }   # required; section 4
```

Any other top-level key is refused, naming the known ones. Every mistake is reported before
anything starts, as one line naming `sketch.yaml` and the path inside it:

```
understudy: examples/cli/sketch.yaml: turn.states.answering.on.STEP: no state "replyng" - did you mean "replying"?
understudy: examples/cli/sketch.yaml: app: hooks.mjs not found next to sketch.yaml
understudy: examples/cli/sketch.yaml: questions.answer.instructions: carries a number in the question; ...
```

If you had a sketch in the old layout: `adapter.mjs`'s `name`, `target` and `player` become
top-level keys, its `app` hooks and `library` move to `hooks.mjs`, `part/questions.yaml` goes
under `questions:` and `part/turn.yaml` under `turn:` (its `description` moves to the top).

## 2. `target` — how the app is seen and moved

### `kind: process` — a command-line program, started in the sketch directory

| Field | Meaning |
|---|---|
| `command`, `args` | what to start (`node`, `[app.mjs]`) |

Its **view** is what a person would see in a terminal:

```js
{ lines: ['Welcome to the coffee counter.', '? size [small|medium|large]', '> '],
  seq: 87,            // grows whenever anything new appears
  sent: 0,            // how many moves (input lines) have been sent
  exited: null }      // or { code, signal } once the program has ended
```

`lines` holds every line printed to stdout, including an unfinished last line (a prompt),
with each input echoed where it was typed (`> medium`). Its **action** is
`{ input: 'medium' }` — one line written to stdin. Needs `hooks.mjs`.

### `kind: page` — a web page, served from the sketch directory and opened in headless Chromium

`bobp make install-browser` if Chromium is missing. The page needs **nothing added to it**:
understudy reads it the way a screen reader does.

| Field | Default | Meaning |
|---|---|---|
| `root` | `.` | the folder to serve, relative to the sketch directory |
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
control the same way and understudy presses, ticks or picks it. A control gone by the time of
the move stops the run (`control-gone`).

With no `app:` the **generic page app** plays it:

| Hook | Does |
|---|---|
| `phase` | `'asking'` when the page has a control, else `'waiting'` |
| `project` | `{ page: title, says: text, controls }` - what Jev reads |
| `options` | one per control, id `<role>:<label>` (`button:Pro (paid monthly)`, `option:Size=Large`) |
| `act` | uses that control by role and name |

It cannot know where your app ends, so the **turn** says it, with the `showing` guard
(section 4).

### `kind: http` — a JSON API: a look is a GET of its state, a move is a request

| Field | Meaning |
|---|---|
| `url` | where it is; `{port}` is replaced by a free port when `command` starts it |
| `state` | the path a look GETs (`/machine`) |
| `command`, `args` | optional: start the server in the sketch directory (it gets `PORT`); stopped at the end |

Without `command` understudy **attaches** to a service already running at `url` and leaves it
running. Its **view**:

```js
{ status: 200, body: { credit: 0, items: [...] }, seq: 3,
  last: { method: 'POST', path: '/select', status: 402, body: { error: '...' } } | null,
  exited: null }
```

Its **action** is a request, `{ method: 'POST', path: '/coins', body: { coin: 1 } }`. An error
status (4xx/5xx) is the app's answer, not a crash: it is kept in `view.last` and in the step's
log line as `response: { status }`, and the run goes on. Needs `hooks.mjs`.

### `kind: mcp` — an MCP server, with understudy as its client

(A step-by-step guide, from an existing `.mcp.json` to a finished run: [MCP_GUIDE.md](MCP_GUIDE.md).)

The moves are the server's **tools**; understudy never needs code for it. Name the server
the way Claude Desktop and Claude Code do, in the `mcpServers` shape, either **inline**:

```yaml
target:
  kind: mcp
  server: { command: node, args: [server.mjs], env: { MODE: demo } }     # a local server, over stdio
```

or **by reference** to a file in that shape, next to the sketch:

```yaml
target: { kind: mcp, config: servers.json, server: boxoffice }
```

```json
{ "mcpServers": {
    "boxoffice": { "type": "http", "url": "http://127.0.0.1:${BOX_PORT:-8765}/mcp",
                   "headers": { "Authorization": "Bearer ${MCP_TOKEN}" } } } }
```

| Server entry | Fields | understudy |
|---|---|---|
| local | `command` (required), `args`, `env`, `type: stdio` (optional) | starts it in the sketch directory (`env` added to understudy's environment), stops it at the end |
| remote | `type: http` (required), `url` (required), `headers` | connects over streamable HTTP with those headers; never starts or stops it |

`${VAR}` and `${VAR:-default}` anywhere in the entry are filled from the environment when the
run starts (`check` needs none of them); an unset variable with no default refuses the run,
naming the variable and the file. **Put secrets in `headers`, not in the URL**: understudy
prints the URL it plays (filled in) but never a header value. Only token headers are
supported - no OAuth - and `type: sse` is refused.

Its **view**:

```js
{ tools: [{ name: 'pick_seats', description: 'Hold seats for one film.', inputSchema: { ... } }, ...],
  last: { tool: 'pick_seats', arguments: { film: 'f1', count: 2 }, isError: false,
          text: '{"hold":"h1","film":"The Long Night","count":2,"total":18}' } | null,
  seq: 3, exited: null }
```

Its **action** is one tool call, `{ tool, arguments }`. A tool that answers with an error (a
result with `isError`, or an MCP error such as an unknown tool or bad arguments) is the
server's answer: it is in `view.last` and in the step's log line, and the run goes on. Each
step's log line has `response: { call: { tool, arguments }, isError, text }`.

**The generic MCP app** offers each tool as a move, `tool:<name>`. A tool's **open
arguments** - the required ones, and optional ones you list values for - are **chosen by Jev,
never written**: after Jev picks the tool, it chooses each open argument from a list, in one
more request. The list, first non-empty wins:

1. the values the sketch lists for it: `values: { pick_seats: { count: [2] } }`;
2. what its schema allows: every `enum` value, `true`/`false`, or each whole number of an
   `integer` whose `minimum` and `maximum` are at most 19 apart;
3. the strings (for a `string`) or numbers (for a `number`/`integer`) in the last answer that
   was not an error - its structured content, or its text when that is JSON - at most 20.

So the box office's `pick_seats` is offered as soon as `list_films` has answered with film
ids. A tool with a required argument that has nothing to choose from is left out, and the run
says so once:

```
understudy: not offering tool:leave_review yet - argument "text" (string) has nothing to choose from; list values for it in sketch.yaml
```

Jev cannot write free text, so such a tool is only playable with listed values. If nothing at
all can be offered for 10 seconds the run ends (`no-first-move`, or `stalled` after step 1),
naming each tool and why.

**Fixed calls** shape the moves further: a tool listed in `calls:` is offered only as listed,
with those arguments fixed; arguments a call leaves open are still chosen by Jev.

```yaml
calls:
  - { tool: pay, arguments: { method: card } }     # offered as tool:pay(method=card); `hold` is chosen
```

Where the run ends is the turn's to say, with `showing` on text **only a result says**:
`showing` searches the whole view, tool descriptions included, so pick an end text that no
tool description contains (the box office ends on `Ticket issued`).

### Several servers

A sketch can play more than one MCP server at once - a box office and a ratings service, say.
Name them under `servers:`, inline or by reference, in the same `mcpServers` shape:

```yaml
target:
  kind: mcp
  servers:
    boxoffice: { command: node, args: [boxoffice.mjs], env: { BOX_STATE: '${BOX_STATE:-normal}' } }
    ratings:   { command: node, args: [ratings.mjs] }
# or: { kind: mcp, config: servers.json, servers: [boxoffice, ratings] }
```

Every server's tools are on offer, named `<server>/<tool>` (`tool:boxoffice/pick_seats`), so two
servers with a tool of the same name never mix; `calls:`, `values:` and `decide:` use the same
names. Step lines carry `response.call.server`. All local servers start before the first move
and stop at the end; one that will not start refuses the run naming it
(`understudy: server "ratings" did not start: ...`) and stops the others. With one server
(`server:`) nothing changes: ids stay `tool:<name>`.

### Deciding: `decide:`, `inputs:`, `pick:`

For an argument the sketch names under `decide:`, understudy does not just offer every value an
answer holds: it decides like a person (ADR-0017..0021). Each value keeps the **answer row** it
came from - the JSON object holding it, plus the plain fields of the objects around it (a
showing nested in a film carries the film's `title` and `genre`) - joined with rows from other
answers that share its `join` field. Then:

1. **Gates** - what the person never accepts. A value that fails one is removed (and the log says
   why); a value whose gate needs a fact nobody has answered yet is **held back** until it is.
2. **Scores** - what the person likes more. Each factor puts one field at a position from 0 to 1
   and its **weight bends the curve**: score = position ^ weight. A value's total is the
   **product** of its scores, so the factor weighted most counts most, and a 0 anywhere removes
   the value.
3. **Shortlist** - every total above 0, best first; Jev makes the final Choice among it (a
   shortlist of one is taken without asking). While any value is still held back, the argument
   offers nothing - every fact comes in before deciding - unless a value already scores a
   perfect 1 (shown as 11 on the dashboard): nothing can beat it, so the understudy stops looking.

```yaml
decide:
  boxoffice/seat_map.showing:          # <tool>.<argument> (<server>/<tool>.<argument> with several servers)
    join: title                        # facts about the same film from any server
    gates:
      starts: { at_least: '17:00' }
      any:                             # passes if any one group passes
        - { genre: horror, tomato: { at_least: 70 } }
        - { tomato: { at_least: 91 } }
    scores:
      tomato:   { range: [70, 100], weight: tomato }     # a weight may name an input
      audience: { ask: audience, weight: 2 }             # Jev's Score, as a factor
  boxoffice/pick_seats.seat:
    gates: { together: { at_least: 2 }, row: { in: [E, F, D] } }
    scores:
      row:    { order: [E, F, D], weight: 2 }
      centre: { range: [0.3, 1], weight: 3 }
    shortlist: { at_most: 5 }          # and/or { total: { at_least: 0.3 } }
  ratings/rating.title: {}             # no rules: values from every answer, each asked once
```

| Word | Where | Means |
|---|---|---|
| a bare value, `is` | gate | the field equals it |
| `in: [...]` | gate | the field is one of these |
| `at_least`, `at_most` | gate | numbers as numbers, `HH:MM` as times |
| `any: [group, ...]` | gate | passes if one group of gates passes |
| `range: [from, to]` | score | position runs straight from 0 at `from` to 1 at `to`, either way, clamped |
| `order: [best, ..., worst]` | score | item i of n at (n - i) / n (E, F, D: 1, 0.67, 0.33); unlisted 0 |
| `ask: <question>` | score | position is Jev's answer to a `type: score` question about the row |
| `weight` | score | a number from 0 (factor off) up, or an input's name; default 1 |
| `field`, `join` | decided argument | the answer field the values come from (default: the argument's name); the field that joins rows across answers |
| `shortlist` | decided argument | `at_most: N`, `total: { at_least: X }` |

At weight 1 rows E, F, D score 1, 0.67, 0.33; at weight 2, 1, 0.44, 0.11 - the row you want most
has the biggest bearing. A decided value used in a call that answered is **spent**: it is not
offered again (its answer is remembered). A score question used by `ask:` says what it
`looks_at` and its `levels`, worst first; Jev is asked about each new row once per run, every
row it is waiting for in one request:

```yaml
questions:
  audience:
    type: score
    looks_at: reviews
    instructions: Judging by these audience reviews, how much would someone who loves horror films enjoy this one?
    levels: [Bored, or walked out, Mixed, Solid fun, Loved it]
```

**Inputs** are what the person sets when the run starts - a choice, or a weight in a range -
with `understudy run <sketch> --input mood=romantic --input centre=1`; the start line lists
them, and a value out of range refuses the run:

```yaml
inputs:
  mood:   { choose: [fun, serious, dramatic, romantic], default: fun }
  centre: { weight: [0, 3], default: 3 }
pick:                                  # the final Choice among a shortlist
  instructions: You are choosing for yourself and a friend, in the mood for something `inputs.mood`.
  with: [mood]                         # the choice inputs Jev is told
```

**Walking away.** Guard `nothing_qualifies` (`params: { for: [<decided argument>, ...] }`) is
true when values were seen for the listed arguments and none is shortlisted or held back. A
final state tagged `walked-away` then ends the run with outcome `walked-away`, exit 0, a
`{"event":"walked-away","removed":{...}}` line and a sentence on stderr:

```
understudy: walked away - nothing qualified: starts removed 6 showings; any removed 3 showings; together removed 104 seats
```

Each step line has `decided: [{ argument, table, removed, held, jev }]` - the shortlist's score
table (each value, each factor's score, the total), what was removed and why, what is held back
and for what, and how many Jev Scores were asked or reused; the watch page shows the same.
The whole example: `examples/evening`.

## 3. `hooks.mjs` — what the view means (program and JSON API)

`app: hooks.mjs` names a module next to the sketch. Its default export has four hooks; it may
also export `library` (section 6). From `examples/http/hooks.mjs`:

```js
export default {
  phase(view) {                       // -> a phase name, tested by the turn's `phase` guard
    return view.body.dispensed?.length > 0 ? 'done' : 'asking';
  },
  project(view) { ... },              // -> the state object Jev reads
  options(state) { ... },             // -> [{ id, what, value? }] the moves on offer now
  act(move) { ... },                  // -> { actions: [<target action>, ...] }
  // propose(option, state, context)  // optional: how a move is described to rule questions
};
```

These are called by the turn's library names, never by you:

- **`phase(view, context)`** — which phase the app is in, e.g. `'asking'`, `'done'`,
  `'waiting'`. *Make it impossible to answer twice:* only say "asking" when there is a
  question that has not been answered yet. The CLI hooks compare the number of questions
  printed with `view.sent`; the vending machine answers each request before the next look.
- **`project(view, context, phase)`** — the **state** Jev reads: small, named facts
  (`topic`, `choices`, `answered_so_far`). Question prose refers to these by path, so name
  them well.
- **`options(state, phase, context)`** — the moves on offer right now, each
  `{ id, what, value? }`: `id` is unique, `<kind>:<thing>` (`size:medium`), and its **kind**
  (before the `:`) picks the wording from the question's `criteria`; `what` is plain words for
  the move; `value` is shown to Jev in backticks. Jev can only ever pick one of these. The
  **last** option is the fallback used when a pick is below the player's confidence floor.
- **`act(move, state, view, context)`** — the target actions that make `move`:
  `{ actions: [{ input: move.value }] }` for a program, `{ actions: [{ method: 'POST', path:
  '/coins', body: { coin: 1 } }] }` for an API. It may also return `say` (a line for the talk
  channel) and `tracks` (fields to keep in context, read by the `track` action).

`check` refuses hooks missing one of the four, naming it. A `page` sketch may name hooks too,
and then they replace the generic page app.

## 4. `turn:` — when to look, when to move, when it is over

An XState statechart, with every guard, action and actor taken from the library
(`understudy library`). The CLI and HTTP examples use this shape:

```yaml
turn:
  initial: waiting
  states:
    waiting:
      tags: [safe]                 # stopping here (Ctrl-C) is harmless
      on: { OBSERVE: looking }     # sent on every look at the app
    looking:
      invoke:
        src: look                  # the app's phase(view)
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

A sketch played by a generic app (page, mcp) ends by what the app **shows** instead, since a
generic app has no `done` phase - from `examples/mcp/sketch.yaml`:

```yaml
        onDone:
          - { target: finished, guard: { type: showing, params: { text: Ticket issued } } }
          - { target: choosing, guard: { type: phase, params: { is: asking } } }
          - { target: waiting }
```

`showing { text }` is true when any text in the view the last `look` read contains `text`.
Literal text is fine in `turn:` (the no-literals rule is for question prose). Forget it and the
run plays to the last screen and then **stalls**; the message says to add a `showing` guard.

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

Flat states only; no nesting. `check` refuses any unknown state, guard, action, actor or
question, naming the path in `turn:`, the bad name and the nearest known name.

## 5. `questions:` and `player:` — what Jev is asked

TypeSafe question definitions, one per name the turn uses:

```yaml
questions:
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
backticks (`topic`, `choices[0]`) and never carry a number or a quoted value — a value in the
question drifts from the value in the state. `check` refuses `Pick 2 items` and
`when it says "ready"`, naming the question.

An MCP sketch's question needs no `criteria`: each tool is described by its own name and
description, and the argument questions are made from the same instructions plus the tool's
argument and its schema description.

`player:` tunes what an unconvincing answer does: `floor` (0–1) is the confidence below which
a pick is not trusted, and `escalation` is `floor_fallback` (play the last option) or `ask`
(ask on the talk channel - none of the built-in targets has one, so `ask` is for a target of
your own).

## 6. Library names

`understudy library` lists them all with their meanings. The ones most turns need:

| Name | Kind | Does |
|---|---|---|
| `look` | actor | reads the view, outputs the app's `phase(view)` and the view |
| `phase` | guard | `{ is: <name> }` — the last `look` found that phase |
| `showing` | guard | `{ text: <text> }` — the view the last `look` read contains that text |
| `play` | actor | `{ phase, question }` — Jev picks from the options (and any open arguments), the move is made |
| `judge` | actor | `{ question }` — a yes/no/unsure Noul about the view |
| `verdict` | guard | `{ is: yes|no|unsure }` — the last judgment |
| `changed`, `quiet` | guards | the view or talk moved since the last look / nothing said for `ms` |
| `count`, `counted`, `track`, `reset` | actions/guard | simple context bookkeeping |

**Your own names** go in `hooks.mjs` as `export const library`, each with a one-line `doc`
(`check` refuses one without). They are merged with the generic names; a name defined twice
is an error. From the test fixture:

```js
export const library = {
  guards: {
    sold_out: { doc: 'the app says the item is sold out', fn: ({ event }) => event.output?.soldOut === true },
  },
};
```

Guards are `fn({ context, event }, params) => boolean`; actions are `fn(...)` or
`assign: ({ context, event }, params) => ({ field: value })`; actors are
`fn: async ({ input }) => output`, where `input` is the state's `with:` plus `context` and
`event`.

## 7. Running

```sh
understudy run <sketch> [--steps N] [--watch [--port N] [--pause]]   # cap: --steps, else steps:, else 50
understudy watch <log.jsonl> [--port N]                              # replay a finished run
```

`--watch`, `--pause` and replay are described in [USER_GUIDE.md §5](USER_GUIDE.md#5-watch-a-run).

- **stdout**: one JSON line per step — `step`, `phase`, `options`, `picked`, `move`,
  `confidence`, `state` (and `offList`/`answer` when Jev's first pick was not offered,
  `response` when the app answered the move: an HTTP status, or an MCP tool call and its
  result) — then a final line `{ "final": true, "outcome": ..., "steps": ..., "state": ... }`.
  The same lines go to `build/runs/<sketch name>/<timestamp>.jsonl`.
- **Event lines** (also on stdout and in the log, with an `event` field - skip them if you only
  want steps). They make a log a complete record that `understudy watch` can replay:
  - first: `{"event":"start","sketch":"coffee-cli","plays":"node app.mjs","turn":{...},"at":"..."}`
    - the sketch, what it plays, and its `turn:` as written;
  - each state change: `{"event":"state","from":"looking","to":"answering","on":"done: phase is asking","at":"..."}`,
    in order, around the step lines. `on` is the event (`OBSERVE`, `STEP`, `QUIT`, `done` when an
    invoked actor finished, `always`) and its guard in words. A look that ends where it began
    without a move is not listed; the next listed change carries how many there were,
    `"idle_looks": 12`;
  - before the final line of a run that did not end `done`: `{"event":"ended","outcome":"stalled","message":"..."}`
    - why it ended, as stderr said it.
- **stderr**: what is played and where the log is, then one readable line per step.
- **Off-list answers**: never sent. Jev is asked once more; a second off-list answer (for the
  move, or for one of its arguments) stops the run.
- **Waiting**: no move offered within 10 s of the start (`no-first-move`) or for 10 s after
  any move (`stalled`) ends the run - for every target.

| Exit | Meaning | Outcomes |
|---|---|---|
| 0 | reached the end state | `done` |
| 1 | started, then could not finish | `step-cap`, `stalled`, `app-exited`, `connection-lost`, `refused` (a remote MCP server answered the connection with an HTTP error), `control-gone`, `off-list`, `no-first-move`, `jev-error`, `interrupted` |
| 2 | refused before starting anything | bad arguments, broken sketch, unset `${VAR}`, no `TYPESAFE_API_KEY`, no Chromium, watch port in use |

## 8. A new kind of app

An app that is not a program, a page, a JSON API or an MCP server needs a new **target**: a
module in `src/targets/<kind>.mjs` exporting `startTarget(spec, { directory, environment })`,
which resolves an object with `view()`, `act(action)`, `talk()`, `say(text)`, `describe()`,
`exited()` and `close()`, plus its fields in `TARGET_FIELDS` in `src/sketch.mjs`.
`src/targets/http.mjs` shows the pattern, including starting a server with
`src/targets/program.mjs`; `src/apps/mcp.mjs` shows a generic app. Nothing in sketches, hooks
or the run loop changes.
