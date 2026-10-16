# Sprint 3 User Stories: One sketch file, and any MCP server as an app

*   **Total Points**: 15 (Tier 1)
*   **Branch**: `sprint-3`
*   **Source**: owner, 2026-10-15, in chat and recorded in `docs/BACKLOG.md` "Sprint 3": an MCP
    *target* (understudy is the client, not a server) built on `@modelcontextprotocol/sdk`; local
    (stdio) and remote (HTTP) servers; server config in the de facto `mcpServers` shape, by file
    reference or inline; one YAML file per sketch and it is the ONLY format (no back-compat);
    a sketch may list fixed calls and Jev fills the remaining arguments; remote auth is token
    headers only.
*   **Status**: Revised after Smith Gate 1 reject (TEST: argument values; FAIL: nothing offerable) — awaiting re-review
*   **Order**: UND-9 → UND-10 → UND-11 → UND-12 (each leaves `understudy` usable)

## Goal

An automation author describes everything about a stand-in in one file, `sketch.yaml` - who it
plays, what it plays against, and how it decides - and writes code only when the app needs
reading that no built-in app can do. With that, understudy gets a fourth kind of app: any MCP
server, local or remote, played through its tools with no code at all. Authors can then point a
sketch at the MCP servers they already configure for Claude and see them used the way an agent
would use them.

## Assumptions made for the owner

- **A sketch is a directory holding `sketch.yaml`** (plus whatever it plays: a program, a page,
  a server, and `hooks.mjs` where code is needed). `understudy run examples/cli` keeps working;
  naming the file itself (`understudy run examples/cli/sketch.yaml`) works too. If the owner wants
  bare files outside a directory, only the loader changes.
- **"Sketch" replaces "part" and "adapter" in what users read** (commands, messages, docs). The
  three examples keep their behaviour; only their files change. Old directories are refused with a
  message saying what to write instead - that is a refusal, not a compatibility path.
- **Jev chooses argument values, it does not write them.** Jev answers yes/no, choice and score
  questions; it cannot produce free text. So an argument is filled by Jev *choosing* among a known
  set: the values the tool's schema allows (an `enum`, `true`/`false`, a whole number in a range of
  at most 20), values the sketch lists for that argument, or values that appeared in the last
  result. A tool with a required argument that has none of these is not offered, and the run says
  so once at the start (UND-10 AC4-AC5 give the exact sets). If the owner expected free text, that needs a value source and is a later
  sprint (it is already in "Later" for page text fields).
- **A look at an MCP server shows its tools and the last call's result.** Resources and prompts
  are not read in this sprint.
- The MCP example is a tiny **cinema box office** server in `examples/mcp/`, written in this repo
  with the same SDK's server side: list today's films, pick seats, pay; the run ends when a
  ticket is issued. It can serve over stdio and, for the remote example, over HTTP with a token.

---

## STORY-UND-9: One sketch file for everything
**Points:** 5
**Depends on:** none

**As an** automation author,
**I want** to write a stand-in as one `sketch.yaml` - its name, target, player settings, step
limit, statechart and questions - with code only where my app needs it,
**so that** I read and change one file instead of three, and the web example needs no code at all.

### Acceptance Criteria
1. `examples/cli`, `examples/web` and `examples/http` each contain a `sketch.yaml` and no
   `adapter.mjs` or `part/` directory. `examples/web` has no `.mjs` file of understudy's at all;
   `examples/cli` and `examples/http` keep their app reading in a `hooks.mjs` that `sketch.yaml`
   names (`app: hooks.mjs`).
2. `understudy run examples/cli`, `run examples/web` and `run examples/http` each play to the same
   end as at the end of sprint 2 and exit 0; step lines and the log file
   (`build/runs/<sketch name>/<timestamp>.jsonl`) have the same fields as before.
3. `understudy check examples/<each>` prints one line naming the sketch, its target kind, the
   number of states and questions, and `generic app` when no hooks are named - without the key and
   without starting anything. `understudy check examples/cli/sketch.yaml` gives the same line.
4. A `steps:` value in `sketch.yaml` sets the step limit; `--steps N` on the command line wins
   over it; with neither, the limit is 50 as today.
5. Every mistake in a sketch is refused before anything starts, exit 2, as one line naming
   `sketch.yaml` and the path inside it - for example
   `examples/cli/sketch.yaml: turn.states.asking.on.STEP: no state "replyng" (states: ...)`, or
   `examples/cli/sketch.yaml: app: hooks.mjs not found next to sketch.yaml`. An unknown top-level
   key is named with the known ones.
6. A directory that still has `adapter.mjs` or `part/` and no `sketch.yaml` is refused, exit 2:
   `<dir>: no sketch.yaml - adapter.mjs and part/ are no longer read; see docs/SKETCHES.md`.
7. `understudy library examples/http` lists the generic names plus the ones `hooks.mjs` adds, as
   today with an adapter.

## STORY-UND-10: Play a local MCP server
**Points:** 5
**Depends on:** UND-9 (the sketch format)

**As an** automation author,
**I want** to name an MCP server in my sketch the way I name it for Claude, and have understudy
use its tools as an agent would,
**so that** I can exercise an MCP server I built without writing any code against it.

### Acceptance Criteria
1. `understudy run examples/mcp` starts the box office server over stdio, plays it until a ticket
   is issued, stops the server, and exits 0. `examples/mcp` contains `sketch.yaml` and the server,
   and no understudy code (no hooks).
