# Tank State

## Context
- Sprint 16 Phase 0 mechanism is approved by the owner (“proceed”, 2026-10-17) and Tank.
- Toolchain is pinned: CPython 3.12.15, uv 0.13.0, SQLMesh 0.236.3, Python DuckDB 1.5.6, and `@duckdb/node-api` 1.5.6-r.1 (the published Node client build for DuckDB core 1.5.6).
- Added project-local Python manifest/lock/environment, aggregate and language-specific Make targets, a synthetic SQLMesh→Node DuckDB→Python reopen probe, SDLC and README setup instructions. `clean` now preserves `build/build.out` for bobp capture.
- Verified with `bobp make distclean`, fresh `bobp make install`, `bobp make check`, a second `bobp make install`, and `bobp make probe-etl`; all passed. Probe uses temporary synthetic data only. No household CSV was read or copied.
- npm initially rejected unpublished `@duckdb/node-api@1.5.6`; pinned available `1.5.6-r.1` matching DuckDB core 1.5.6 and documented it.
- No commit; SDLC requires a Morpheus-reviewed phase before committing. Worktree also contains sprint planning artifacts from earlier gates.

## Current Task
- **Status:** Complete — Sprint 16 Phase 0 setup/probe and sprint-close SDLC conformance check.
- [x] Record the approved mechanism and exact published package versions.
- [x] Add pinned Node/Python manifests, lockfiles, local environment, and `bobp make` targets.
- [x] Update SDLC and README; verify clean install and repeated install.
- [x] Verify synthetic SQLMesh CSV materialization and sequential Node write/Python reopen against the same DuckDB file.
- [x] Run aggregate tests, lint, and secret scan through `bobp make check`.
- [x] Sprint close: `bobp make distclean`, `bobp make install`, and `bobp make check` passed; a repeated install was idempotent. Updated `docs/SDLC.md` Last verified for Sprint 16 close.

## Next Steps
1. Hand off to Oracle for Sprint 16 document grooming and chat report archive.
2. Preserve private CSV data under ignored `build/runs/`; no household exports were read.
