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

## Sprint 5 (owner, 2026-10-16) - preferences as hard rules
- Owner: "I prefer horror films, and I want to go in the evenings but only if row E, F, or D is
  available (in that order), seats together but not too far from the center."
- **All hard rules** (owner decided): every preference becomes a rule in `sketch.yaml` (filters
  and orderings on the values Jev may choose) - not left to Jev's judgment. Needs a rule
  language in the sketch format, and a richer box office (genres, showtimes, a seat map).
- **Ties go to Jev** (owner decided): rules filter (an ordering keeps only the best available);
  Jev chooses among what is left, as now. A rule is never broken.
- **Enrichment from more MCP servers** (owner, 2026-10-16): a sketch may play several MCP
  servers at once - e.g. the box office plus a ratings service - so rules can use facts another
  server answers (a film's Rotten Tomatoes score). Owner asked for the tomato score: Rotten
  Tomatoes has no open public API; OMDb (omdbapi.com, free key, daily limit) returns it in
  `Ratings` for most titles (to verify when web search is back).
- **Fake ratings only** (owner decided): an in-repo ratings MCP server with made-up scores for the
  box office's made-up films - no key, no network, repeatable.
- Open: how rules name data that is not an
  argument (a film's genre, a showing's time, a seat's distance from the centre); what happens
  when nothing passes (walk away).

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
