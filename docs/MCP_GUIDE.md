# Playing your MCP server

How to point understudy at an MCP server you already have - one you configured for Claude, one
you are building, or one running somewhere behind a URL - and get a stand-in using its tools
the way an agent would.

TLDR:
    Write one sketch.yaml naming the server (inline, or by reference to a .mcp.json) - no code.
    `check` it, then run with a small cap and read the "not offering ... yet" lines.
    Jev chooses every argument from a list: the schema's values, values you list, or the last good answer.
    Text arguments need `values:` - Jev never writes text (constrained automation, ADR-0013).
    End the run with `showing` on text only a tool result says; read the log's `response` per step.
    Reference: SKETCHES.md §2 "kind: mcp". Worked box-office example: WALKTHROUGH.md §5.

## Contents

1. [What understudy does with an MCP server](#1-what-understudy-does-with-an-mcp-server)
2. [Name the server](#2-name-the-server)
3. [Write the sketch](#3-write-the-sketch)
4. [First run: read what is not offered](#4-first-run-read-what-is-not-offered)
5. [Give Jev something to choose](#5-give-jev-something-to-choose)
6. [Say where it ends](#6-say-where-it-ends)
7. [Read the log](#7-read-the-log)
8. [A remote server with a token](#8-a-remote-server-with-a-token)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What understudy does with an MCP server

understudy is the server's **client**. Each step it:

1. lists the server's tools (and keeps the answer to the last call);
2. offers Jev every tool it can call right now - a tool is a **move**;
3. when Jev has picked a tool, asks Jev once more to **choose** each open argument from a list;
4. makes the call and logs the call and the answer.

Jev only ever chooses; it never writes a value. That keeps every run bounded and every value
traceable: whatever was sent was on a list you can see in the log. The price is that an
argument needs something to choose from - most of this guide is about giving it that.

A tool that answers with an error (bad arguments, "not found", a refused payment) is the
server's answer, not a crash: it is logged and the run goes on, the way an agent would read the
error and try something else.

## 2. Name the server

understudy reads servers in the same `mcpServers` shape Claude Desktop and Claude Code use, so
the server you already configured for Claude works as it is. Two ways:

**By reference** - point at the file and name the entry. A path is relative to the sketch, or
absolute:

```yaml
target: { kind: mcp, config: ../../.mcp.json, server: via }
```

**Inline** - copy the entry into the sketch:

```yaml
target:
  kind: mcp
  server: { command: node, args: [server.mjs], env: { LOG_LEVEL: warn } }
```

A local server (`command`, `args`, `env`) is started in the sketch's directory and stopped at
the end; a remote one (`type: http`, `url`, `headers`) is only connected to (section 8).
`${VAR}` and `${VAR:-default}` anywhere in the entry come from the environment when the run
starts.

## 3. Write the sketch

Make a directory for it and copy the box office's sketch as a start:

```sh
mkdir -p my-sketches/via
cp examples/mcp/sketch.yaml my-sketches/via/
```

Then change three things: the `name`, the `target`, and the question's instructions - who Jev
is and what it wants. Here is a complete sketch for the `via`
code-index server this repository uses in its own `.mcp.json`:

```yaml
name: via-explorer
description: >-
  An understudy explores a code index the way a new developer would.
target: { kind: mcp, config: ../../.mcp.json, server: via }

questions:
  next:
    type: choice
    instructions: >-
      You are a developer new to this code base. `tools` are what the code index offers and
      `last_call` is what it last told you. Choose what to look up next to learn how a run starts.

turn:
  initial: waiting
  states:
    waiting: { tags: [safe], on: { OBSERVE: looking } }
    looking:
      invoke:
        src: look
        onDone:
          - { target: choosing, guard: { type: phase, params: { is: asking } } }
          - { target: waiting }
    choosing: { tags: [move], on: { STEP: acting } }
    acting: { invoke: { src: play, with: { phase: asking, question: next }, onDone: waiting } }
    finished: { type: final }
```

The question needs no `criteria`: each tool is described to Jev by its own name and
description. Keep the prose free of numbers and quoted values (refer to `tools` and `last_call`
in backticks instead) - `check` refuses them.

Check it - this reads the config file and the entry but starts nothing and needs no key:

```sh
bobp make run ARGS="check my-sketches/via"
```

```text
my-sketches/via: sketch OK - via-explorer (mcp, generic app) - 5 states, 1 question
```

## 4. First run: read what is not offered

Run with a tiny cap; each step costs Jev calls:

```sh
bobp make run ARGS="run my-sketches/via --steps 2"
```

The first run of a new sketch usually stops before it moves. This is the real first run of the
sketch above:

```text
understudy: playing via-explorer (.../python -m via mcp serve --no-web ...) - log build/runs/via-explorer/....jsonl
understudy: not offering tool:via_query yet - argument "args" (array) has nothing to choose from; list values for it in sketch.yaml
understudy: not offering tool:via_ask yet - argument "query" (string) has nothing to choose from; list values for it in sketch.yaml
understudy: no first move from ... within 10 s - nothing can be offered: tool:via_query - argument "args" (array) has nothing to choose from; ...
```

Those lines are the to-do list. Each names a tool, the required argument that blocks it, and
its type. Nothing is wrong with the server - the sketch just has not said what Jev may choose.

## 5. Give Jev something to choose

An open argument (every required one, plus optional ones you list values for) is filled from
the first of these that has anything in it:

| Source | Example | You do |
|---|---|---|
| **your `values:`** | `query: ['what calls startTarget']` | list them in the sketch |
| **the schema** | `"enum": ["card", "cash"]`, `"type": "boolean"`, an integer with `minimum` 1 and `maximum` 4 | nothing |
| **the last good answer** | `list_films` answered `[{"film":"f1",...}]`, so `pick_seats` can take `film: "f1"` | nothing - call order does it |

The third source is what makes tools chain: an id one tool returns becomes a choice for the next
tool's argument. It reads strings (for a `string` argument) or numbers (for `number`/`integer`)
out of the last answer that was **not** an error - its structured content, or its text when that
is JSON - up to 20 of them. A refused call does not wipe them.

Text that comes from nowhere - a search query, a note, a review - has to be listed. For the via
sketch:

```yaml
values:
  via_ask: { query: ['what calls startTarget', 'where is the run loop'] }
```

Each listed value is sent exactly as written, so an array or object argument takes whole arrays
or objects as its values - in whatever shape the tool's schema asks for.

**Fixed calls.** To pin a whole call, or some of its arguments, list it under `calls:`. A tool
listed there is offered only as listed; arguments a call leaves out are still chosen:

```yaml
calls:
  - { tool: pay, arguments: { method: card } }   # offered as tool:pay(method=card); `hold` is still chosen
```

Use `calls:` to take a choice away from Jev on purpose (always pay by card), and `values:` to
give it a menu.

With the `values:` above, the via sketch plays:

```text
understudy: not offering tool:via_query yet - argument "args" (array) has nothing to choose from; list values for it in sketch.yaml
understudy: step 1 asking -> tool:via_ask (1)
understudy: step 2 asking -> tool:via_ask (1)
understudy: stopped after 2 steps without reaching the end state (last state: choosing)
```

`via_query` stays out (no values for it), which is fine - a tool you never list for is simply
not part of the run. The run stopped at the cap because this sketch has no end yet.

## 6. Say where it ends

A generic MCP sketch has no "done" phase of its own; the turn says what the end looks like,
with the `showing` guard on text a tool answer contains. From the box office:

```yaml
    looking:
      invoke:
        src: look
        onDone:
          - { target: finished, guard: { type: showing, params: { text: Ticket issued } } }
          - { target: choosing, guard: { type: phase, params: { is: asking } } }
          - { target: waiting }
```

Pick text that **only a result** says. `showing` searches the whole view - tool names and
descriptions too - so an end text that appears in a description ends the run at the first look.

Some sketches are explorations with no natural end, like the via one. Leave out the
`showing` line and let the cap end them: the run exits 1 with outcome `step-cap`, and the log
still has every call.

## 7. Read the log

Every step is one JSON line on stdout and in `build/runs/<sketch name>/<timestamp>.jsonl`.
For an MCP sketch the useful part is `response` - the call as sent and what came back:

```json
{"step":2,"phase":"asking","options":["tool:list_films","tool:pick_seats","tool:pay","tool:leave_review"],
 "picked":"tool:pick_seats","move":"tool:pick_seats","confidence":1,
 "response":{"call":{"tool":"pick_seats","arguments":{"film":"f1","count":2}},"isError":false,
             "text":"{\"hold\":\"h1\",\"film\":\"The Long Night\",\"count\":2,\"total\":18}"},
 "state":"waiting"}
```

- `options` - the moves that could be offered at that step (what was *not* there is often the
  interesting part).
- `response.call.arguments` - the values Jev chose (or you fixed).
- `response.isError` / `text` - the server's answer, first 2000 characters. A server that
  reports errors inside a normal answer (as via does, with `"output_type": "error"`) shows
  `isError: false` - that is how the server chose to answer.
- the last line - `{"final":true,"outcome":"done"|"step-cap"|...}`.

Two Jev calls per step when a tool has open arguments (the move, then its arguments); one
otherwise.

## 8. A remote server with a token

A server already running behind a URL is an entry with `type: http`. Keep it in a file next
to the sketch so the token stays out of it:

```json
{ "mcpServers": {
    "boxoffice": { "type": "http", "url": "https://mcp.example.com/mcp",
                   "headers": { "Authorization": "Bearer ${MCP_TOKEN}" } } } }
```

```yaml
target: { kind: mcp, config: servers.json, server: boxoffice }
```

```sh
MCP_TOKEN=... bobp make run ARGS="run my-sketches/boxoffice --steps 5"
```

- understudy prints the URL it plays, never a header value - so put secrets in `headers`, not
  in the URL.
- It connects, retrying for 10 s while nothing answers; it never starts or stops a remote
  server.
- Token headers only: OAuth logins and the old `sse` transport are not supported.

`examples/mcp-remote` is a working copy of this, against the box office served locally over
HTTP - [its README](../examples/mcp-remote/README.md) has the two commands.

## 9. Troubleshooting

| You see | Exit | Means / do |
|---|---|---|
| `not offering tool:X yet - argument "a" (type) has nothing to choose from` | - | list `values:` for it, or let an earlier tool's answer supply them; ignore it if you do not want that tool played |
| `no first move from ... - nothing can be offered: ...` | 1 | no tool could be offered for 10 s: the lines above say which arguments to give values for |
| `.../sketch.yaml: target.config: X not found` | 2 | the config path is wrong (relative to the sketch, or absolute) |
| `target.server: no server "x" in .mcp.json (it has: ...)` | 2 | use one of the names listed |
| `.../servers.json: ${MCP_TOKEN} is not set` | 2 | export it, or give a default `${MCP_TOKEN:-value}` |
| `target.server.type: sse servers are not supported` | 2 | use the server's streamable HTTP endpoint (`type: http`) |
| `... exited with code N before the MCP handshake - it printed: ...` | 1 | the server could not start; its last stderr lines say why - run its command by hand |
| `... did not answer the MCP handshake within 10 s` | 1 | the server started but never spoke MCP on stdout (wrong command, or it logs to stdout) |
| `the MCP server at <url> refused the connection (HTTP 401)` | 1 | wrong or missing token |
| `no first move from <url>: nothing answered within 10 s (ECONNREFUSED)` | 1 | nothing listening at that URL |
| `lost the connection to ...` / `exited with code N before the end state` | 1 | the server went away mid-run |
| `Jev answered off the list twice for argument "a" of X` | 1 | the list for that argument confuses Jev - give clearer `values:` or fix the call |
| `stopped after N steps without reaching the end state` | 1 | no `showing` end matched (or none was given): check the end text appears in a result |

More: the full `sketch.yaml` reference is [SKETCHES.md](SKETCHES.md); the box office taken
apart call by call is [WALKTHROUGH.md §5](WALKTHROUGH.md#5-the-mcp-examples-a-cinema-box-office).
