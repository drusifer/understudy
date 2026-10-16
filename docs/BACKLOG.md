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
