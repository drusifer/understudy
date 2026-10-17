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
Between sprints. Sprints 5-7 merged and pushed. After sprint 7, on main: dashboard opens on a sketch
with inputs (2e4b7c2), layout tightened per owner - tube centre, printer left, compact vertical faders
right, rack as tabs, everything fits one 1600x960 screen (3650ba1, c596ca2); pushed with this checkpoint.
- A dashboard was left running in the session's background: `understudy dashboard examples --port 4180
  --host 0.0.0.0` (http://192.168.86.69:4180/d/<token>/). It ends with the session; restart the same way.
- Open owner note: shrunken mood-dial labels (~11px) may need more room.

## Next Steps
1. `/init` -> resume as Cypher; ask the owner what is next (one question at a time, short replies).
2. Backlog "Next (from the sprint 6 retro)": tube label crowding, "yet" wording, split page.mjs (~600 lines).
3. Any new feature: Tier 2 mini-sprint (story+arch doc, task.md, phases, close) like sprint 7.
