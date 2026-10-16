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

## Sprint 4 (owner, 2026-10-15) - watch the understudy live
- Owner: "a way to see what the understudy is doing - a UX that displays the state machine
  diagram and shows the state changes and Jev decisions in real time."
- **Browser page** (owner decided): `understudy run ... --watch` serves a local page on
  127.0.0.1 that draws the turn's statechart, highlights the current state, and streams each
  Jev decision (options, pick, confidence, chosen arguments, the app's answer).
- **Live + replay** (owner decided): the same page follows a run live (`run --watch`) and
  replays a finished one from its log (`understudy watch <log.jsonl>`); the log gains the state
  changes it needs for that.
- **Decision detail = pick + confidence** (owner decided): options offered, the pick, its
  confidence, chosen arguments, the app's answer - what the log has today. No probability bars.
- **Pause and step live** (owner decided): the page can pause a live run before its next move
  and release it one step at a time, then resume. Replay has play / pause / step through the log.
- Assumptions to confirm at story time: the diagram is drawn from the sketch's own `turn:` (no
  hand-made picture); the page and its drawing library are served by understudy itself (works
  offline, nothing fetched from the internet); 127.0.0.1 only, no login; while paused the
  first-move/stall timers do not run; Ctrl-C still stops a paused run.

## Next (from the sprint 3 retro)
- Scope `showing` to results for generic MCP sketches (today it also searches tool descriptions). (Morpheus)
- "not offering ... yet" should not say "yet" for array/object arguments a result can never fill. (Smith)

## Later
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
