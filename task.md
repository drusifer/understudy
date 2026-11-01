# Sprint 21 Task Board: the console in Python, and the last Node deleted

* **Goal**: `understudy dashboard` in Python; no Node left. **Branch**: `sprint-21`. **Plan**: `docs/sprints/USER_STORIES_SPRINT21.md`, `ARCH_SPRINT21.md`. **Decisions**: `docs/sprints/OWNER_DECISIONS_SPRINT21.md`.
* Process note: phases 1 and 2 were built before the planning artifacts and gates existed; their gates run now, after the fact.

## Phase 1: the console server (UND-74) - L2
- [x] Neo **UND-74** `src/dashboard/server.py`, `page.js`, `page.html`, CSS, fonts, `dashboard` command, `tests/python/test_dashboard.py`.
- [x] Trin UAT phase 1 (tests plus a real look at a real run in a browser)
- [x] Switch security review phase 1 (new network listener)
- [x] Morpheus review phase 1

## Phase 2: delete Node (UND-75) - L2
- [x] Neo **UND-75** removed package.json, lockfile, eslint, .nvmrc, .mjs, node tests; `bin/understudy`; Makefile Python-only.
- [x] Trin UAT phase 2 (`bobp make check` from the Python side; `bin/understudy check`/`run`)
- [x] Switch security review phase 2 (secrets scan; dependency surface shrank)
- [x] Morpheus review phase 2

## Phase 3: docs and close - L1
- [x] Oracle: README, USER_GUIDE, SKETCHES, DOMAIN, CHANGELOG, epic doc, ADR-0048, backlog
- [x] Tank `*devops sdlc-check` (SDLC rewritten Python-only)
- [x] Smith user test; retro; Cypher launch
