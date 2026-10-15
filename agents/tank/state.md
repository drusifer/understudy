# Tank State

## Context
- Build env done 2026-10-15 (uncommitted): package.json (npm, Node >=24, deps xstate+yaml only),
  package-lock.json, Makefile (help/install/test/lint/secrets/hooks/check/clean/distclean),
  eslint.config.js (recard rules minus browser bits), .nvmrc, .githooks/pre-commit, build/ ignored.
- docs/SDLC.md written - source of truth. Verified: distclean -> install -> install (lockfile
  unchanged) -> check green, 46/46 tests unchanged.
- No `bin` yet: bin/understudy.mjs does not exist; added (with `make run`) by the story creating it.
- Open questions for user (SDLC sec 6/7): branch convention, version-bump rule.
- No README in repo, so "README setup = make commands" item is N/A for now.

## Current Task
*devops build-env - 100% complete, handed to Smith (Gate 1).

## Next Steps
- At sprint close: *devops sdlc-check per docs/SDLC.md section 10.
- When a story adds Jev/playwright/MCP deps: Neo adds them; no Tank action unless mechanism changes.
