# Cypher State

## Context
- **What understudy is now** (since Sprint 19, merged and pushed 2026-10-30, `origin/main` = ea5f76b): a platform for automating decisions the way their owner makes them. One kind of sketch: a YAML file with `sources`, `sinks`, `outcomes`, `data` and a user-written `machine` (python-statemachine). Rules are `decide` trees with explicit YAML conditions (`eq ne lt le gt ge in not_in has`, `and or not`, slices `a:b` read as YAML 1.2 via ruamel), weights are numbers or `if/then/else`, a stage's deciders are blended per dimension, `forbid` drops options and always wins. Jev is a `kind: jev` source (rubric = `instructions` + `criteria`, `state` from other sources; one row per level). Every non-file read is captured under git-ignored `.understudy/cache/`; `--replay [run-id|folder]` runs offline from one complete run, never live. Docs: `docs/SKETCHES.md` (reference), `docs/USER_GUIDE.md`, `docs/DOMAIN.md`, ADR-0040..0045, design record `docs/sprints/DESIGN_SKETCH_MODEL.md`, epic `docs/sprints/EPIC_PYTHON_PORT.md`.
- **Code:** `src/sketch/` (loader, check, model, vocabulary, conditions, decide, blend, machine, run, stages, sql, cli, sources/{file,jev,capture,reader}); shared `src/machine_runner.py` (used by the ETL too), `src/jev.py`, `src/paths.py`; `src/cli.mjs` is only a launcher (`run`, `check`, `etl run`); `src/etl/` is the Sprint 16-18 household ETL (SQLMesh on DuckDB). Coffee example and fixtures: `tests/fixtures/coffee/` (committed real Jev answer in `replay/`).
- **Sprint 19 deleted the whole old Node player** (targets, apps, watch and dashboard servers, XState machine, 41 test files, 9 npm deps, `test-browser`/`test-live`/`install-browser`). `library`, `watch`, `dashboard` print "being rebuilt". Kept for slice C: `src/dashboard/` browser files. Still present until slices B/D: `examples/`, `schema/sketch.schema.json` (old), `seed/`, `docs/design/DASHBOARD.md`.
- **Epic (4 slices, owner appetite 2026-10-29):** A = Sprint 19 DONE; B = translate old examples (evening with a seating subsketch) or delete; C = dashboard and watch page over `events.jsonl`; D = delete the last Node (launcher, package.json, eslint, node:test). The epic's **purge list** is slice D's exit gate: one sketch format, one command set, one runtime, no duplicate code or docs.
- **Owner rules (also in memory):** no back-compat; YAGNY and DRY; ask only about consequential, hard-to-back-out decisions, one at a time, decide the rest and note it; short conversational replies; Jev chooses and never writes; Edit/Write tools for edits (no sed/python scripts, I slipped twice); always `bobp make` and `bobp chat`; push only via `bobp make push`; ask before merging/pushing.
- **Branches:** `main` (ea5f76b, pushed); `sprint-16`, `sprint-17`, `sprint-18`, `sprint-19` kept on purpose; the `understudy-sprint-16` worktree still exists and the owner said to leave it.
- **Open ETL items (Sprint 17 backlog):** net spending of $433k YTD looks too large (card-payment/transfer legs counted?), 270 merchants sent to review, Python port of the rest.

## Current Task
Status: Completed. Sprint 19 launched, merged and pushed. No work in flight.

### Progress
- [x] Epic framed, domain model, stories (one Smith rejection), architecture, plan, 7 phases, closeout, live Jev judgement, groom, acceptance, retros, launch, merge and push
- [ ] Slice B planning not started
- Working tree: only `agents/CHAT.md` modified (this checkpoint's chat post).

## Next Steps
1. Cold start: read the last messages of `agents/CHAT.md`, then this file. Nothing is blocked.
2. When the owner says go on the Python-port epic: cut `sprint-20` from `main` (no worktree), then `*plan sprint` for slice B: stories for translating the old examples into the new model (the evening example needs `on_empty: walk_away`, a seating subsketch with an ETL stage for adjacent seats, and probably MCP/HTTP source kinds or file fixtures; `docs/sprints/DESIGN_SKETCH_MODEL.md` section 7 sketches it). Candidates and retro items are in `docs/BACKLOG.md` under "From Sprint 19".
3. Before asking the owner anything, apply the rule: ask only if the choice is consequential and hard to back out; otherwise decide, note it, move on.
4. Other open threads the owner may raise: the net-spending check on the real ETL run, the 270 review merchants, removing the old worktree and branches (owner said keep them).
