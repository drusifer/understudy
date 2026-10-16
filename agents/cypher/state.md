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
Sprint 5 Stage 1 Step 1 - stories rewritten (UND-18..26, 29 pts), handed to Smith Gate 1.
- Branch `sprint-5` cut from main 51fa684; task.md archived to docs/sprints/TASKS_SPRINT4.md.
- docs/BACKLOG.md "Sprint 5" holds every owner decision (gates, weight-shaped scores multiplied,
  Jev Score factor, shortlist + mood Choice, inputs from CLI, walk away). "Sprint 6" = steampunk dashboard.
- docs/sprints/USER_STORIES_SPRINT5.md is the superseded hard-rules draft (UND-18..23).
- Owner wants SHORT conversational replies, one chunk at a time (memory).

## Next Steps
1. DONE: shortlist = all qualifying (bounded by at_most/at_least); defaults proposed.
2. DONE: rewrote USER_STORIES_SPRINT5.md from BACKLOG "Sprint 5" (keep UND-18 box office, UND-19 ratings
   +reviews, UND-20 several servers; new: gates, scores, Jev score factor, shortlist+mood, inputs,
   walk away, example+docs). Self-check STORIES rubric -> Smith Gate 1.
3. Uncommitted: agents/CHAT*.md, state files, task.md move, BACKLOG, stories draft - commit with the
   first reviewed phase.
