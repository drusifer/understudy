# Oracle State

## Context
- 2026-10-15 groom (owner request): added README.md, docs/USER_GUIDE.md, docs/WALKTHROUGH.md;
  populated agents/PROJECT.md; fixed stale status lines (CHANGELOG, task.md) after the merge.
- All user-facing commands are written as `bobp make ...` (owner: "USE BOBP"); team updates via `bobp chat`.
- Walkthrough break-it messages were verified with `bobp make run ARGS="check ..."` on scratch copies.
- Doc map lives in README.md "Documentation" table; keep it current when docs are added.
- agents/DOCUMENTATION_INDEX.md is Bob Protocol scaffolding (links STARTUP.md, SHORTHAND_GUIDE.md,
  docs/WALKTHROUGH.md as a Bob walkthrough) - not understudy's index; left for Bob.
- Open: tag v0.1.0 points at 66ce717 (initial commit), must move to 766a47c (owner action).

## Current Task
Groom done; changes uncommitted (owner commits).

## Next Steps
- When the tag is moved: update the status lines in agents/PROJECT.md and task.md.
- Next sprint close: groom, ADRs/lessons, `bobp chat-report --moniker SPRINT_2`.
