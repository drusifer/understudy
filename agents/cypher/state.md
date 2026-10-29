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
2026-10-27 (end of day): Sprint 16 launched, merged and pushed (main 5786fc8). Sprint 17 (UND-49..55, 29 pts) is in progress on branch `sprint-17` (worktree `/home/drusifer/Projects/understudy-sprint-17`, from main 5786fc8): stories approved at Smith Gate 1 (UND-53 split into 53+55), architecture at Gate 2, plan approved, Phase 0 spike done (Python controller; ADR-0038/0039), Phase 1 (source servers, hydration; commit 04e250d) and Phase 2 (purchase pairing, Amex-account detection; commit b5a0f71) done and committed locally, NOT pushed. Real files (counts only): 4,276 of 4,321 Amex rows pair. STOPPED before Phase 3: the Monarch card account changes sign convention in Nov 2025 (charges positive with Amex-style categories until Oct 2025, negative after), so refund and transfer rules need a decision on the older history. Owner asked one question at a time; the question posed: normalise by an auto-detected per-account cutoff date (recommended), or restrict refund/transfer logic to the consistent period.

Owner decisions today (details in `agents/cypher/platform_decision_2026-10-27.md`): Python for all of understudy, no back-compat; sketches stay no-code and custom, but no new ETL language or state machine format (SQL on DuckDB; `python-statemachine` YAML); no XML; Jev categories from Monarch's 180 plus a Noul "does it fit", new names from the MCC list; transfers kept as two linked records; refunds linked to the merchant; IO is JSONL in and out. Movie selector (TMDB + OMDb, keys in `.env`; OMDb key was still rejected) is in `docs/BACKLOG.md` on `main`'s working tree.

## Next Steps
1. Get the owner's answer on the pre-Nov-2025 sign convention of the Monarch card account; record it as an amendment to `ARCH_SPRINT17.md` section 3 (and a story note on UND-51/52), then run Phase 3 (`transfer_pairs`, `refund_candidates`, refund Jev stage) per `task.md`.
2. Then Phase 4 (categories: Noul fit + Choice, MCC naming via `iso18245`, needs `typesafe-sdk` and a Jev double; a live probe only with the owner's go-ahead) and Phase 5 (Python controller on `python-statemachine` YAML, JSONL output, delete the Node ETL: `src/etl/run.mjs`, `categories.mjs`, `csv.mjs`, old models, `review.csv`; owner has not yet confirmed that deletion).
3. Closeout per `task.md` (Tank check, Oracle groom, Smith test, retro, launch). Push `sprint-17` or merge only when the owner asks.
4. Work rule slip to avoid: edit files with the Edit tool, never `sed -i` (done three times this session on `task.md`).
5. Python port epic still to frame (`*epic`): `tags` missing from python-statemachine's schema, `elkjs` replacement.
