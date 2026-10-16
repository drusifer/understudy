# Cypher State

## Context
- understudy plays apps with Jev. Since sprint 3 a stand-in is a **sketch**: one `sketch.yaml`
  (+ `hooks.mjs` for process/http). Targets: `process`, `page`, `http`, `mcp` (local stdio or
  remote streamable HTTP with token headers; server in Claude's mcpServers shape, inline or by
  `config:` reference, absolute paths OK). Jev *chooses* MCP arguments (values/schema/last
  non-error result), never writes them (ADR-0013). Docs: README, docs/USER_GUIDE.md,
  docs/WALKTHROUGH.md, docs/SKETCHES.md, docs/DECISIONS.md (ADR-0001..0013), docs/SDLC.md.
- Owner rules (also in memory): no back-compat; recard is not a goal; version bumps only when
  the owner asks; ask ONE question at a time; always `bobp make` / `bobp chat`; publish only via
  `bobp make push MSG=...` when the owner asks.

## Current Task
**Status:** Shaping sprint 5 (preferences as hard rules + enrichment from more MCP servers) with
the owner. sprint-4 (+ --host, browser tests) is complete on branch sprint-4, NOT merged yet.
Decisions so far in docs/BACKLOG.md "Sprint 5": all hard rules; ties go to Jev; several MCP
servers per sketch for enrichment; fake in-repo ratings server.

## Next Steps
1. Ask the owner (one at a time): rule form - YAML conditions on the answer object a value came
   from (recommended; works across servers) vs JS in hooks.mjs (owner redirected to enrichment
   instead of answering); then what happens when nothing passes (walk away = new 'leave' move?).
2. Then: merge sprint-4 when the owner says, cut sprint-5, write stories (richer box office:
   genres, showtimes, seat map with from_centre; ratings server; multi-server sketch; rules).
