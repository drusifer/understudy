# Cypher State

## Context
- Understudy = recard's Jev + XState harness, generalized into a standalone automation tool
  (named 2026-10-15). Owner decisions: web + CLI/HTTP targets (transport-neutral adapter),
  recard consumes via git dependency on tags, Jev required. See docs/EXTRACTION_MAP.md.
- Files were copied in from recard d817d3c (src/, tests/, seed/). Nothing deleted in recard.

## Current Task (2026-10-15) - Sprint 1 stories: DRAFTED, Gate 1 NOT run
docs/sprints/USER_STORIES_SPRINT1.md: UND-1 CLI target (5), UND-2 web target (3),
UND-3 broken part refused at load (2), UND-4 Jev key required (1), UND-5 adapter doc +
`understudy library` (2) = 13 pts, Tier 1. Assumptions listed for the owner to confirm
(HTTP next sprint, recard migration later, examples/ demo apps, `understudy` bin).
Stopped here on the owner's request ("stop once the files are moved in").

## Next Steps
- Owner confirms or edits the assumptions, then @Smith *user review stories (Gate 1).
- Tank first: build env (package.json, Makefile, lint/test) so the copied tests run.
