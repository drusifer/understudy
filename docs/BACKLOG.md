# Backlog

Groomed by Cypher from the sprint 1-3 retros (2026-10-15). Owner, 2026-10-15: recard is no longer
a goal - no migration work. README done in the post-sprint docs groom. Not yet sized or ordered beyond
"Next" vs "Later".

## Sprint 2
Done - see `CHANGELOG.md` (HTTP target; hookless pages with the generic page app).

## Sprint 3
Done - see `CHANGELOG.md` (one `sketch.yaml` per sketch; MCP target, local and remote; Jev-chosen
tool arguments). Decisions: ADR-0011..0013. Owner confirmed (2026-10-15): Jev chooses argument
values, never writes them - understudy is constrained automation by design.

## Sprint 4
Done - see `CHANGELOG.md` (live watch page, pause/step, replay, the log as an event stream).
Decisions: ADR-0014..0016.

## Sprint 5 (owner, 2026-10-16) - a decision engine: gates, scores, Jev - DONE (launched 2026-10-16)
Owner: "I prefer horror films, and I want to go in the evenings but only if row E, F, or D is
available (in that order), seats together but not too far from the center." Shaped in chat on
2026-10-16; the general case is a **filter over JSON rows** - constraints and scores pick the
subset worth a closer look, and Jev makes the qualitative calls. Owner decisions:

- **Several MCP servers per sketch** (mcpServers entries, inline or `servers.json`). Facts about
  one film are joined across servers by its title.
- **Fake ratings server** in the repo: a made-up tomato score and made-up audience reviews per
  film; no key, no network. (Rotten Tomatoes has no open API; OMDb has the score - not used.)
- **Gates** are hard pass/fail tests on an answer row's fields, code-free YAML: `is`, `in`,
  `at_least`, `at_most` (numbers, and `HH:MM` times), and `any` (one of several groups passes).
  Example: horror scoring 70+, **or** any film above 90 - the "automatic yes" decides the film
  only; evening and seat rules still apply.
- **Scores** rank what passes the gates. Each factor maps one field to 0..1 - `range: [from, to]`
  (linear, either direction, clamped) or `order: [E, F, D]` - and its **weight shapes the
  curve**: score = position ^ weight (rows E/F/D at weight 1: 1, 0.67, 0.33; at weight 2: 1,
  0.44, 0.11). The option wanted most has the biggest bearing.
- **Factors multiply** into the total (a weighted geometric mean), so a higher weight counts for
  more, and a zero anywhere (the bottom of a range) drops the value.
- **Walk away**: if nothing passes the gates or every total is zero, the understudy leaves - an
  end state, exit 0, the log says what ruled out what.
- **Centreness scales with the theatre**: the box office answers each seat's `centre` from 0 (end
  of row) to 1 (middle), scaled by that screen's row width; closer is better (a scored factor).
- **Jev's qualitative part is a Score question in the YAML**: what it looks at (e.g. the film's
  reviews), the instructions and the levels ("bored" ... "loved it"); its 0..1 answer is a
  weighted factor like any other.
- **Shortlist, then Jev picks**: the top totals form a shortlist; Jev makes the final Choice among
  them, coloured by a **mood** (fun, serious, dramatic, romantic).
- **Preferences are inputs**: the sketch declares them - the mood (a choice) and each weight
  within a range, with defaults - and the run sets them from the command line in sprint 5.
- Out for now: Jev choosing weights (it would be writing numbers; maybe later as levels it
  chooses); scoring a showing by its best seats (picks are made one move at a time).
- Superseded: "all preferences are hard rules" and `order` keeping only the best available - an
  order is now a scored curve; only gates are hard.
- **Shortlist = everything that qualifies** (owner): every value with a total above zero, unless
  the sketch bounds it with the same words, e.g. `shortlist: { at_most: 5 }` (the top 5 totals)
  or `{ total: { at_least: 0.3 } }`.
