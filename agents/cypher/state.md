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
**Status:** Shaping sprint 4 (watch the understudy live) - owner answered all four questions
(browser page; live + replay; pick + confidence; pause and step live). Recorded in
docs/BACKLOG.md "Sprint 4". Waiting for the owner's go.

## Next Steps
1. On go: `/sprint 4` - cut `sprint-4` from main, archive task.md to docs/sprints/TASKS_SPRINT3.md,
   Cypher writes docs/sprints/USER_STORIES_SPRINT4.md from BACKLOG "Sprint 4" (assumptions there
   go into the stories' Assumptions section) -> Smith Gate 1.
