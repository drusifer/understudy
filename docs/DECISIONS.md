# Decisions

Newest first. Each record follows `agents/templates/_template_DECISION.md`, kept short.
Sprint 1 records were made by Morpheus in `docs/sprints/ARCH_SPRINT1.md` §8, sprint 2
records in `docs/sprints/ARCH_SPRINT2.md` §8 and sprint 3 records in
`docs/sprints/ARCH_SPRINT3.md` §8 and sprint 4 records in `docs/sprints/ARCH_SPRINT4.md` §8
(all approved at Smith Gate 2, 2026-10-15). Records before
ADR-0011 say "adapter" and "part"; since ADR-0011 those are `hooks.mjs` and `sketch.yaml`.

---

## ADR-0016: Pause is a gate before each move; no Jev call while paused

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-15
*   **Context**: owner: pause and step a live run from the watch page. A pause must not let Jev be asked anything, must not trip the 10 s first-move/stall limits, and Ctrl-C must still stop the run.
*   **Options**: (1) a gate in the run loop before `takeStep` (the Jev request is inside the step); (2) pause the seat's looking too; (3) pause by suspending the app.
*   **Decision**: (1). `gate.beforeMove()` waits while paused; Step lets one move through, Resume opens it. Idle limits subtract paused time. Ctrl-C releases a *paused* run straight to stop (`interrupted`, no move - QUIT alone would wait for a safe state, which a move state is not); a running watched run stops as any run does, so `--watch` alone changes nothing.
*   **Consequences**: + a paused run is fully still and cheap. − pause takes effect at the next move: until the app offers one, the understudy keeps looking.

## ADR-0015: The watch page is served by understudy and draws its own statechart

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-14, UND-16
*   **Context**: owner: a browser page showing the statechart, state changes and Jev decisions live, plus replay. Must work offline and on the Pi.
*   **Options**: (1) node:http + Server-Sent Events + a small layered SVG layout of our own; (2) Mermaid for the diagram (122 MB unpacked, re-render to highlight); (3) a WebSocket library; (4) a terminal UI.
*   **Decision**: (1). The server binds 127.0.0.1 with a per-run token path, serves only the page's own files, streams history then live lines then `end`; `/control` in live mode only. Live and replay are the same page fed the same events; replay frames are one per log line, so stepping walks the statechart (Phase 5 finding: per-step frames hid the move state).
*   **Consequences**: + no new dependency, nothing fetched from the internet. − the layout is ours to maintain (columns by distance from the start, gaps sized to labels, back edges arced above - a visual check in Phase 2 drove both).

