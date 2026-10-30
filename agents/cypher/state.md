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

### Progress (2026-10-30, branch `sprint-20`, local only, last commit 2dce220, 220 Python tests, lint clean)
- [x] Planning: stories UND-68..73, architecture, task board approved.
- [x] Phase 1 (UND-68): Jinja2 sketches, `--with` / per-call `with`, unused-name check, `each`, final-state `outcome`, `outputs`.
- [x] Phase 2 (UND-73): options read from rows `{ from, key }`, `shortlist`, Jev `options`.
- [x] Stage model (decisions 23-33): `@stage` registry with typed signatures; `do: { map|reduce|sink|sketch: {...} }` + `with:` beside; `blend` is `reduce.blend`; `kind: stage` sources (lazy, once); stages `map.adjacent_runs/prefer_order/prefer_middle/weigh`, `reduce.max/min/any`; single-row guards; `center` (American spelling).
- [x] Phase 3 (UND-69): `tests/fixtures/evening/seating.yaml` + `seats.jsonl` + `test_sketch_seating.py` (blocks, weights, outcome none).
- [ ] Trin UAT and Morpheus review of phases 1-3 (not done).
- [ ] Phase 4 (UND-70 the evening), Phase 5-6 (UND-71 ETL as sketch; freeze expected result first), Phase 7 (UND-72 purge + docs).

## Next Steps
1. **Read `docs/sprints/OWNER_DECISIONS_SPRINT20.md` first** (decisions 1-33, choices A-H all accepted). Record each new owner answer there at once; check it before asking anything.
2. Phase 4: move `seating.yaml`/`seats.jsonl` to `examples/evening/`, write `evening.yaml` (showings, films, ratings, reviews fixtures; `each` over films with a Jev review score; weights as `--with`; shortlist of 5 and Jev pick; calls `seating` with `with:`; walk away = final state `outcome`), replacing the old Node example. The unresolved piece: how the evening ranks showings with `map.weigh` + `reduce.max` and joins audience scores to showings by title (a join map is not built; ask the owner before adding one).
3. Open (owner said wait): shape of non-weights outputs (a `hold`); `from:` as a blend entry key (owner unsure, kept for now).
4. Then UND-71 (ETL), UND-72 (purge), Trin/Morpheus gates, Tank sdlc-check, Oracle groom, Smith test, retro, Cypher launch. Do not push or merge without the owner.
5. Owner rules: no back-compat, YAGNI, reuse existing syntax, no new words, one question at a time, define names before using them, Edit tool for edits (no sed/python scripts), `bobp make` only, American spelling, push only via `bobp make push` and only when asked.
6. Other open threads: net-spending check ($433k), 270 review merchants, old worktree and branches (owner said keep).
