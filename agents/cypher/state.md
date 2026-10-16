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
Sprint 5 COMPLETE - launched 2026-10-16 on branch `sprint-5` (phase commits 3842e55..9966798 + close).
- UND-18..26 delivered; 254 unit, 4 browser, 7/7 live; ADR-0017..0022; CHANGELOG; chat archived (CHAT_sprint-5).
- Not merged/pushed: awaits the owner ("merge and push sprint 5" → Tank: bobp make push on main after --no-ff merge).

## Next Steps
1. Ask the owner the open question (BACKLOG "Next"): should a decided argument wait until nothing is held back?
2. On owner request: merge sprint-5 to main and push (Tank, `bobp make push`).
3. Sprint 6 = the steampunk dashboard (BACKLOG "Sprint 6": knobs to 11, flux-capacitor edges) - shape with the owner one question at a time, short replies.
