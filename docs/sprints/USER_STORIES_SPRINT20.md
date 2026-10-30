# Sprint 20 User Stories: the evening and the household ETL as sketches

*   **Total Points**: 26 (Tier 1; UND-73 added at architecture, 2026-10-30)
*   **Branch**: `sprint-20`
*   **Source**: Owner, 2026-10-30: plan slice B of `docs/sprints/EPIC_PYTHON_PORT.md`; keep only the evening example; "the budget one" (the household ETL) must become a sketch as part of B; the ETL reads its CSVs as file sources (option 1, so the MCP source servers go).
*   **Status**: Revised after Smith's Gate 1 rejection — awaiting re-review

## Goal

When this sprint is done, the owner's two real pipelines are sketches in the new model: the evening at the cinema (with a seating subsketch) and the household spending ETL. Both run with `understudy run`, both can be checked, captured and replayed, and the old examples, the old schema and the ETL's own MCP servers and controller are gone. This is the first proof that the sketch model carries real work and not only the coffee example.

**Order and dependencies.** UND-68 comes first (the two sketches need it). UND-73 (candidates from file rows) needs 68. UND-69 needs 68 and 73; UND-70 needs 68, 73 and 69. UND-71 needs 68 and is independent of 69, 70 and 73. UND-72 needs 70 and 71 and goes last. Each story leaves the product usable: after 68 the coffee example still runs; the old ETL command keeps working until UND-72.

## Assumptions made for the owner

1. The evening reads showtimes, ratings and seat maps from committed JSON/JSONL fixtures (file sources); nothing live. The Node box office and ratings servers are deleted. If wrong: the evening waits for an MCP source kind, which the epic rules out.
2. The evening's oracle is its own old rules (gates, scores, shortlist, mood pick, walk away) checked against a Jev double. The old Node player no longer exists to compare against.
3. The ETL's oracle is the current Python ETL: UND-71 first captures its `result.jsonl` and summary on the invented CSV fixtures as a committed expected file, and the sketch must match it; only then does UND-72 delete `understudy etl run`. If wrong: the sketch has nothing to prove "identical" against.
4. The net-spending question ($433k looks too large) is not fixed here. It moves with the pipeline unchanged and stays in the backlog, so the port is proved identical first.
5. The new model's gaps, listed in UND-68, are added in the smallest form that serves these two sketches, not as general features.

---

## STORY-UND-68: The sketch model gains what the two sketches need
**Points:** 3

**As the** owner,
**I want** the sketch model to say "walk away", take values from the command line or a calling sketch (Jinja2 templates), and repeat a sketch once per row (`each:`),
**so that** my evening and my budget can be written down without workarounds.

### Acceptance Criteria
1. A stage with `on_empty: walk_away` that has no options left ends the run with exit 0, writes no sink output and prints `walked away at <stage>`; the existing `fail`, `skip` and `fallback` values behave as before (coffee tests unchanged).
2. A sketch file is a Jinja2 template read as standard YAML 1.2: `{{ tickets | default(2) }}` takes `--with tickets=3` from the command line; plain YAML without template marks reads unchanged (every existing test still passes). A variable with no default and no value fails naming it: `needs a value for 'tickets': pass --with tickets=<value>`.
3. Any sketch can be called by another: the calling state's `with: { seats: {{ tickets }} }` passes values to it; the child sees only what its call passes; one sketch can be called many times with different values. A `--with` or `with` name that the receiving file does not use is refused with the nearest used name: `--with tikets: the file does not use it (did you mean 'tickets'?)`.
4. `each: <source>` on a state that calls a sketch runs that sketch once per row of the source, passing the row's values with `with:`; a list given to any other source, stage or sketch is one input, never looped over behind the scenes. The loop's result is one list with an entry per row. Each iteration's Jev answers are captured under that call, and a replay returns them without a live call; a replay whose rows changed since the capture says it is stale.
5. `docs/SKETCHES.md` describes each of the four additions with one example.

## STORY-UND-73: A decision can choose among candidates read from a file
**Points:** 5

**As the** owner,
**I want** a sketch to rank and shortlist options that only exist in a file (showings, seat blocks) and have Jev choose among them,
**so that** my evening can weigh real showings without my listing each one in the sketch.

### Acceptance Criteria
1. An outcome whose options come from a file's rows (`showings.jsonl`, key `title`) can be weighted by deciders and filtered by `forbid` like a declared one; a decider that names a title not in the file fails with `<title> is not a candidate (did you mean …?)`.
2. `shortlist: { at_most: 5 }` on a blend keeps the five highest-weight candidates; with three candidates it keeps three.
3. A Jev source can list as its options a stage's shortlist (`options: { from: <stage>, key: <field> }`); only those options are offered to Jev, so its answer can only be one of them. A stage that has not run is named: `its options come from stage 'rank', which has not run`.
4. Capture and replay cover that read like any other source.

## STORY-UND-69: Seating is a subsketch
**Points:** 3

