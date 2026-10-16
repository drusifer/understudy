# Sprint 3 Acceptance Test Plan (UAT): One sketch file, and any MCP server as an app

*   **Owner**: Trin (per phase) / Smith (end to end) · **Date**: 2026-10-15 · **Branch**: `sprint-3` at `018d053`
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT3.md` · **Status**: PASSED — Smith approved

## 1. Scope of Acceptance Testing

UND-9 (one `sketch.yaml`, examples converted, old layout refused), UND-10 (local MCP server over
stdio, generic MCP app, Jev-chosen arguments), UND-11 (remote MCP over streamable HTTP with a
token header), UND-12 (docs), through the real `understudy` command. Live runs use real Jev
(owner-approved, capped at 20 steps). Out of scope: OAuth, SSE, MCP resources/prompts, free-text
arguments without listed values (stories' Out of Scope).

## 2. Preconditions & Test Environment Setup

| Item | Value |
|---|---|
| Machine | Raspberry Pi (linux arm64), Node v24, Playwright 1.62.1 Chromium, `@modelcontextprotocol/sdk` 1.32.1 |
| Setup | `bobp make install` from clean (Tank's sdlc-check, 018d053) |
| Key | `TYPESAFE_API_KEY` set; unset for key tests. `MCP_TOKEN`/`BOX_PORT` for the remote example |
| Remote server | `node examples/mcp/server.mjs --http --port <p> --token <t>`, started by hand (or by `make test-live`) |
| Evidence | outputs posted to `agents/CHAT.md`; logs in `build/runs/{coffee-cli,signup-web,vending-http,boxoffice-mcp,boxoffice-remote}/` |

## 3. Scenario-Driven Acceptance Test Cases

### `UAT-UND9-01`: the three converted examples play as before
`bobp make test-live` → coffee-cli 3 steps, vending-http 2, signup-web 3, outcome `done`, exit 0;
step lines carry the sprint 2 fields; logs under `build/runs/<sketch name>/`. **PASS** (Phase 1,
again in Phase 3).

### `UAT-UND9-02`: check by directory and by file
`check examples/cli` and `check examples/cli/sketch.yaml` both print
`examples/cli: sketch OK - coffee-cli (process, hooks.mjs) - 5 states, 1 question`; web and mcp
say `generic app`; no key, nothing started. **PASS**.

### `UAT-UND9-03`: the step cap's precedence
`steps: 2` in a sketch caps at 2; `--steps 4` wins over it; neither → 50
(`tests/run.test.js`). **PASS**.

### `UAT-UND10-01`: play the box office over stdio, live
`bobp make run ARGS="run examples/mcp --steps 20"` → `tool:list_films`, `tool:pick_seats`
(film `f1`, count 2, chosen by Jev), `tool:pay` (hold `h1`, method `card`), `Ticket issued`,
outcome `done`, exit 0; three `not offering ... yet` lines at the start, once each; no
understudy code in `examples/mcp`. **PASS** (twice).

### `UAT-UND10-02`: both config forms, fixed calls, listed values
Inline entry (`examples/mcp`) and file reference (`examples/mcp-remote`, `tests/sketch.test.js`)
play the same way; `calls: [{ tool: pay, arguments: { method: card } }]` is offered as
`tool:pay(method=card)` with `hold` still chosen; `values: { pick_seats: { count: [2] } }`
replaces the schema's 1-4. **PASS**.

### `UAT-UND10-03`: a tool error is the server's answer
End-to-end test pays `cash` first: step 3 `response.isError: true`, text "This box office takes
cards only.", step 4 pays `card`, outcome `done`. **PASS**.

### `UAT-UND11-01`: play the remote box office, live
Server started by hand on port 18770; `MCP_TOKEN=<t> BOX_PORT=18770 understudy run
examples/mcp-remote` → 3 steps, `tool:pay(method=card)`, exit 0; the server still answers
afterwards; the token is in no stdout, stderr or log line. **PASS**.

### `UAT-UND11-02`: `make test-live` serves and stops the remote server itself
Five examples green; `ps` shows no box office left running. **PASS**.

### `UAT-UND12-01`: docs
Every `check`/`library`/`--help`/no-key command in README, USER_GUIDE, WALKTHROUGH and SKETCHES
gives the documented line; anchors resolve; ADR-0011..0013 recorded; the AC3 grep hits only the
amended exceptions. Cold read: an MCP sketch can be written from SKETCHES §2 alone. **PASS**.

## 4. Negative & Error Handling Test Cases

| ID | Scenario | Expected (exit) | Result |
|---|---|---|---|
| `UAT-ERR-01` | old `adapter.mjs` + `part/` directory | `<dir>: no sketch.yaml - adapter.mjs and part/ are no longer read; see docs/SKETCHES.md` (2) | PASS |
| `UAT-ERR-02` | turn typo `STEP: replyng` | `.../sketch.yaml: turn.states.answering.on.STEP: no state "replyng" - did you mean "replying"?` (2) | PASS |
| `UAT-ERR-03` | `app: hooks.mjs` with the file missing | `.../sketch.yaml: app: hooks.mjs not found next to sketch.yaml` (2) | PASS |
| `UAT-ERR-04` | unknown top-level key | `.../sketch.yaml: adapter: not a sketch key (known: ...)` (2, unit) | PASS |
| `UAT-ERR-05` | unset `${BOX_DB}` in a server's env | `.../sketch.yaml: ${BOX_DB} is not set - set BOX_DB ...` (2), nothing started | PASS |
| `UAT-ERR-06` | server exits 4 before the handshake | `... exited with code 4 before the MCP handshake - it printed: boom` (1) | PASS |
| `UAT-ERR-07` | server never answers the handshake | `... did not answer the MCP handshake within 0.3 s - it printed nothing on stderr` (1, unit) | PASS |
| `UAT-ERR-08` | only a free-text tool | `no first move from node server.mjs within 10 s - nothing can be offered: tool:note - argument "text" (string) has nothing to choose from; ...` (1) | PASS |
| `UAT-ERR-09` | server killed mid-run | outcome `app-exited` (1, unit) | PASS |
| `UAT-ERR-10` | argument off the list twice | `step 2: in phase "asking" Jev answered off the list twice for argument "film" of pick_seats (...) - offered: ...` (1, unit) | PASS |
| `UAT-ERR-11` | wrong token | `the MCP server at http://127.0.0.1:18770/mcp refused the connection (HTTP 401)` (1), no token printed | PASS |
| `UAT-ERR-12` | `MCP_TOKEN` unset | `examples/mcp-remote/servers.json: ${MCP_TOKEN} is not set ...` (2) | PASS |
| `UAT-ERR-13` | nothing at the URL | `no first move from http://127.0.0.1:18799/mcp: nothing answered within 10 s (ECONNREFUSED)` (1) after 10 s of trying | PASS (AC4 reworded: 10 s count from the first attempt) |
| `UAT-ERR-14` | unknown server name in `servers.json` | `target.server: no server "bx" in servers.json (it has: box)` (2) | PASS |

