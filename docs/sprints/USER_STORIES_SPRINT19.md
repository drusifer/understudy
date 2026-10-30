# Sprint 19 User Stories: The coffee proof of concept

*   **Total Points**: 28 (Tier 1)
*   **Branch**: `sprint-19` (cut from `main` at the Sprint 18 merge, 357c85b)
*   **Source**: owner, 2026-10-29, recorded in `docs/sprints/EPIC_PYTHON_PORT.md` (slice A) and `docs/sprints/DESIGN_SKETCH_MODEL.md`.
*   **Builds on**: the Python ETL controller (Sprint 17, ADR-0038) for the state machine runner, and `src/etl/jev.py` for Jev. The old Node player is untouched.
*   **Status**: Revised after Smith's Gate 1 rejection (2026-10-29): goal updated, UND-62 guard made testable on a fixture machine, UND-65 `expose` moved out of scope, UND-64 rounding stated, `--jev-answers` added to UND-60, share check added to UND-61 — awaiting re-review

## Goal

When this sprint is done, a shop owner can write one YAML file that says how they decide what to order, give it last week's total sales and the Farmers' Almanac's descriptions of last week and next week as plain files, and get back the ingredients to order for next week. Their own rules decide; counts and conversions are plain SQL; and Jev is used once, to read the two Almanac descriptions and say how much warmer or colder next week will be. This is the first working piece of the new sketch model, and it decides whether the rest of the Python port (the other examples, the dashboard) is built on the right shape.

## Assumptions made for the owner

1. **Fixtures are invented** (owner, 2026-10-29), under `tests/fixtures/coffee/`: about 1,600 drinks last week, five segments with shares summing to 1, two one-line Almanac descriptions (last week's and next week's). Real figures can replace them later.
2. **Files only.** Every source and sink is a file (owner, 2026-10-29); MCP and HTTP kinds are not built.
3. **Command line only.** No dashboard (owner, 2026-10-29).
4. **The weather is a decider, not a shift** (owner, 2026-10-29): each of the five Almanac levels carries hot/iced weights (much colder 0.90/0.10 … much warmer 0.30/0.70), the subsketch returns their probability-weighted mix on `temp`, and the parent blends it by weight; night workers get weight 0. Weights are numbers or `if` / `then` / `else`, never expressions.
5. **The syntax is settled** with the owner (`DESIGN_SKETCH_MODEL.md`): `blend:` for a stage's deciders, explicit YAML conditions, `returns: { decider: [...] }` for a subsketch, and a Jev question as a `kind: jev` source with `instructions`, `criteria` and `state`. Morpheus writes it down in the architecture; a change to how the owner writes a sketch returns to the owner before it is built.
6. **One live Jev judgement** at sprint close, with the owner's go-ahead; everything else uses `--replay` or an injected Jev double. Capture and replay (owner, 2026-10-29) is the testing mechanism for every non-file source.
7. **Stale replay** (the sketch or rubric changed since the capture) is flagged in the output and carries on; it does not fail the run (owner, 2026-10-29: "fine for now").

---

**Order and dependencies:** UND-60 first. UND-61 needs UND-60. UND-62 and UND-63 each need UND-61. UND-64 needs UND-63. UND-65 needs UND-61 and UND-62. UND-66 needs UND-64 and UND-65. UND-67 last.

## STORY-UND-60: Run a sketch from the command line
**Points:** 3

**As the** shop owner, **I want** to run `understudy sketch run coffee_week.yaml`, **so that** I can get next week's order without touching code. (`sketch` is a temporary word, because the old Node `understudy run` still exists until slice D deletes it; then the command becomes `understudy run`. The owner wants one kind of sketch and no duplicates when the epic ends: see the epic's purge list.)

