# Cypher State

## Context
- understudy plays apps with Jev via sketches (`sketch.yaml`, + `hooks.mjs` for process/http).
  Targets: process, page, http, mcp (stdio or streamable HTTP + token headers; mcpServers config
  inline or by `config:` reference). Jev only CHOOSES values (ADR-0013). Live watch page
  (`run --watch [--host] [--pause]`), replay (`understudy watch <log>`), event-stream log
  (ADR-0014..0016). Docs: README, docs/USER_GUIDE.md, docs/WALKTHROUGH.md, docs/SKETCHES.md,
  docs/MCP_GUIDE.md, docs/DECISIONS.md (ADR-0001..0016), docs/SDLC.md.
- Sprints 1-4 merged and pushed; main = origin/main = 51fa684 (Merge sprint-4).
- Owner rules (also in memory): no back-compat; recard not a goal; version bumps only when asked;
  ONE question at a time; always `bobp make` / `bobp chat`; publish only via `bobp make push`;
  Jev chooses, never writes; verify with committed tests, never one-off scripts (AGENTS.md p.1).
- Make targets for tests: `test` (no browser), `test-browser` (headless Chromium, Jev double),
  `test-live` (real Jev, paid).

## Current Task
Sprint 6 COMPLETE - launched 2026-10-16 on branch `sprint-6` (308c242..8795f8d). Dashboard: `understudy dashboard <folder>`.
- 281 unit + 5 browser tests; ADR-0023..0026; CHANGELOG; chat archived (CHAT_sprint-6).
- Deviation flagged to owner: evening has an "evenings only" switch, not "seats together" (box office holds side-by-side only).
- Not merged/pushed: awaits the owner.

## Next Steps
1. On owner request: merge sprint-6 to main (--no-ff) and push via `bobp make push` (Tank).
2. Backlog "Next (from the sprint 6 retro)": tube label crowding, together switch, "yet" wording, split page.mjs.
3. Owner prefers short conversational replies, one question at a time; generic utilities from libraries.
