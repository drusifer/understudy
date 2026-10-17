# Cypher State

## Context
- understudy plays apps with Jev via sketches (`sketch.yaml`, + `hooks.mjs` for process/http).
  Targets: process, page, http, mcp (stdio or streamable HTTP + token headers; mcpServers config
  inline or by `config:` reference). Jev only CHOOSES values (ADR-0013). Live watch page
  (`run --watch [--host] [--pause]`), replay (`understudy watch <log>`), event-stream log
  (ADR-0014..0016). Docs: README, docs/USER_GUIDE.md, docs/WALKTHROUGH.md, docs/SKETCHES.md,
  docs/MCP_GUIDE.md, docs/DECISIONS.md (ADR-0001..0016), docs/SDLC.md.
- Sprints 1-9 merged and pushed to origin/main (2026-10-16). Sprint 8: bay behind the printer
  (UND-35, ADR-0028). Sprint 9: THEME switch steampunk/professional/starship (UND-36, ADR-0029).
  Evening weights now 0-10. Chat for sprints 7-9 archived: agents/chat_archive/CHAT_sprint-7-9.md.
- Owner rules (also in memory): no back-compat; recard not a goal; version bumps only when asked;
  ONE question at a time; always `bobp make` / `bobp chat`; publish only via `bobp make push`;
  Jev chooses, never writes; verify with committed tests, never one-off scripts (AGENTS.md p.1).
- Make targets for tests: `test` (no browser), `test-browser` (headless Chromium, Jev double),
  `test-live` (real Jev, paid).

## Current Task
Between sprints. Sprint 9 (themes) closed, docs groomed (README shows the dashboard), merged to main
and pushed. No dashboard running in the background.

## Next Steps
1. `/init` -> resume as Cypher; ask the owner what is next (one question at a time, short replies).
2. Backlog "Next" sections (docs/BACKLOG.md): sprint 9 (measure contrast in test; tube label overlap),
   sprint 8 (split page.mjs ~690 lines - overdue; browser-test bay AC4-5; foldable sticker),
   sprint 6 ("yet" wording).
3. Any new feature: Tier 2 mini-sprint (story+arch doc, task.md, phases, close) like sprints 7-9.
