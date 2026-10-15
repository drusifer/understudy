# Morpheus State

## Context
- docs/EXTRACTION_MAP.md (copied from recard) is the plan: core moves as-is, the rest is
  generalized around an app-adapter contract, game content stays in recard as its adapter.
- Owner decisions (2026-10-15): transport-neutral adapter (web page hook is ONE target;
  CLI and HTTP next to it; sprint 1 proves it with web + CLI), git dependency, Jev required
  (unit tests double the judge at the SDK seam: `judge.systemOne(...)`).
- Adapter shape seen in recard today (seat `services`): `peer` = target {view, act, say,
  talk}, `game` = app knowledge {project, options, act, propose}, plus judge, questions,
  player. Generalize names: `TABLE` event -> e.g. `OBSERVE`, `services.game` -> `services.app`.

## Current Task
Architecture for sprint 1 not started - waits on Smith Gate 1 of the stories.

## Next Steps
After Gate 1: append the architecture to docs/sprints/USER_STORIES_SPRINT1.md (adapter
contract, CLI target over a child process, web target over Playwright, run loop from
seed/recard/tools/jev/runner.mjs), then Smith Gate 2.
