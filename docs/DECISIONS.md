# Decisions

Newest first. Each record follows `agents/templates/_template_DECISION.md`, kept short.
Sprint 1 records were made by Morpheus in `docs/sprints/ARCH_SPRINT1.md` §8, sprint 2
records in `docs/sprints/ARCH_SPRINT2.md` §8 and sprint 3 records in
`docs/sprints/ARCH_SPRINT3.md` §8, sprint 4 records in `docs/sprints/ARCH_SPRINT4.md` §8
(all approved at Smith Gate 2, 2026-10-15) sprint 5 records in `docs/sprints/ARCH_SPRINT5.md` §8
and sprint 6 records in `docs/sprints/ARCH_SPRINT6.md` §8 (approved at Smith Gate 2, 2026-10-16). Records before
ADR-0011 say "adapter" and "part"; since ADR-0011 those are `hooks.mjs` and `sketch.yaml`.

---

## ADR-0037: SQLMesh owns deterministic ETL; Understudy coordinates Jev decisions

*   **Status**: Accepted · **Deciders**: Morpheus, owner, Tank · **Date**: 2026-10-17 · **Related**: STORY-UND-46, STORY-UND-47, STORY-UND-48; [Sprint 16 architecture](sprints/ARCH_SPRINT16.md)
*   **Context**: Sprint 16 reproduces a local Monarch and Amex cleanup workflow over roughly 4,700 reconciled transactions. SQL joins and transformations are standard ETL; Understudy must stage data-dependent steps and apply Jev's bounded category choices without using its limited answer-row memory as a transaction store.
*   **Options**: (1) SQLMesh models in SQL with YAML project configuration and local DuckDB: mature relational transforms with a run-scoped external decision table, at the cost of an isolated Python toolchain and a JSONL hydration stage; (2) dbt with DuckDB: familiar SQL/YAML models, but it also requires Python and offers no advantage for the sequential Jev handoff in this small local run; (3) custom Node joins/maps: fewer runtime components, but Understudy would own and maintain bespoke relational operations for reconciliation, grouping, and output.
*   **Decision**: (1) is accepted. Understudy validates and snapshots the local CSV exports, converts each flat row to an internal JSONL record with normalized fields and source provenance, then SQLMesh loads the JSONL records into DuckDB and owns deterministic relational transforms. Understudy coordinates named hydration and decision stages, asks Jev to choose from the fixed category/subcategory taxonomy (including Misc), and stores accepted merchant mappings in a run-scoped relation for reuse. This does not add arbitrary or nested JSONL input. CSV pagination and fetch mechanics remain below ETL operations if future MCP sources are added. Google Sheets/MCP I/O is deferred. Tank and the owner approved the isolated Python/SQLMesh mechanism; the Phase 0 clean setup and sequential SQLMesh/Node/DuckDB handoff probe passed.
*   **Consequences**: + uses a mature SQL engine for joins and row transforms while keeping qualitative decisions bounded and auditable. − introduces Python alongside Node and a second toolchain; CSV-to-JSONL hydration and SQLMesh JSONL loading add a staged interchange step. Synthetic end-to-end and SQLMesh model tests verify reconciliation, taxonomy mapping, review output, and failure behavior; private production CSVs and live Jev were not used for acceptance.

## ADR-0036: Gauges read the run's own lines; flair is visibly decoration

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-17 · **Related**: UND-42
*   **Context**: owner: per-theme flair with gauges - "yes real metrics in the gauges".
*   **Options**: (1) gauges computed in the page from the stream it already gets (start, step and `decided` lines), plus the run's limits added to the start line; (2) a separate metrics endpoint; (3) decorative gauges.
*   **Decision**: (1). `metersAfter`/`gaugesOf` are pure and unit-tested; the start line gains `limits: { steps, first_move_ms, stall_ms }`. Each theme draws the same five readings its own way (needle, hovering bars that stay within a small band round the value, card). Bulbs, leather and screws carry no meaning.
*   **Consequences**: + no new endpoint; a page joining mid-run rebuilds the readings from the history. − the start line has one more field.

## ADR-0035: The statechart is a layered flow laid out by ELK on the server

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-17 · **Related**: UND-41, UND-30
*   **Context**: owner: the states-round-a-circle tube was hard to follow ("is there a more standard visualization?"); edges crossed the middle and labels piled up.
*   **Options**: (1) a layered (Sugiyama) flow from `elkjs`, computed on the server and sent with the sketch; (2) `@dagrejs/dagre`; (3) improve the hand-made circle layout.
*   **Decision**: (1), top to bottom (it comes out square, so it fits the round tube and a phone without shrinking), orthogonal arrows, edge labels placed by ELK, model order kept so the initial state leads. The page only draws boxes, arrows and text. Steampunk keeps its round tube with a thin power ring on the rim; the other themes draw on a rectangular screen; the shares that the orb showed are a bar under the screen.
*   **Consequences**: + the standard statechart picture; no overlaps; no layout code in the page. − a new dependency; the layout is async, so describing a sketch waits for it.

