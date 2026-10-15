# Backlog

Groomed by Cypher from the sprint 1 retro (2026-10-15). Not yet sized or ordered beyond
"Next" vs "Later".

## Next
- **HTTP target** — `src/targets/http.mjs`: view = GET, act = request; an example under `examples/http/`. (Morpheus; contract already allows it, ADR-0001.)
- **README** — what understudy is, `make install` + `make run ARGS="run examples/cli"`, link `docs/ADAPTERS.md`. (Oracle)
- **Recard migration sprint** — recard depends on `github:drusifer/understudy#<tag>`, renames its turn files (ADR-0003), deletes its moved copies. (EXTRACTION_MAP §5)

## Later
- DOM-reading page mode for apps that cannot expose a hook (ADR-0002).
- Generic MCP server (EXTRACTION_MAP §2); scenario file / multi-actor runs.
- A second Ctrl-C should say "stopped at once" instead of whatever error closing causes. (Neo)
- `unexpected error:` should say how to get the stack (e.g. `UNDERSTUDY_DEBUG=1`). (Neo)
- `make test-live` should check each run's final `outcome`, not only the exit code. (Trin)
- DEF-04: the no-key message repeats "understudy" after the `understudy:` prefix. (Smith)
- `--quiet` to drop the per-step stderr lines. (Smith)