## 5. Defect Summary & Gate Outcome

| Defect ID | Severity | Description | Assignee | Status |
|---|---|---|---|---|
| `DEF-07` | Major | a refused tool call erased the argument candidates the call before it offered (`pay` no longer offerable after a `cash` refusal) | Neo | Resolved in Phase 2 (b7ddba1): candidates from the last non-error result |
| `DEF-08` | Minor | UND-12 AC3 grep contradicted UND-9 AC6 (refusal must name the old files) | Cypher | Resolved: AC3 lists its exceptions |
| `DEF-09` | Major | an absolute `config:` path (a project's own `.mcp.json`) was glued onto the sketch directory and refused | Neo | Resolved at close: `path.resolve`, test in `tests/mcpConfig.test.js` |

### `UAT-SMITH-01`: a real MCP server from Claude's own config (end to end)
A sketch written from SKETCHES.md alone, `target: { kind: mcp, config: <project>/.mcp.json, server: via }`
→ after DEF-09, `check` OK; the first run said which arguments had nothing to choose from
(`via_query` takes an `args` array, `via_ask` a `query`) and stopped `no-first-move` naming
both; with `values: { via_ask: { query: [...] } }` it played `tool:via_ask` twice with Jev
choosing the query, logged via's own error answers, and stopped at the 2-step cap (the
sketch had no end). **PASS**.

**Gate outcome**: PASSED - Smith approved. rubric UAT: COVER=S STEPS=A FAIL=S DATA=A EVID=A.