## ADR-0034: Every Jev request carries the run's inputs; `pick.with` is removed

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-17 · **Related**: UND-40, UND-24
*   **Context**: owner: the questions' wording should follow the parameters ("see all"); fixed words like "two seats" contradicted the tickets input.
*   **Options**: (1) the run's inputs in every request's state, named in prose as `` `inputs.<name>` ``; (2) per-question `with:` lists, as `pick` had; (3) substituting values into the prose text before asking.
*   **Decision**: (1). `services.inputs` reaches the library's requests and the MCP app's score request; `pick.with` is removed outright; `check` refuses an undeclared `inputs.<name>`. (3) would put literal values in the prose, which the no-literals rule forbids - Jev reads the path from the state instead.
*   **Consequences**: + one rule for every question; wording cannot drift from the controls. − every request is a little larger; a sketch that used `with:` must drop it.

## ADR-0033: A run takes the caller's pause gate; the dashboard steps through it

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-17 · **Related**: UND-39, ADR-0016
*   **Context**: owner: step a run one move at a time from the dashboard, as `--watch` already can.
*   **Options**: (1) `runSketch({ gate })` - the caller makes a `createGate` and holds it; (2) the dashboard starts each run with `watch` and drives the watch server; (3) a second pause mechanism in the runner.
*   **Decision**: (1). The run loop already asks `gate.beforeMove()`; the dashboard's runner makes one gate per run, sends its changes to the pages as `{ event: 'dashboard', paused, waiting }`, and exposes `pause`/`step`/`resume`. Without a gate a run is unchanged.
*   **Consequences**: + one pause mechanism for both pages; paused time stays out of the idle limits. − a run takes either the watch page's gate or the caller's, not both.

## ADR-0032: Light and dark are a `data-mode` attribute; each theme's colours are variables

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-38
*   **Context**: owner: every theme in light and dark; the mode follows the device unless chosen (LIGHT / DARK / AUTO, remembered).
*   **Options**: (1) `data-mode` beside `data-theme`, each theme's other mode an override block, colours held in custom properties; (2) six separate theme stylesheets; (3) only `prefers-color-scheme` media queries.
*   **Decision**: (1). `modeOf(choice, isDeviceDark)` with a `matchMedia` listener sets `data-mode`; professional and starship were rewritten so their other mode only redefines variables; steampunk light is one override file, because steampunk's wood and brass live in `page.css`. Media queries alone (3) could not honour a fixed choice.
*   **Consequences**: + a mode switch is instant and follows the device live; a new theme declares its variables twice. − steampunk light is an override list that must follow `page.css` when panels change.

## ADR-0031: A hand-written JSON Schema for editors; check stays the full check

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-37
*   **Context**: owner asked how the YAML is documented; the reference is complete but editors gave no help while typing.
*   **Options**: (1) a hand-written draft-07 schema for the YAML language server, kept in step with `check` by tests; (2) generate the schema from `check`'s code; (3) make `check` run the schema.
*   **Decision**: (1). `ajv` (dev only) validates the examples and common mistakes; a test compares the schema's keys, target fields, input kinds and question types with the lists `check` exports. Examples carry a `# yaml-language-server: $schema=` line.
*   **Consequences**: + completion, hover text and underlines in any YAML-language-server editor, no runtime dependency; `check`'s precise messages unchanged. − the schema is a second description of the format, held to `check` only where the comparison test reaches (deeper rules - names, states, prose - are `check`'s alone).

## ADR-0030: A weight input is a share of the full weighting (3)

*   **Status**: Accepted · **Deciders**: owner · **Date**: 2026-10-16 · **Related**: UND-24, ADR-0017
*   **Context**: the evening's weight inputs moved from [0, 3] to [0, 10] so the faders read 1-10; used straight as exponents, 10 punished anything short of the best far harder (row F 0.67^10 = 0.02 against 0.67^3 = 0.30).
*   **Options**: (1) the input's share of its range times a full weight of 3; (2) keep the value as the exponent; (3) a per-input `max` field.
*   **Decision**: (1) - owner: "the slider is the percentage of the weighting applied (so 5 is = 1.5)". `inputs.weightsOf` turns the run's values into weights; `score` takes them as `weights`. A written number is still the exponent itself.
*   **Consequences**: + any range reads naturally and scores the same; the dashboard's sizes and the engine agree. − a person cannot weigh a factor above 3 from an input; a sketch wanting more writes the number.

