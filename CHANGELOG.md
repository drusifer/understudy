# Changelog

## Sprint 12 — one move at a time (2026-10-17, branch `sprint-12`, not yet merged)

- **STEP** and **PAUSE/RESUME** on the dashboard: STEP starts a run and makes one move, then one
  more each press; PAUSE holds a playing run before its next move; STOP ends either. ADR-0033.
- The printer opens on an **OPEN** release latch (was REMOVE).

## Sprint 11 — light and dark (2026-10-16, branch `sprint-11`, not yet merged)

- A **MODE** switch on the dashboard: **AUTO** follows the device's light/dark setting (live),
  **LIGHT** and **DARK** fix it; remembered per browser, `?mode=` on the link. Every theme has both:
  steampunk light (parchment, maple, brass), professional dark (charcoal), starship light (the
  bars on a pale screen). ADR-0032.
- The fader LEDs, slot glows and readouts shine as brightly as their fader is set (owner).
- Phones: the bay drops down under the tube; the theme switch wraps. The dashboard is served at
  the root - no token in the URL (owner; ADR-0023 amended).

## Sprint 10 — a schema for sketch.yaml (2026-10-16, branch `sprint-10`, not yet merged)

- **`schema/sketch.schema.json`**: editors with the YAML language server complete `sketch.yaml`
  keys, show what each means and underline mistakes as you type. Every example points at it;
  `docs/SKETCHES.md` "Editor help" says how to point yours. `check` is unchanged. ADR-0031.

## Between sprints (2026-10-16, on `main`)

- **A weight input is a share of the full weighting** (owner): the top of its range weighs a factor
  3, half way 1.5, the bottom turns it off - so the evening's 0-10 faders score as the old 0-3 did.
- `docs/SKETCHES.md`: a table of the four input kinds and their rules, the weight rule, and
  `when:` / `{ input: }` in the table of words.

## Sprint 9 — themes (2026-10-16, branch `sprint-9`, not yet merged)

- A **THEME** switch on the dashboard: **steampunk** (default), **professional** (light, flat, one
  blue accent) and **starship** (black screens framed by rounded orange/lilac/blue bars, pill
  buttons, condensed lettering - in the manner of the Enterprise-D's computers). Remembered per
  browser; `?theme=` on the link. ADR-0029.
- Fixed: with 0-10 weights the tube's centre orb and decision edge grew far too big; sizes now
  follow each weight's share of its range.

## Sprint 8 — behind the printer (2026-10-16, branch `sprint-8`, not yet merged)

- **REMOVE the printer** to edit the sketch's whole `sketch.yaml` in the bay behind it, with a
  cheat-sheet sticker; saved half a second after typing stops (checked first), and the state tube
  redraws as you type. Refused text is not saved and says why; read-only while a run plays.
  **REFIT PRINTER** puts it back. ADR-0028.
- The evening's weights run 0-10 (was 0-3).

## Sprint 7 — how many tickets (2026-10-16, branch `sprint-7`, not yet merged)

- **Count inputs** (`tickets: { count: [1, 4], default: 2 }`, `--input tickets=3`), shown on the
  dashboard as a **brass stepper**; weights stay analog faders.
- **`{ input: <name> }`** in `values:` lists and gate bounds: the evening holds as many seats as
  tickets, all together in one row. ADR-0027.

## Sprint 6 — the dashboard, with atmosphere (2026-10-16, branch `sprint-6`, not yet merged)

- **`understudy dashboard <folder>`**: a steampunk operations console (design approved on a
  clickable mockup, `docs/design/DASHBOARD.md`): a rack of the folder's sketches; each sketch's
  inputs as a pointer dial, coloured analog faders with Nixie readouts (`11` at the top) and
  switches with lamps; a square lit PLAY/STOP with a green READY lamp; POWER.
- **State tube**: any sketch's statechart on a round tube screen, every state and transition
  labelled; the current state glows; a power ring of the weights, and their blended colour on the
  decision edge and the centre orb.
- **Printer**: the run log printed on tractor-feed paper, score tables with 1.0 as `11`.
- **Access panels**: edit a factor's range/order, its Jev question, defaults and the moods - saved
  to `sketch.yaml` in place (comments and layout kept), checked first; POWER off and on restores the
  factory settings.
- **Switch inputs** and `when:` on gates; `examples/evening` has an evenings-only switch.
- Fonts from `@fontsource/*` (local). ADR-0023..0026.

## Sprint 5 — decide like a person (2026-10-16, branch `sprint-5`, not yet merged)

- **Several MCP servers in one sketch**: `target.servers` (inline or names in `servers.json`);
  tools are `<server>/<tool>` when there are several. One-server sketches are unchanged.
- **Deciding** (`decide:`): for a named tool argument, each value keeps its answer row (joined
  across servers by a key). **Gates** (`is`, `in`, `at_least`, `at_most` with numbers or HH:MM,
  `any`) remove or hold back; **scores** (`range`, `order`, `ask`) with weights that bend the
  curve multiply into a total; Jev makes the final Choice from the **shortlist**. Step lines and
  the watch page show the score table, what was removed and why, what is held back. A decision
  waits until nothing is held back, unless a value already scores a perfect 1. A deciding sketch
  does not repeat a call already answered with the same arguments (an LRU cache of 200, `lru-cache`).
- **Jev judges what numbers cannot**: a `type: score` question (`looks_at`, `levels`) is a
  factor - asked once per row, in one request per look.
- **Inputs**: `inputs:` declares choices and weights; `understudy run <sketch> --input
  mood=romantic --input centre=1`; `pick:` tells the final Choice the mood.
- **Walk away**: guard `nothing_qualifies` + a final state tagged `walked-away` - outcome
  `walked-away`, exit 0, and a sentence saying what removed what.
- **`examples/evening`**: the owner's night out against a box office and a ratings server
  (made-up films, scores, reviews); `BOX_STATE=full` walks away. `make test-live` checks every
  run's outcome. Docs: SKETCHES "Several servers" and "Deciding", MCP_GUIDE "Deciding like a
  person"; ADR-0017..0022.

## Sprint 4 — watch the understudy live (2026-10-15, branch `sprint-4`, not yet merged)

- **Live view**: `understudy run <sketch> --watch [--port N]` serves a page on 127.0.0.1 that
  draws the sketch's statechart, highlights the current state and the transition just taken,
  and lists each Jev decision - options, pick and confidence, chosen MCP arguments, the app's
  answer - as it is made. Opening late or reloading shows everything so far. No internet needed,
  no new dependency; watching changes nothing about the run.
- **Pause and step**: Pause stops a watched run before its next move, Step lets one move
  through, Resume lets it run; `--pause` starts paused. No Jev call while paused; the idle
  limits count running time only; Ctrl-C stops a paused run at once.
- **Replay**: `understudy watch <log.jsonl>` replays any finished run from its log alone - play,
  pause, step through each state change, click a decision to jump to it.
- **The log is the whole story**: a `start` line (sketch, what it plays, its statechart), a
  `state` line per transition (idle looks folded into `idle_looks`), and an `ended` line saying
  why a failed run stopped. Step and final lines are unchanged; skip lines with `event`.
- Docs: USER_GUIDE "Watch a run" with a screenshot, SKETCHES §7 event lines; ADR-0014..0016.

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