### Acceptance Criteria
1. `understudy sketch run <sketch.yaml>` loads the sketch, prints one line per stage as it starts (`stage weather`, `stage split_trade`, …) and ends with a line naming the output file.
2. Exit code 0 on success, 1 when a stage fails, 2 when the sketch or an input file is wrong; the last line of an error says what to fix.
3. `--source <name>.path=<file>` replaces one source's file for this run only; the sketch file is not changed.
4. The command makes no network call except to Jev, and only when a stage reads a `kind: jev` source.
5. Every non-file source (here the Jev source) captures a complete, successful live read into a git-ignored local cache with the run id, source name, kind, request hash and time; the last 5 runs are kept.
6. `--replay [run-id|dir]` makes every non-file source read its capture and never go live: no key, no network, and the run repeats exactly. It uses the latest live run that captured every non-file source (or the named run, or the committed fixtures in `dir`); if no run covers them all it stops naming the missing source and saying to do a live run first.
7. Without `--replay` the run is live, and a missing `TYPESAFE_API_KEY` is exit 2 before any stage starts. `summary.json` records `mode: live` or `mode: replay`, and `stale: true` when the capture's request hash no longer matches the sketch.

## STORY-UND-61: A wrong sketch is refused before anything runs
**Points:** 5

**As the** shop owner, **I want** the sketch checked as a whole before it runs, **so that** a typo costs me seconds, not a half-finished run.

### Acceptance Criteria
1. The sketch is checked for: sources and sinks (a bare path, `kind: file` or `kind: jev`), declared `outcomes`, `data` (segment shares must add up to 1, within 0.001), and a `machine` whose stages and transitions all exist and end in a final state.
2. Every mistake names the file, the path inside it (`machine.states.match_orders.blend[0].decide.then.drink[1]`), the bad value and the nearest good one.
3. A decider that returns an option not in `outcomes` is refused at check time when it is written in the sketch, and at run time when it comes from a source, naming the stage.
4. A required source file that does not exist stops the run before any stage starts, and no output file is created.
5. A slice such as `70:100` is accepted in a condition (`in: [70:100]`, start included, stop excluded) and in a score; the sketch is read as YAML 1.2, so `70:30` stays text and is never turned into a number.

## STORY-UND-62: Run the owner's state machine
**Points:** 3

**As the** shop owner, **I want** my stages to run in the order and under the conditions I wrote, **so that** the quiet-week path or any other branch I add is followed.

### Acceptance Criteria
1. The machine is the sketch's own python-statemachine YAML; the Python loop runs the step the current state names and feeds the result back as an event.
2. A transition guarded by an explicit YAML condition over a stage's result (for example `if: { drinks: { lt: 500 } }`) is taken only when the condition holds; otherwise the next unguarded transition is. The coffee sketch is a straight line, so this is tested on a small fixture machine with a branch (`tests/fixtures/machine_branch.yaml`).
3. A stage that fails ends the run with exit code 1, names the stage, and publishes no output file; earlier stages' files stay in the run folder for inspection.
4. The run folder records each stage as complete or failed, so a failed run says where it stopped.

## STORY-UND-63: Decide per segment with weights and hard rules
**Points:** 5

**As the** shop owner, **I want** to write what each kind of customer usually orders, with shares, and some rules that are never broken, **so that** the forecast follows how I actually think about my trade.