**As the** owner,
**I want** seat selection to be its own sketch that the evening can call,
**so that** it can be reused and so that only seats it really found can be booked.

### Acceptance Criteria
1. On a seat map fixture with free seats `E3 E4 E5` and `E8 E9` in row E, `tickets=2` yields the blocks `E3-E4`, `E4-E5` and `E8-E9` as candidates; `tickets=3` yields only `E3-E5`.
2. The seating sketch takes the showing, tickets, row weight and centre weight, and returns one hold. With centre weight 10 it holds the block nearest the middle of the row; with centre 0 and the row order E, F, D it holds a row E block whatever its position.
3. A caller can use only the hold the subsketch returned: `check` rejects a parent that names a hold the subsketch does not declare, with the name in the message.
4. When no block is long enough, the subsketch finishes with outcome `none` and the parent receives it as such.
5. A seat map fixture that is missing or has no `seat` column fails `check` naming the file and the column; nothing is written.

## STORY-UND-70: The evening runs as a sketch
**Points:** 5

**As the** owner,
**I want** my cinema preferences to run as a sketch in the new model,
**so that** the understudy books two seats the way I would, or walks away when nothing suits me.

### Acceptance Criteria
1. `understudy check` passes on the evening sketch; `understudy run` with a Jev double and the committed fixtures books a showing and a hold that obey my rules: evening only, horror scoring 70 or more or anything above 90, seats together in row E, F or D, central.
2. Values shape the decision, each with a test: `--with evenings=off` admits a 15:00 showing that is otherwise dropped; `--with tickets=3` books a block of three; `--with centre=0` and `--with centre=1` (a weight, 0.0 to 1.0) book different named blocks on the same fixture; `--with mood=romantic` is shown to the Jev double in its request.
3. The final pick is made by Jev from a shortlist of at most five; a Jev double that answers with an option outside the list is refused and the run fails naming the option.
4. When no showing qualifies (fixture with only afternoon horror at 60) or seating returns `none`, the run exits 0, prints `walked away at <stage>` and writes no booking.
5. A missing or malformed fixture fails `check` naming the file and the field; no booking is written.
6. A captured run replays offline with the same booking.

## STORY-UND-71: The household ETL runs as a sketch
**Points:** 8

**As the** owner,
**I want** my spending pipeline to be one sketch over my Monarch and Amex files,
**so that** the same model and commands run both my cinema evenings and my budget.

### Acceptance Criteria
1. First, before any change, the current ETL's `result.jsonl` and summary on the invented CSV fixtures are committed as the expected files.
2. The sketch declares the Monarch and Amex CSVs as file sources and the result and summary as file sinks; stages run in order: validate, convert, pair, transfers, plan spending, refunds, categories, output. A failing stage ends the run with exit 1, names the stage, and publishes no result.
3. On the fixtures, the sketch's result equals the committed expected file as sorted JSONL records, and its summary numbers match exactly.
4. Merchants are categorised once each by Jev from the fixed taxonomy with MCC naming; the test path uses a Jev double and a committed replay.
5. A CSV missing the date, amount or merchant column fails with `<file>: missing a required <column> column (recognized: …)`, exit 1, nothing published.
6. A captured run replays offline with the same result.
7. A run on the owner's real files completes with 5,074 records, printing counts and paths only (no merchant names or amounts), and writes nothing private under `src/`.

## STORY-UND-72: The old shapes are purged
**Points:** 2

**As the** owner,
**I want** the old examples and the second pipeline format gone,
**so that** there is one kind of sketch and one way to run it.

### Acceptance Criteria
1. `examples/cli`, `http`, `web`, `mcp`, `mcp-remote`, the old `evening`, `seed/`, `schema/sketch.schema.json` (old) and the Node box office and ratings servers are deleted; the epic's purge list marks these rows done.
2. `understudy etl run` and the ETL's own controller, runner and MCP source servers are deleted; `understudy etl run` then reports an unknown command; the SQL and Jev code the sketch uses exists once.
3. `docs/SKETCHES.md`, `docs/USER_GUIDE.md` and `docs/DOMAIN.md` describe the evening and the ETL as sketches; no doc names a deleted command or file; ADR-0011, 0018 and 0030 are marked superseded if not already.
4. The full `bobp make` check, lint and test suite is green, not only the changed files.

---

## Out of Scope
- The net-spending bug and the 270 review merchants (backlog).
- MCP and HTTP source kinds (epic no-go; the MCP servers are deleted, not ported).
- Joint decider rows (a recipe on two options at once); nothing in these two sketches needs them.
- The dashboard and watch page (slice C); deleting the last Node (slice D).
- Fetching real showtimes or reviews.

## Open Questions
1. Does the ETL's SQLMesh model stay as a stage the sketch calls, or become plain SQL stages on DuckDB? Morpheus answers in the architecture; assumed: whichever deletes more code with the identical result.
2. Is "the same result" sorted-record equality? Assumed yes (UND-71 criterion 3); the owner can say byte-identical instead.
