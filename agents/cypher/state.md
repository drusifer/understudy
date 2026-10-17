# Cypher State

## Context
- understudy plays apps with Jev via sketches (`sketch.yaml`, + `hooks.mjs` for process/http).
  Targets: process, page, http, mcp. Jev only CHOOSES values (ADR-0013). Watch page, replay,
  event-stream log. The `understudy dashboard <folder>` console is most of recent work.
- Sprints 1-15 merged and pushed: origin/main = 3507240 (2026-10-17). Recent:
  10 sketch JSON Schema (ADR-0031); weight inputs = share of full weighting 3 (ADR-0030);
  11 light/dark MODE for every theme (ADR-0032); 12 STEP/PAUSE on the console (ADR-0033);
  13 every Jev request sees `inputs`, `pick.with` removed (ADR-0034); 14 statechart as a layered
  flow via elkjs on the server, rectangular screens except steampunk's round tube (ADR-0035);
  15 per-theme flair + five real gauges (ADR-0036), console fills big screens.
- Dashboard pieces: src/dashboard/{page.html,page.css,page.mjs,theme-*.css,flow.mjs,tube.mjs,
  rack.mjs,runner.mjs,settings.mjs,server.mjs,console.mjs}. Printer = spool-to-spool paper behind
  glass, OPEN release latch reveals the YAML bay; dashboard served at the root (no token).
- Demo: `bobp make run ARGS="dashboard examples --port 4180 --host 0.0.0.0"` in the background,
  http://192.168.86.69:4180/ - owner lets me restart it any time (memory). It is running now.
- Owner rules (also in memory): no back-compat; ONE question at a time, short replies; always
  `bobp make` / `bobp chat`; push only via `bobp make push`; Jev chooses, never writes; edit files
  with the Edit/Write tools, never python/sed scripts; gauges show real data only.
- Owner screenshot of the console kept at build/Screenshot From 2026-10-17 10-15-45.png (ignored).

## Current Task
Between sprints. Sprint 15 + big-screen fixes merged to main and pushed (3507240). Working tree
clean except the team chat files.

## Next Steps
1. `/init` -> resume as Cypher; ask the owner what is next (one question at a time).
2. Backlog (docs/BACKLOG.md "Next" sections): steampunk flow labels small in the round tube;
   split src/dashboard/page.mjs (~1000 lines, overdue); browser-test bay AC4-5; measure contrast
   in a test; a `genre` input for the evening; try the schema in a real editor.
3. New features: Tier 2 mini-sprint like sprints 10-15 (story+arch doc in docs/sprints/,
   task.md, branch sprint-<N>, phases, close with ADR/CHANGELOG/BACKLOG/SDLC line), screenshots
   checked with a scratch headless script before reporting.
