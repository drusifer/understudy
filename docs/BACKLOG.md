# Backlog

Groomed by Cypher from the sprint 1 retro (2026-10-15). Owner, 2026-10-15: recard is no longer
a goal - no migration work. README done in the post-sprint docs groom. Not yet sized or ordered beyond
"Next" vs "Later".

## Sprint 2
Done - see `CHANGELOG.md` (HTTP target; hookless pages with the generic page app).

## Sprint 3
- **MCP server** — generic tools (start / look / act / stop) over all three targets. Starting point:
  `seed/recard/tools/mcp/harnessServer.mjs`. (`seed/` is kept untouched until then.)

## Later
- Scenario file / multi-actor runs (only if useful for understudy itself).
- A second Ctrl-C should say "stopped at once" instead of whatever error closing causes. (Neo)
- `unexpected error:` should say how to get the stack (e.g. `UNDERSTUDY_DEBUG=1`). (Neo)
- `make test-live` should check each run's final `outcome`, not only the exit code. (Trin)
- DEF-04: the no-key message repeats "understudy" after the `understudy:` prefix. (Smith)
- `--quiet` to drop the per-step stderr lines. (Smith)