### Acceptance Criteria
1. A `decide` tree with `if` / `then` / `else` over explicit YAML conditions (`segment: { eq: students }`) on a segment's fields returns, for each segment, weighted drink rows whose weights sum to 1 (a leaf listing 0.5, 0.2 and 0.3 is used as written).
2. A `forbid` rule drops matching rows (teens: no caffeine) and the remaining weights are renormalised to sum to 1 again; the rule wins over every preference.
3. If a `forbid` leaves a segment with no rows, the run fails naming the rule and the segment; the sketch can opt in to `on_empty: fallback` or `skip` per stage.
4. An unknown dimension or option in a leaf is refused as in UND-61, with the nearest valid one.
5. A weight is a number or an `if` / `then` / `else` over the segment (`if: { segment: { eq: night_workers } }`, `then: 0`, `else: 0.3`) and is evaluated per segment; no text is parsed as an expression, and the operators are `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, `not_in`, `has` with `and`, `or`, `not` to combine (several fields in one condition mean `and`).

## STORY-UND-64: From weekly sales to ingredients
**Points:** 3

**As the** shop owner, **I want** last week's total sales split across my customer groups and turned into amounts to order, **so that** I know how many grams to buy.

### Acceptance Criteria
1. The total drinks are split across segments by their `share`; expected counts stay fractional and the segment totals add up to the total exactly (1,600.00 stays 1,600.00); nothing is rounded until the packs (AC3).
2. Each segment's drinks are spread over its weighted drink rows, and the recipes turn drink counts into ingredient amounts (a medium uses 18 g of beans).
3. Amounts are rounded up to whole packs from `data.packs` (1,000 g of beans); a missing pack size leaves the amount unrounded.
4. All of this is plain SQL on DuckDB; no Jev call and no network.

## STORY-UND-65: A weather subsketch reads the forecast against last week
**Points:** 5

**As the** shop owner, **I want** the weather handled as a small sketch of its own that tells me how much warmer or colder next week will be, **so that** I can reuse it and the parent sketch only sees the answer.

### Acceptance Criteria
1. `weather_change` is its own sketch file with two file sources (the pasted Almanac descriptions of last week and next week); the parent calls it and sees only its output, which it declares as `returns: { decider: [temp] }`.
2. Jev is asked one rubric question over both descriptions and answers with a probability for each of five levels (much colder, colder, same, warmer, much warmer); the rubric holds only what each level means, and the owner's weights per level are separate and never shown to Jev. With the Jev double fixed to "warmer" the output is hot 0.45 and iced 0.55, and with mixed probabilities it is their weighted average.
3. The parent blends the weather weights with each segment's own preference by the weight the sketch gives; a segment whose weight is 0 (night workers) is unchanged by warm weather.
4. A Jev failure fails the run (UND-62 AC3); a Jev answer that is not one of the five levels (possible only from a recorded-answers file) is refused with the file and row named, and the run fails.

## STORY-UND-66: One reproducible output file
**Points:** 2

**As the** shop owner, **I want** a single file of ingredients and a short summary, **so that** I can order from it and trust it.

### Acceptance Criteria
1. `ingredients.jsonl` has one row per ingredient (`ingredient`, `amount`, `unit`) in a fixed order, written only when every stage finished.
2. A `summary.json` holds counts only: total drinks, drinks per segment, the Jev requests made, the weather weights used.
3. With `--replay` and the same fixtures, two runs produce byte-identical files.
4. The output lands in the run folder under `build/runs/` by default, never in a tracked folder or `data/` (as in UND-54).

## STORY-UND-67: One live judgement
**Points:** 2

**As the** owner, **I want** the Almanac judgement checked against real Jev once, **so that** I know the rubric gives sensible answers.

### Acceptance Criteria
1. With the owner's go-ahead, one live run on the fixture descriptions (last week: "Mild and breezy, highs near 55."; next week: "Fair but cold, with rain clearing midweek and a hint of snow by the weekend.") returns probabilities with most of the weight on the colder levels.
2. The probabilities and the resulting hot/iced weights are recorded in the UAT plan; if they are not sensible, the rubric wording changes and the run repeats once.
3. The live run is the only live Jev call in the sprint; its capture is copied into `tests/fixtures/` as the committed replay fixture, so later tests replay the real answer.

---

## Out of Scope
- The dashboard and watch page (slice C); MCP and HTTP source kinds; fetching the Almanac automatically.
- Translating the other examples (cli, http, web, mcp, evening) to the new model (slice B).
- Deleting the Node code (slice D); the Node player keeps working unchanged.
- Per-customer history, customer-level forecasts, or real shop data.
- A scoring formula or the old `position ^ weight` rule; vetoes are explicit filters.
- Subsketch inputs and the parent's `expose` list (the weather subsketch has no inputs, and there is no dashboard to show them on).
- Other styles of Jev interaction (yes/no probability, score); only the `choice` question is built. They are added later behind the same `kind: jev` source (owner, 2026-10-29).

## Open Questions
1. None on syntax (settled 2026-10-29). Morpheus confirms the module layout and the JSON Schema for sketches in the architecture.
2. None on conditions: explicit field/operator/value, compared with a fixed value only, no field-to-field comparison and no `between` (owner, 2026-10-29).
