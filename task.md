# Sprint 20 Task Board: the evening and the household as sketches (CLOSED 2026-10-30)

* **Goal**: both of the owner's real pipelines run as sketches with `understudy run`.
* **Branch**: `sprint-20` (local, not pushed). **Plan**: `docs/sprints/USER_STORIES_SPRINT20.md`, `ARCH_SPRINT20.md`. **Retro**: `docs/sprints/RETRO_SPRINT20.md`. **Decisions**: `docs/sprints/OWNER_DECISIONS_SPRINT20.md` (1-40).
* The plan's seven phases were reshaped by the owner's decisions during the sprint; what was delivered is listed below.

## Delivered

- [x] **UND-68** Jinja2 sketches, `--with` and `with:`, `each`, `outcome`, `outputs`.
- [x] **UND-73** options read from rows (`{from, key}`), Jev choosing among them.
- [x] **Stage model** `map`/`reduce`/`sink`/`sketch`, `@stage` registry, `kind: stage` sources, `each` + `reduce` fold.
- [x] **UND-69** seating as a subsketch (adjacent runs, scoring stages).
- [x] **UND-70** the evening (`examples/evening/`).
- [x] **UND-71** the household as a sketch (`examples/household/`): CSV sources, `convert`, `pair`, `link`, `earlier`, `group`, `classify`, child sketches that ask Jev, a folding category namer. Real-file run done (5,074 records).
- [x] **UND-72** purge: old ETL, SQLMesh, MCP servers, `etl run`, old Node examples, `seed/`, old schema; docs, ADR-0047, changelog.
- [x] **Gate**: `bobp make check` (tests, lint, secrets) green; 221 Python and 19 JavaScript tests.
- [x] **Close-out**: SDLC doc matches the tooling (edited by Cypher; Tank to confirm), retro written, backlog updated.

## Not done (carried to the backlog)

- [ ] Per-phase Trin UAT and Morpheus review (the author reviewed at close only).
- [ ] The 1,706 records in category review; the $433k net spending; replay of a household run.
- [ ] Merge, tag and push: waiting for the owner.
