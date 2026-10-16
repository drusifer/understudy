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
**Status:** Sprint 3 launched (2026-10-15) on branch `sprint-3` (last commit: sprint 3 launch).
Merge to main / push / version await the owner.

## Next Steps
1. When the owner says so: merge `sprint-3` into main and `bobp make push MSG=...` (Tank).
2. (answered) Owner confirmed Jev chooses, never writes - constrained automation by design.
3. Sprint 4 candidates: docs/BACKLOG.md "Next" (`showing` scoped to MCP results, "yet" wording).
