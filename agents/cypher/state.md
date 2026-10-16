# Cypher State

## Context
- understudy plays apps with Jev via targets: `process` (CLI), `page` (unmodified web page, read via
  accessibility snapshot, generic page app), `http` (JSON API). Sprints 1-2 done, merged and pushed
  to main (b020fc5). Docs: README, docs/USER_GUIDE.md, docs/WALKTHROUGH.md, docs/ADAPTERS.md,
  docs/DECISIONS.md (ADR-0001..0010), docs/SDLC.md, docs/BACKLOG.md.
- Owner rules (also in memory): no back-compat (replace old shapes outright); recard is not a goal;
  version bumps only when the owner asks; ask the owner ONE question at a time; always use
  `bobp make` and `bobp chat`; publish only via `bobp make push MSG=...` when the owner asks.
- Sprint 3 direction (owner, 2026-10-15) - full text in docs/BACKLOG.md "Sprint 3":
  - An MCP **target** (`kind: 'mcp'`): understudy is an MCP *client* playing any MCP server, so
    "sketches" can drive anything reachable over MCP. NOT an MCP server for understudy.
  - Off-the-shelf client: `@modelcontextprotocol/sdk` (latest 1.32.1; has stdio, streamableHttp,
    sse client transports). Both local (stdio) and remote (HTTP) servers.
  - Config = de facto `mcpServers` shape (Claude Desktop/Code `.mcp.json`): local
    command/args/env; remote Claude Code `type: http` + url/headers. Two ways: file reference
    (`config: .mcp.json, server: via`) or same entry inline. Secrets as `${VAR}` from env.
  - Owner asked for ONE YAML file per sketch with all configs and params (`sketch.yaml`: name,
    target, player, steps, turn, questions; `app: hooks.mjs` only where code is needed).

## Current Task
**Status:** Shaping done - all owner questions answered; waiting for the owner's `/sprint 3 go`.

### Progress
- [x] MCP target vs server decided (target)
- [x] Off-the-shelf SDK client agreed
- [x] Local + remote both supported
- [x] mcpServers shape, file reference or inline
- [x] One-YAML-per-sketch proposed (docs/BACKLOG.md)
- [x] sketch.yaml is the ONLY format - convert cli/web/http examples, drop part + adapter.mjs (owner)
- [x] Tool args: sketch may list fixed calls; otherwise Jev fills args from the input schema (owner)
- [x] Remote auth: token headers via `${VAR}` only; OAuth to Later (owner)

## Next Steps
1. Run `/init` (resume). Read the end of agents/CHAT.md and docs/BACKLOG.md "Sprint 3" (all
   decisions recorded there).
2. (done) Owner answered: sketch.yaml only format; sketch calls + Jev fills args; token headers only.
3. (done) Answers in docs/BACKLOG.md and CHAT.md.
4. When the owner says go: `/sprint 3 go` - cut `sprint-3` from main, Cypher writes
   docs/sprints/USER_STORIES_SPRINT3.md (MCP target, sketch.yaml format, docs) -> Smith Gate 1.
   Morpheus flags `@modelcontextprotocol/sdk` (+ zod if required) as an ordinary dependency (no
   Tank Phase 0) unless sketch.yaml changes make targets.
5. Uncommitted at checkpoint: docs/BACKLOG.md (sprint 3 decisions) and agents/CHAT*.md - commit
   with the sprint 3 planning commit, or `bobp make push MSG=...` if the owner asks first.
