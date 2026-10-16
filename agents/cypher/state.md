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
1. Shaping done (BACKLOG "Sprint 5": hard rules as YAML on answers, ties to Jev, ratings as its
   own MCP server with fake scores, walk away = success). Wait for the owner's go.
2. On go: merge sprint-4 into main first (owner's say), cut sprint-5, write
   docs/sprints/USER_STORIES_SPRINT5.md from BACKLOG (assumptions listed there) -> Smith Gate 1.
