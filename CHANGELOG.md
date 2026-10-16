# Changelog

## Sprint 3 — one sketch file, and any MCP server as an app (2026-10-15, branch `sprint-3`, not yet merged)

- **`sketch.yaml` is the only format**: one file holds a stand-in's name, target, player
  settings, step cap (`steps:`), questions and turn (statechart). Code only where an app needs
  reading - `hooks.mjs` for programs and JSON APIs. `adapter.mjs` and `part/` are no longer read
  (no back-compat): such a directory is refused, saying what replaced them. The three examples
  were converted; `examples/web` has no code at all. Commands take a sketch directory or the file.
- **MCP target** (`kind: mcp`): understudy is an MCP client (`@modelcontextprotocol/sdk`) and
  plays any MCP server - local over stdio, or remote over streamable HTTP with token headers.
  The server is named in Claude's `mcpServers` shape, inline or by reference to a file
  (`config: servers.json`, or a project's own `.mcp.json`); `${VAR}` / `${VAR:-default}` come
  from the environment. Tool errors are logged as the server's answer.
- **Generic MCP app**: each tool is a move; Jev **chooses** each open argument from the sketch's
  `values:`, the tool's schema, or the last successful answer (it never writes text). `calls:`
  fixes whole calls. Tools that cannot be filled are left out, and the run says why.
- Examples: `examples/mcp` (a cinema box office over stdio) and `examples/mcp-remote` (the same
  box office by URL and token). `make test-live` serves the remote one itself.
- Docs: `docs/SKETCHES.md` replaces `docs/ADAPTERS.md`; ADR-0011..0013.

## Sprint 2 — a JSON API, and web pages without changing them (2026-10-15, branch `sprint-2`, not yet merged)

- **HTTP target** (`kind: 'http'`): plays a JSON API - a look is a GET of its state, a move is a
  request. Starts the server on a free port or attaches to a running one. An error status is
  logged as the step's `response`, not treated as a crash. Example: `examples/http` (vending machine).
- **Web pages need no changes**: the page target reads the accessibility snapshot (what a screen
  reader sees) and presses, ticks or picks controls by role and name. The `window.__understudy`
  hook is gone (no back-compat).
- **Generic page app**: a web adapter can be just a name and a target; the controls on the page
  are the moves (`button:Pro (paid monthly)`). `examples/web` now has a 4-line adapter.
- **`showing` guard**: a part says what its end looks like.
- **Stalled runs end**: 10 s with nothing offered after a move ends the run (`stalled`) with a
  hint, for every target.
- `check` refuses unknown or missing target fields, naming what each field is for.
- Docs and ADR-0007..0010 updated; ADR-0002 superseded.

## Sprint 1 — MVP first run (2026-10-15, merged to `main` at 766a47c, tag `v0.1.0`)

First release of understudy: Jev-driven stand-ins that play real apps.

- `understudy run <dir> [--steps N]` plays an example's part against its app with live Jev:
  one JSON line per step on stdout and in `build/runs/<adapter>/<ts>.jsonl`, a final
  outcome line, a step cap (default 50), Ctrl-C stops at a safe state.
- Two targets: a command-line **process** and a web **page** (headless Chromium, driven
  through the page's `window.__understudy` hook).
- `understudy check <dir>` refuses broken parts before anything starts, naming file, path,
  bad name and the nearest known one; `understudy library [<dir>]` lists every name.
- Examples: `examples/cli` (coffee counter) and `examples/web` (sign-up wizard).
- Exit codes 0 done / 1 failed after starting / 2 refused before starting.
- Core (statechart parts, Jev decisions, seat) moved from recard d817d3c and generalized.
- Docs: `docs/ADAPTERS.md`, `docs/DECISIONS.md`, `docs/SDLC.md`.
