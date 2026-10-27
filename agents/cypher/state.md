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
2026-10-27: Sprint 16 (UND-46..48, SQLMesh + DuckDB ETL, built 2026-10-17) accepted by the owner and launched; its stories file was overwritten by mistake and rebuilt (reconstruction noted in the file). Nothing on `sprint-16` is committed or merged: that waits for the owner. Sprint 17 stories (UND-49..54: source servers, sign-flipped match, transfers as linked records, refunds, Noul + MCC category naming, JSONL result) are drafted in `docs/sprints/USER_STORIES_SPRINT17.md`, not yet through Smith Gate 1.

Owner decisions today (details in `agents/cypher/platform_decision_2026-10-27.md`): Python for all of understudy, no back-compat; sketches stay no-code and custom, but no new ETL language or state machine format (SQL on DuckDB; `python-statemachine` YAML); no XML; Jev categories from Monarch's 180 plus a Noul "does it fit", new names from the MCC list; transfers kept as two linked records; refunds linked to the merchant; IO is JSONL in and out. Movie selector (TMDB + OMDb, keys in `.env`; OMDb key was still rejected) is in `docs/BACKLOG.md` on `main`'s working tree.

## Next Steps
1. Owner decides when to commit and merge `sprint-16` (`bobp make push MSG=...`); the tree mixes Sprint 16 work with today's docs, `.gitignore` and Sprint 17 draft.
2. Smith Gate 1 on `USER_STORIES_SPRINT17.md`, then Morpheus architecture (the source servers and sketch runtime language depend on the Python epic).
3. Frame the Python port as its own epic (`*epic`): verify `python-statemachine` YAML coverage of `turn:` (tags, guards, invoke), `typesafe-sdk` per-answer probabilities, and the `elkjs` layout replacement.
4. Main tree still holds uncommitted `Makefile` (`.env` sourcing), `.gitignore` (`data/`) and `docs/BACKLOG.md` (movie selector) edits; the worktree has its own copies of the first two.
