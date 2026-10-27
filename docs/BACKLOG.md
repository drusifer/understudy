# Backlog

Groomed by Cypher from the sprint 1-3 retros (2026-10-15). Owner, 2026-10-15: recard is no longer
a goal - no migration work. README done in the post-sprint docs groom. Not yet sized or ordered beyond
"Next" vs "Later".

## Sprint 16 (owner, 2026-10-17) - staged local ETL with Jev-guided categories - DONE (launched 2026-10-27)
- UND-46..48: Monarch and Amex CSVs reconciled with SQLMesh and DuckDB, merchants categorised by Jev
  from a fixed taxonomy, a review file and a summary. ADR-0037.

## Next (from the sprint 16 retro and the owner, 2026-10-27)
- Sprint 17 stories drafted in `docs/sprints/USER_STORIES_SPRINT17.md` (UND-49..54): the source servers
  that serve each export as JSONL, the sign-flipped match, transfers kept as two linked records,
  refunds linked to their merchant, categories with a Noul check and MCC names for new ones, and a
  JSONL result. Needs Smith Gate 1 and an architecture.
- Python for all of understudy (owner, 2026-10-27): its own epic. Statecharts on `python-statemachine`'s
  YAML, ETL stays SQL on DuckDB, Jev through `typesafe-sdk`. Risks: `elkjs` flow layout and `xstate` have no
  Python equivalent; check the SDK's per-answer probabilities and the YAML coverage of `turn:` first.
  See `agents/cypher/platform_decision_2026-10-27.md`.
- The owner's workbook comparison (4,666 of 4,672 IDs matched) needs a baseline or crosswalk before a
  category score means anything: its `Category` and `Category_Ontology` disagree on 2,522 rows. (Neo)
- A `judge-trace` make target is missing from this worktree's Makefile although the Trin skill expects it. (Trin)
- A real-shaped test fixture with sign-flipped pairs and transfers, so a matching rule is tested before real data. (Trin)
- Record ADRs for Python-for-all and no-XML; add an ETL section to `docs/USER_GUIDE.md`. (Oracle)
- Commit at each phase gate as the SDLC says, and run `git status` before a sprint starts. (Mouse)
- ETL results as JSONL (owner's JSONL-in/out principle), the run visible in the dashboard, and a way to pin Jev's
  category choices between runs. (Smith)

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

## Sprint 6 (owner, 2026-10-16) - the dashboard, with atmosphere - DONE (launched 2026-10-16)
Design approved on a clickable mockup - **`docs/design/DASHBOARD.md`** is the brief. Owner decisions:
- `understudy dashboard <folder>`: a folder of sketches to choose from; each sketch's inputs define
  its controls. Knobs are set **before** a run; Play starts it (not live tuning).
- A new **switch** input (on/off) turns a gate on or off with `when: <switch>`.
- Access panels edit factor parameters and the moods; edits are **saved to the sketch**; turning
  POWER off and on resets the sketch to its **factory defaults**.
- "11" is how a perfect 1.0 is shown. Square lit Play button; green glowing READY lamp.

## Sprint 9 (owner, 2026-10-16) - themes - DONE (launched 2026-10-16)
- UND-36: THEME switch - steampunk, professional, starship.

## Sprint 15 (owner, 2026-10-17) - flair and real gauges - DONE (launched 2026-10-17)
- UND-42: five gauges from the run's lines (start line now carries `limits`); steampunk leather,
  screws, ornate edge, valve bulbs, needle meters; starship power-bar readouts; professional cards.
- Next: steampunk's flow labels are small inside the round tube. (Smith)

## Sprint 14 (owner, 2026-10-17) - the statechart as a flow - DONE (launched 2026-10-17)
- UND-41: layered flow (elkjs); rectangular screens; decision power bar.

## Sprint 13 (owner, 2026-10-17) - questions that know the inputs - DONE (launched 2026-10-17)
- UND-40: every Jev request sees `inputs`; `pick.with` removed; the evening's questions use them.
- Next: the evening's horror taste is fixed in a gate; a `genre` choice input would let it follow too. (Cypher)

## Sprint 12 (owner, 2026-10-17) - one move at a time - DONE (launched 2026-10-17)
- UND-39: STEP and PAUSE/RESUME on the dashboard; the printer opens on a release latch.

## Sprint 11 (owner, 2026-10-16) - light and dark - DONE (launched 2026-10-16)
- UND-38: MODE switch (AUTO / LIGHT / DARK); six looks; LEDs follow their faders; phone layout of the bay.

## Next (from the sprint 11 retro)
- Steampunk light is an override list over `page.css`; moving steampunk's colours into variables would make it a variable block like the others. (Morpheus)
- A contrast check in the browser test (still by eye). (Trin)

## Sprint 10 (owner, 2026-10-16) - a schema for sketch.yaml - DONE (launched 2026-10-16)
- UND-37: `schema/sketch.schema.json`, editor line in every example, kept in step with check by tests.

## Next (from the sprint 10 retro)
- The bay's edit box could offer the schema's completions (it is a plain textarea today). (Smith)
- Try the schema in a real editor (VS Code YAML extension) and note any rough edges. (Trin)

## Next (from the sprint 9 retro)
- DONE in sprint 10: a JSON Schema for `sketch.yaml` (UND-37).
- Measure contrast in the browser test instead of by eye (professional AC3). (Trin)
- The tube's labels still overlap round "looking" in every theme - the sprint 6 item below. (Smith)
- Styling each new control three times is the cost of themes; keep new controls built from the shared custom properties. (Morpheus)

## Sprint 8 (owner, 2026-10-16) - behind the printer - DONE (launched 2026-10-16)
- UND-35: REMOVE the printer to edit the sketch's YAML with a cheat-sheet sticker; saved as typed; the tube redraws.

## Next (from the sprint 8 retro)
- `src/dashboard/page.mjs` is now ~640 lines: the split below is overdue. (Neo, Morpheus)
- Browser-test the bay's read-only-while-running and its reload on POWER and drawer saves (UND-35 AC4-5). (Trin)
- The sticker takes ~40% of the bay; let it fold away to give the YAML box room. (Smith)

## Next (from the sprint 6 retro)
- Tube labels still crowd when a state has several guarded exits (evening's "looking"); try label
  leader lines or a label-collision pass. (Smith)
- DONE in sprint 7: the "seats together" toggle became a number-of-tickets stepper (owner).
- `not offering ... yet - already answered` should not say "yet". (Smith)
- `src/dashboard/page.mjs` is ~550 lines: split the tube drawing and the panels into modules. (Neo)

## Next (from the sprint 5 retro)
- DONE on sprint-5: **Wait for every fact, unless it scores a perfect 1** (owner decided, 2026-10-16; "11" is how the dashboard shows 1.0): a decided argument
  offers nothing while any value is held back - except when a value scores 100% on a factor
  turned to 11, which wins outright at once (see Sprint 6 "Knobs that go to 11"). (Morpheus)
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