- **Example defaults** (proposed by Cypher, owner OK'd proposing; tweak later): every weight an
  input in `[0, 3]`; row `order: [E, F, D]` weight 2; `centre` `range: [0.3, 1]` weight 3;
  `tomato` `range: [70, 100]` weight 1; Jev's audience Score weight 2; mood default `fun`;
  shortlist unbounded.
- Sprint 5 branches from main (51fa684); the first story draft (`USER_STORIES_SPRINT5.md`,
  hard rules only) is to be rewritten from this.

## Sprint 6 (owner, 2026-10-16) - the dashboard, with atmosphere
- A **steampunk operations dashboard** for understudy: knobs, toggles and chunky sliders to set a
  sketch's declared inputs (mood, weights within their ranges), and the statechart, scores and
  decisions shown in an embedded terminal-like panel. The owner wants understudy to have
  atmosphere. Builds on the sprint 4 watch page and the sprint 5 inputs.
- **Knobs that go to 11** (owner idea, queued 2026-10-16): a weight knob has a setting past its
  range, `11`: a value scoring 100% on that factor wins outright - no other factor matters (gates
  still apply). Needs a small engine rule alongside the knob.
- **Power through the graph** (owner idea, queued 2026-10-16): in the logic display, the edge for
  each factor carries more visible power as its weight rises - a flux-capacitor glow and flow,
  strongest at 11.

## Next (from the sprint 5 retro)
- **Owner question**: a decision can pick a showing while other films are still held back
  (waiting for their score). Should a decided argument offer nothing until nothing is held? (Morpheus)
- Extract the decision path (`decided`, scores, standing) from `src/apps/mcp.mjs` into its own module. (Neo)
- Watch page: group a step's removed values by reason ("together 1 < 2: 64 seats"). (Smith)
- `test-live`: a step budget per example, so a run that wanders fails. (Trin)
- A short "Deciding" cheat-sheet in USER_GUIDE. (Oracle)
- Debt: spent values never come back if the app changes (ADR-0017).

## Next (from the sprint 3 and 4 retros)
- Scope `showing` to results for generic MCP sketches (today it also searches tool descriptions). (Morpheus)
- "not offering ... yet" should not say "yet" for array/object arguments a result can never fill. (Smith)
- Watch page: shorten a stall message's raw view JSON; show what Jev read for a step on demand. (Smith)
- A Playwright UAT script for the watch page kept in the repo (and a make target - Tank's call). (Trin)

## Later
- Watch page: reconnect a live page that lost its stream mid-run (today: "connection lost", reload). (Morpheus)
- Split `src/watch/page.mjs` into model and DOM when it next grows. (Neo)
- OAuth for remote MCP servers (sprint 3 does token headers only). (Morpheus)
- MCP resources, prompts and notifications in the view; cache the tool list until `list_changed`. (Morpheus, Neo)
- A test that drops a remote MCP server mid-run (`connection-lost` is unit-tested only). (Trin)
- `check` could warn about `calls:`/`values:` naming a tool the server does not have (needs the server running). (Smith)
- Typing into text fields on pages (needs a source for the text). (Morpheus)
- Auth headers / cookies for the HTTP target. (Morpheus)
- Make the first-move and stall limits configurable (`--wait`). (Neo)
- `npm test` with `--test-timeout`, so a hanging test fails instead of freezing the suite. (Trin)
- `check` could warn when a generic-page part has no `showing` guard. (Smith)
- Scenario file / multi-actor runs (only if useful for understudy itself).
- A second Ctrl-C should say "stopped at once" instead of whatever error closing causes. (Neo)
- `unexpected error:` should say how to get the stack (e.g. `UNDERSTUDY_DEBUG=1`). (Neo)
- `make test-live` should check each run's final `outcome`, not only the exit code. (Trin)
- DEF-04: the no-key message repeats "understudy" after the `understudy:` prefix. (Smith)
- `--quiet` to drop the per-step stderr lines. (Smith)