2. The server is named in `sketch.yaml` either inline, as one `mcpServers` entry
   (`command`/`args`/`env`), or by reference (`config: servers.json`, `server: boxoffice`) to a file
   in the `mcpServers` shape that Claude Desktop and Claude Code read. Both forms play the same
   way; `examples/mcp` uses the inline form.
3. The moves on offer are the server's tools. Each step's log line names the call it made as
   `tool:<name>` with the arguments it sent, and the result's text, so the log reads without the
   server's code.
4. A sketch may list fixed calls (a tool with all its arguments given). A tool listed with some
   arguments left open, or not listed, has each open argument chosen by Jev from one of:
   - the values its schema allows: every `enum` value, `true`/`false`, or every whole number of
     an `integer` with `minimum` and `maximum` at most 20 apart;
   - the values the sketch lists for that argument (`values:`);
   - the strings and numbers in the last result that was not an error (its text and structured
     content; Phase 2 finding: a refused call must not take away the values before it) - for
     example, after `list_films` answered `[{"id":"f2","title":"Up"}]`, `pick_seats` is offered
     with `film` from `f2`, `Up`.
   Every value sent is one of these; the log line shows it.
5. A tool with a required argument that has no values from AC4 is not offered, and one stderr
   line at the start names it and the argument, e.g.
   `understudy: not offering tool:add_note - argument "text" (string) has nothing to choose from; list values for it in sketch.yaml`.
   If no tool at all can be offered for 10 seconds, the run exits 1 (outcome `no-first-move`, or
   `stalled` after step 1) naming each tool and why it is not offered; the server is stopped.
6. A tool call the server answers with an error is recorded in that step's log line with the
   error text, and the run continues - an error is the app's answer, not a crash.
7. If the server does not complete the MCP handshake within 10 seconds, the run exits 1 naming the
   command and what it printed on stderr (last lines); the server is stopped. If the server exits
   before the end state, the run exits 1 naming the command and its exit code.
8. `understudy check examples/mcp` passes without the key and without starting the server. A
   reference to a missing file, or to a server name the file does not have, is refused, exit 2,
   naming the file and the names it does have.
9. A `${VAR}` in `command`, `args`, `env`, `url` or `headers` is replaced from the environment at
   run time; an unset one refuses the run, exit 2, naming the variable and the file, and nothing
   is started.

## STORY-UND-11: Play a remote MCP server over HTTP
**Points:** 3
**Depends on:** UND-10

**As an** automation author,
**I want** to point a sketch at an MCP server that is already running behind a URL, with a token,
**so that** I can exercise a deployed server the same way as a local one.

### Acceptance Criteria
1. With the box office server started by hand in HTTP mode with a token (the command is in
   `examples/mcp-remote/README.md`), `MCP_TOKEN=<token> understudy run examples/mcp-remote` plays
   it to a ticket and exits 0, and leaves the server running.
2. `examples/mcp-remote/sketch.yaml` names the server by reference to a committed
   `servers.json` whose entry is `{ "type": "http", "url": ..., "headers": { "Authorization": "Bearer ${MCP_TOKEN}" } }`
   - Claude Code's shape. The token is never written to stdout, stderr or the log.
3. A wrong token: the run exits 1 saying the server refused the connection (with the status, e.g.
   401) and naming the URL - not the token.
4. Nothing answering at the URL: after trying for 10 seconds the run exits 1 naming the URL (the
   10 seconds count from the first connection attempt, as for the other targets - Phase 3 UAT).
5. `make test-live` plays `examples/mcp-remote` too, starting and stopping the server itself.

## STORY-UND-12: The docs teach sketches and the MCP target
**Points:** 2
**Depends on:** UND-9, UND-10, UND-11

**As a** developer writing a new sketch,
**I want** one guide to the sketch file and the four targets,
**so that** I can write a sketch for a program, a page, an API or an MCP server from the docs alone.

### Acceptance Criteria
1. `docs/SKETCHES.md` replaces `docs/ADAPTERS.md`: every `sketch.yaml` key, the four targets with
   their views and moves, when `hooks.mjs` is needed, and the MCP server config in both forms.
2. `README.md`, `docs/USER_GUIDE.md` and `docs/WALKTHROUGH.md` use `sketch.yaml` throughout and
   cover the MCP example with real run output.
3. `grep -rnE "adapter\.mjs|part/turn|part/questions" README.md docs/*.md examples src` finds
   nothing (sprint records under `docs/sprints/` and `docs/DECISIONS.md` history excepted).
4. The decisions (one sketch file; MCP target and its config) are recorded in `docs/DECISIONS.md`,
   superseding the ones they replace.

---

## Out of Scope
- OAuth for remote MCP servers (token headers only; OAuth is in "Later").
- Jev writing free text for an argument (needs a value source; see Assumptions).
- MCP resources, prompts, sampling, elicitation and notifications; the older SSE transport.
- An MCP server that exposes understudy (owner: not a goal).
- Any way to keep using `adapter.mjs` + `part/` (owner: no back-compat).
- Reading Claude's own config files (`~/.claude.json`, project `.mcp.json`) automatically - a
  sketch names its file.

## Open Questions
1. Is choosing argument values (not writing them) what the owner meant by "Jev fills
   arguments"? Owner. Assumed yes; if not, UND-10 AC4 grows a value source and likely moves a
   point from UND-12.