## ADR-0029: Dashboard themes are a `data-theme` attribute and one stylesheet per theme

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-36
*   **Context**: owner: a professional theme and a Star Trek TNG one, beside the steampunk console. The tube's colours were hard-coded in the page script.
*   **Options**: (1) `<html data-theme>` with `page.css` as the default and a scoped stylesheet per theme, all loaded; script colours read from CSS custom properties; (2) swap one stylesheet link at run time; (3) a theme object in JavaScript styling every element.
*   **Decision**: (1). Theme rules sit under `:root[data-theme="..."]` so they beat the default without `!important`; the choice is `?theme=`, else localStorage, else steampunk.
*   **Consequences**: + an instant switch, mid-run; a new theme is one CSS file and one button. − every new piece of the console must be styled three times; the theme files are long override lists.

## ADR-0028: The bay behind the printer writes the whole sketch file

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-35
*   **Context**: owner: take the printer off to edit the sketch's YAML, saved as you type, and watch the tube change. The access panels' allow-list (ADR-0024) only lets listed values change.
*   **Options**: (1) a separate whole-file `write` beside the allow-listed `edit`, checked the same way on a copy; (2) widen the allow-list to every path; (3) a code-editor library with live parse and save.
*   **Decision**: (1). Same refusal check and factory copy as `edit`; refused while a run plays; the page sends writes one at a time after 500 ms of quiet, into a plain `<textarea>`.
*   **Consequences**: + any part of the sketch is editable, with the same safety (nothing failing `check` is written; POWER restores). − a whole-file write rewrites comments as typed, and no highlighting or completion; the drawers stay the precise way to change one value.

## ADR-0027: Count inputs, and inputs referenced as `{ input: <name> }`

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-34
*   **Context**: owner: replace the "seats together" toggle with a number-of-tickets selector (a brass stepper); the number must drive both the seats held and the together rule.
*   **Options**: (1) a `count` input kind and `{ input: name }` wherever a value or a gate bound is written; (2) a tickets-specific setting; (3) Jev choosing the count.
*   **Decision**: (1), in `values:` lists and gate `at_least`/`at_most` only. `check` validates the name and, for bounds, that it is a count or weight. On the dashboard a count is a stepper; weights stay analog faders.
*   **Consequences**: + one input feeds several places; other sketches get the stepper for free. − references are not allowed elsewhere yet (e.g. score ranges).

## ADR-0026: Switch inputs turn gates on and off (`when:`)

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-28
*   **Context**: owner: toggles on the console; a switch should turn a rule on or off.
*   **Options**: (1) a `switch` input and a `when: <switch>` word on a gate test; (2) switches that pick between whole gate sets; (3) a rule language with conditions.
*   **Decision**: (1). A test whose switch is off passes and needs no fact. `check` refuses `when:` naming anything but a switch. `--input name=on|off|true|false`.
*   **Consequences**: + no new language, one word. − a switch can only turn individual tests off, not swap rules.

## ADR-0025: Factory defaults are a copy kept at the first edit; POWER off-on restores

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-32
*   **Context**: owner: edits are saved to the sketch, with a reset to defaults - "turn it off and then back on".
*   **Options**: (1) copy `sketch.yaml` to `<folder>/.factory/<name>.yaml` before its first edit, restore all on POWER on; (2) git checkout; (3) keep edits only in memory.
*   **Decision**: (1). The copy is git-ignored and removed once restored.
*   **Consequences**: + works without git, one gesture undoes all. − a sketch edited by hand while the console has a copy is overwritten by the reset.

## ADR-0024: Panel edits replace only the edited value's text, checked on a copy first

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-32
*   **Context**: saving must keep a hand-written `sketch.yaml` readable, and never write a sketch that fails its checks.
*   **Options**: (1) find the value through `yaml.parseDocument` source ranges and replace just that text, then `loadSketch` a temp copy of the sketch directory; (2) edit the YAML Document and re-serialise; (3) write and roll back on failure.
*   **Decision**: (1). (2) was tried in Phase 6 and reflowed long lines and padded every flow list. Only allow-listed paths (inputs' defaults and choices, factor range/order/ask, a question's `looks_at`) can change.
*   **Consequences**: + byte-for-byte the rest of the file; nothing invalid is written. − a key the file does not have yet falls back to (2).

## ADR-0023: The dashboard is its own server beside the watch page; runs go through runSketch

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-27, UND-29
*   **Context**: owner: a steampunk console over a folder of sketches - set inputs, press Play, watch.
*   **Options**: (1) a second local server built like the watch page (token path, local files, SSE) with a small JSON API, running sketches in-process through `runSketch` and reading their stdout lines; (2) extend the per-run watch server; (3) spawn `understudy run` processes.
*   **Decision**: (1). `listenOn`/`readBody` are shared with the watch server; the watch page's `turnGraph` is reused. A STOP pressed while a run's servers start is held and delivered on its start line.
*   **Amendment (owner, 2026-10-16)**: the dashboard is served at the root (`http://<host>:<port>/`), with no token in the URL - not needed on the owner's network. With `--host 0.0.0.0` anyone who reaches the port can play and edit sketches; the watch page keeps its token path.
*   **Consequences**: + the CLI and the console run sketches the same way. − one run at a time; two browsers share it.

