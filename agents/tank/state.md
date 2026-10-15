# Tank State

## Context
- docs/SDLC.md current; Last verified at sprint 1 close (2fba1d8): distclean->install x2
  (lock unchanged)->check 93/93 (96 after Smith fixes), test-live green.
- Make targets: help install install-browser test test-live lint secrets hooks check run clean distclean.
- Deps: xstate, yaml, @typesafe-ai/sdk ^0.6.0, playwright ^1.62.1 (locked 1.62.1 to share
  recard's Chromium in ~/.cache/ms-playwright).
- Open SDLC questions for the owner: version bump rule (proposal: bump + tag at sprint close).

## Current Task
None.

## Next Steps
- Next sprint close: *devops sdlc-check per SDLC §10.
- If a sprint adds an HTTP target with a local server, check it needs no new make target.
