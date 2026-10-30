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
Status: Sprint 20 in progress on branch `sprint-20` (local only, not pushed). Stories (Smith Gate 1) and architecture (Gate 2) approved, plan approved. **Phase 1 code committed (ef98618) but not yet UAT'd by Trin or reviewed by Morpheus.**

### Progress
- [x] Epic slice B planned: `docs/sprints/USER_STORIES_SPRINT20.md` (UND-68..73), `ARCH_SPRINT20.md`, `task.md` (7 phases).
- [x] Phase 1 code (Task 1.1): Jinja2 sketches, `--with`, per-call `with`, unused-name check, `each`, final-state `outcome`, `outputs`/`from` (no `decider` keyword), 179 Python tests green, lint clean.
- [ ] Phase 1 UAT (Trin) and review (Morpheus); `docs/SKETCHES.md` is updated.
- [ ] Phases 2-7 not started (UND-73 candidates/shortlist/Jev pick, UND-69 seating, UND-70 evening, UND-71 ETL as sketch, UND-72 purge).

## Next Steps
1. **Read `docs/sprints/OWNER_DECISIONS_SPRINT20.md` first.** It holds every owner answer (decisions 1-20) and the choices Claude made alone overnight (A-F). Check it before asking the owner anything; record each new answer there at once.
2. Ask the owner to review choices A-F and the two open points; the owner may overturn any.
3. UND-73 needs a re-think under "take away" (the owner's rule): ranking and shortlisting showings may be plain SQL stages, leaving only "a Jev choice among runtime options" as new; discuss before building. ARCH_SPRINT20 still describes the original UND-73 (candidate outcomes, `shortlist:`, Jev `options:`).
4. Then phases 3-7 per `task.md`; the ETL expected-result file must be committed (Phase 5) before any ETL change.
5. Owner rules: no back-compat, YAGNI, reuse existing syntax, no new words, one question at a time, define names before using them, Edit tool for edits, `bobp make` only, push only via `bobp make push` and only when asked.
6. Other open threads: net-spending check ($433k), 270 review merchants, old worktree and branches (owner said keep).