## ADR-0022: Several servers in one MCP target

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-20
*   **Context**: owner: enrichment from more MCP servers (a ratings service beside the box office), each named the MCP way.
*   **Options**: (1) one target holding several clients; (2) one target per server with the run switching between them; (3) a proxy server merging tools.
*   **Decision**: (1). `servers:` (inline, or names in a `servers.json`); tools are `<server>/<tool>` only when there are several, so one-server sketches, ids and logs are unchanged. A server that will not start stops the others and is named.
*   **Consequences**: + a sketch plays any mix of local and remote servers. − with several, ids are longer; a failure anywhere ends the run.

## ADR-0021: Walking away is a guard plus a tagged final state

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-25
*   **Context**: owner: when nothing passes, the understudy leaves and the run succeeds.
*   **Options**: (1) guard `nothing_qualifies` + a final state tagged `walked-away`; (2) the run detects it and ends by itself; (3) treat it as `stalled`.
*   **Decision**: (1). The turn decides where leaving goes; outcome `walked-away`, exit 0, a `walked-away` line and a sentence. Smith Gate 2: an argument that never saw a value (no seat map read because every showing was gated out) does not block leaving; a held-back value always does.
*   **Consequences**: + "nothing tonight" is a testable result. − a sketch without the state stalls instead (with the same explanation).

## ADR-0020: Jev at the edges - a Score per row and the final Choice; never weights

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-23, UND-24
*   **Context**: owner: constraints for what can be measured, Jev for the qualitative (audience reaction) and the final pick coloured by mood. Jev chooses, never writes.
*   **Options**: (1) Score questions as factors + a final Choice with inputs; (2) Jev sets the weights from prose; (3) Jev ranks the whole list.
*   **Decision**: (1). A `type: score` question `looks_at` a row field; asked once per row per run, every waiting row in one request on the next look; its 0..1 answer is a weighted factor. The final Choice gets `pick.instructions` and the inputs in `pick.with`; a shortlist of one is taken without asking. (2) deferred - it would be writing numbers.
*   **Consequences**: + Jev's judgment is one more knob, reused, cheap. − a value waits a look for its Score.

## ADR-0019: Scoring lives in the app, not in the statechart

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-21, UND-22
*   **Context**: owner asked whether the rule logic belongs in xstate or new primitives.
*   **Options**: (1) the generic MCP app filters and ranks the values of one move; (2) per-factor xstate guards.
*   **Decision**: (1). Guards are booleans choosing transitions; ranking values within one move is a different job. The turn sees one outcome, `nothing_qualifies`. The engine (`src/engine.mjs`) is pure over JSON rows.
*   **Consequences**: + reusable beyond MCP (a later `understudy rank`). − the statechart diagram does not show the rules; the step's score table does.

## ADR-0018: Gates, then weighted curves multiplied

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-21, UND-22
*   **Context**: owner: what is never accepted vs what is liked more; "the option I want the most has the biggest bearing"; a zero should drop a value.
*   **Options**: (1) hard gates, then score = position^weight per factor, multiplied (weighted geometric mean); (2) a weighted sum; (3) everything as hard rules.
*   **Decision**: (1). Gates remove (with why) or hold back (missing fact); while anything is held back the argument offers nothing, unless a value already totals a perfect 1 (owner, 2026-10-16). `range`/`order`/`ask` place a field 0..1; weight 0 turns a factor off; a 0 anywhere removes the value; the shortlist is every total above 0, bounded by `at_most`/`total.at_least`.
*   **Consequences**: + a great tomato cannot hide an end seat. − authors must set range floors deliberately: the bottom of a range removes.

## ADR-0017: Values carry their answer row; facts join by a named key

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-21
*   **Context**: rules test facts about a value (a showing's genre lives a level up; a film's score on another server). Sprint 3 offered flat leaf values of the last answer only.
*   **Options**: (1) rows: objects with inherited scalars, values from rows that own the field, across all remembered answers, joined by `join`; (2) look facts up by value equality.
*   **Decision**: (1). Lists of plain values (reviews) count as facts. A decided value used in a call that answered is spent. At most 500 rows kept.
*   **Consequences**: + facts from any server meet; a call already answered with the same arguments is not repeated (owner: an LRU cache, `lru-cache`, 200 calls). − spent values never come back even if the app changes; one join key, exact match.

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
*   **Amendment (owner, 2026-10-16)**: `--host ADDR` binds the page to another address (e.g. `0.0.0.0`) to watch from another device; 127.0.0.1 stays the default, and the per-run token is then the only guard (documented).
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