## ADR-0014: The run log is an event stream

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-15 · **Related**: UND-13
*   **Context**: replay (owner) needs everything the page shows to be in the log; tools reading step and final lines must keep working.
*   **Options**: (1) add `event` lines - `start` (sketch, plays, turn), `state` (from XState's inspection API), `ended` (why a failed run ended) - to stdout and the log; (2) a second file for events; (3) live-only events.
*   **Decision**: (1). Idle looks (end where they began, no move) are folded into `idle_looks` on the next listed change. Step and final lines keep exactly their fields; readers skip lines with `event`.
*   **Consequences**: + one self-contained log per run; stdout stays equal to the log. − the seat reads XState's microstep `_transitions` (an internal of the inspection API), pinned by a test listing the exact transitions.

## ADR-0013: Jev chooses argument values, it never writes them

*   **Status**: Accepted, confirmed by the owner after launch ("constrained automation") · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-10 AC4-5
*   **Context**: owner: a sketch may list fixed calls, and Jev fills the remaining arguments. Jev (TypeSafe) answers only choice, noul and score questions - it cannot produce free text.
*   **Options**: (1) Jev chooses each open argument from a finite list - the sketch's `values`, the schema (enum, boolean, narrow integer range), or the last non-error result's leaves; (2) generate free text with another model; (3) offer only tools with no required arguments.
*   **Decision**: (1), in a second request after the tool is picked, one Choice per argument; an off-list answer is re-asked once, then the run stops (ADR-0004). A tool whose required argument has no list is not offered, and the run says so once per tool. Candidates come from the last result that was **not an error** (Phase 2 finding: a refused call must not erase what the call before it offered).
*   **Consequences**: + every value sent was offered and is in the log; tools chain naturally (ids from one answer feed the next call). − free-text arguments need listed values; noisy results give long lists (capped at 20).

## ADR-0012: MCP target - SDK client, understudy's own stdio transport, the `mcpServers` shape

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-15 · **Related**: UND-10, UND-11
*   **Context**: owner: understudy plays any MCP server as its client (not an MCP server itself), on the off-the-shelf `@modelcontextprotocol/sdk`, local and remote, configured the way Claude Desktop/Code configure servers.
*   **Options**: (1) SDK `Client`; local servers over a small `ProgramTransport` on `program.mjs` (using the SDK's `ReadBuffer`/`serializeMessage`), remote over the SDK's `StreamableHTTPClientTransport`; (2) the SDK's `StdioClientTransport` for local servers; (3) a hand-written JSON-RPC client.
*   **Decision**: (1). The server is one `mcpServers` entry, inline (`server: {...}`) or by reference (`config: servers.json, server: <name>`); `${VAR}`/`${VAR:-default}` filled at run start only; remote auth is token headers only (no OAuth, no SSE). A look lists tools + the last result; a move is one tool call; tool errors (isError or JSON-RPC) are the server's answer. A remote server that answers the connection with an HTTP error is `refused`, named by URL and status, never by header.
*   **Consequences**: + a local server is started, watched (exit code, stderr tail) and stopped like every other program; check needs no secrets. − `ProgramTransport` leans on two SDK exports (checked in Phase 2); resources, prompts and notifications are not read.

## ADR-0011: One `sketch.yaml` per sketch; code only in `hooks.mjs`

*   **Status**: Accepted (replaces the adapter/part layout of sprints 1-2) · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-9
*   **Context**: owner: one YAML file per sketch with all configs and params, and it is the only format (no back-compat). Sprints 1-2 split a stand-in over `adapter.mjs`, `part/turn.yaml` and `part/questions.yaml`.
*   **Options**: (1) `sketch.yaml` (name, description, target, app, player, steps, questions, turn, and for MCP calls/values) + `hooks.mjs` only where the target has no generic app; (2) keep the three files and add a YAML adapter beside the JS one.
*   **Decision**: (1). `src/sketch.mjs` replaces `part.mjs`; `parseTurn` takes the parsed `turn:`; every error names `sketch.yaml` and the path in it (`turn.states...`, `questions.answer...`); `--steps` beats `steps:`; a directory with `adapter.mjs` or `part/` and no `sketch.yaml` is refused, saying what replaced them.
*   **Consequences**: + one file to read; pages and MCP servers need no code; logs go to `build/runs/<sketch name>/`. − hooks still need JavaScript for programs and APIs; the old layout must be converted by hand (docs/SKETCHES.md §1 maps it).

## ADR-0010: One stall rule in the run loop, for every target

*   **Status**: Accepted · **Deciders**: Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-6 AC9, UND-7 AC8
*   **Context**: Smith Gate 1: a run could wait forever once the app stopped offering moves - the step cap counts moves, so it never trips. Hookless pages make this the likely failure (a last screen with no controls).
*   **Options**: (1) one rule in `run.mjs`: 10 s with nothing offered after a move → `stalled`; (2) per-target timeouts.
*   **Decision**: (1), sharing the idle check with the first-move rule; the message says to add a `showing` guard.
*   **Consequences**: + no run hangs; the commonest authoring slip explains itself. − an app that legitimately takes over 10 s between moves needs a larger limit (not configurable yet).

## ADR-0009: The part declares where it ends (`showing`), not the generic adapter

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-7
*   **Context**: the generic page app cannot know a page's end; the owner wanted web adapters to be optional.
*   **Options**: (1) a library guard `showing { text }` over the view `look` returns; (2) a `done` field on the adapter; (3) a Jev question on every look.
*   **Decision**: (1). It works for every target and costs no Jev calls; literal text in `turn.yaml` is allowed.
*   **Consequences**: + web adapters are a name and a target. − `showing` matches substrings anywhere in the view and may over-match on large views.

## ADR-0008: HTTP target - GET-state view, request moves, error statuses are the app's answer

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-6
*   **Context**: the third target kind the owner asked for at the start; ADR-0001's interface was meant to fit it.
*   **Options**: (1) view = GET of a state path, move = adapter-defined request, 4xx/5xx returned and logged, play continues; (2) treat 4xx/5xx as a run failure.
*   **Decision**: (1), with start-on-a-free-port or attach-to-a-running-URL; only a lost connection or a dead server ends the run.
*   **Consequences**: + an API refusing a bad move is visible in the log, which is what a test wants. − no auth headers or cookies yet.

## ADR-0007: Pages are read through the accessibility snapshot; the page hook is removed

*   **Status**: Accepted (supersedes ADR-0002) · **Deciders**: owner, Morpheus · **Date**: 2026-10-15 · **Related**: UND-7
*   **Context**: owner: "ditch the special hook" - play pages that were not written for understudy, with no back-compat.
*   **Options**: (1) Playwright's `ariaSnapshot()` + `getByRole` actions; (2) raw DOM walk with CSS selectors; (3) keep the hook.
*   **Decision**: (1). Roles and visible names are what a person (and a screen reader) meets; hidden and disabled controls are handled by the browser. All hook code, fields and docs were deleted.
*   **Consequences**: + unmodified pages; web adapters optional (generic page app). − free-text fields deferred; duplicate control names use the first visible one.


## ADR-0006: `make test` never calls Jev or launches Chromium

*   **Status**: Accepted · **Deciders**: Morpheus, Tank · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, SDLC §5
*   **Context**: Jev calls cost money and need a key; Chromium is slow and machine-dependent. The gate must be cheap and repeatable.
*   **Options**: (1) unit tests with a judge double and fake/real-process targets, live runs in a separate target; (2) live calls in `make test` behind an env flag.
*   **Decision**: (1). `runPart` takes `makeJudge`/`makeTarget`; the page target takes `launch`. Live runs live in `make test-live`.
*   **Consequences**: + fast, offline gate (93 tests). − the real SDK and Chromium are exercised only at UAT; a live regression is caught later.

## ADR-0005: Exit codes 0 / 1 / 2 for every command

*   **Status**: Accepted · **Deciders**: Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-1..4
*   **Context**: Smith Gate 1 asked for consistent exit codes so scripts and people can tell failures apart.
*   **Decision**: 0 done; 1 the run started and could not finish (`RunError`, with an `outcome`); 2 refused before anything started (`UsageError`). Every failure is one `understudy: <message>` line, no stack trace.
*   **Consequences**: + one rule everywhere. − an internal bug also exits 1 (`unexpected error: ...`) — indistinguishable by code from a failed run.

## ADR-0004: An off-list answer is re-asked once, then the run stops

*   **Status**: Accepted · **Deciders**: Morpheus, Cypher · **Date**: 2026-10-15 · **Related**: UND-1 AC3
*   **Context**: recard silently played its fallback move when Jev chose something not offered. For a testing tool that hides a broken question or option list.
*   **Options**: (1) fallback and continue (recard); (2) re-ask once, then stop with exit 1; (3) stop at once.
*   **Decision**: (2). The step records `offList` and the raw answer; nothing off-list is ever sent to the app.
*   **Consequences**: + broken parts surface. − one extra Jev call per miss; recard's own tests that relied on silent fallback had to change (they now model Jev picking only offered options).

## ADR-0003: Generic `look` actor and `phase` guard

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, UND-5
*   **Context**: every recard game wrote its own `<game>_look` actor and `<game>_phase` guard.
*   **Decision**: one `look` (calls `adapter.app.phase(view)`) and one `phase` guard (`is:`). Also renamed: `TABLE`→`OBSERVE`, `table_changed`→`changed`, `quiet_table`→`quiet`, `ask_table`→`ask`, `services.peer/game`→`target/app`, option `card`→`value`.
*   **Consequences**: + both example parts are the same shape; adapters stay small (51 and 24 lines). − recard's turn files must be renamed when recard migrates (no back-compat shims, per recard's rule).

## ADR-0002: The web target drives a page hook, not the DOM

*   **Status**: Superseded by ADR-0007 (sprint 2) · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-2
*   **Context**: a web adapter needs a view and moves. recard used `window.__recardHarness`.
*   **Options**: (1) a hook the page exposes (`window[hook]`, configurable); (2) generic DOM reading (buttons, text).
*   **Decision**: (1), default `__understudy`. The hook should only read the page and press what is on it.
*   **Consequences**: + exact views, tiny adapters. − the app must cooperate; a DOM mode for unmodified pages is backlog.

## ADR-0001: Target interface `view / act / talk / say / describe / exited / close`

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, extraction map
*   **Context**: the moved core already called recard's `peer` (`view/act/talk/say`); targets must be transport-neutral (web + CLI now, HTTP next).
*   **Options**: (1) keep the peer shape, add `describe/exited/close`; (2) an event-stream interface (push observations).
*   **Decision**: (1). The process target makes a terminal-like view (lines, echoed input, `seq`, `sent`, `exited`).
*   **Consequences**: + the core changed by renaming only. − a process target must buffer output and expose `seq`; adapters must guard against answering a question twice (`questions > sent`).
