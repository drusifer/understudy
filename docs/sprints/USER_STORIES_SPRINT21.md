# Sprint 21 User Stories: the console in Python, and the last Node deleted

*   **Total Points**: 8 (Tier 2: epic slices C and D, `EPIC_PYTHON_PORT.md`)
*   **Branch**: `sprint-21`
*   **Source**: Owner, 2026-11-01: slices C and D in one sprint (`OWNER_DECISIONS_SPRINT21.md` 1); "ok to use javascript in the dashboard" (2).
*   **Status**: Written alongside the build; see the retro for the process miss.

## Goal

`understudy dashboard` serves a read-only console over the runs under `build/runs/`, from Python, with the browser page in plain JavaScript and CSS. Then Node is gone: no `package.json`, eslint, `node:test`, `.mjs` or launcher; the `understudy` command is a shell script over the Python package. The epic's purge list is empty.

## Assumptions made for the owner (decided, not asked)

1. The console **watches**; it does not start runs or edit YAML (YAGNI; `understudy run` starts runs). The old play controls, faders, dial, bay and cheat sheet are removed.
2. The server is standard-library `http.server`; no new dependency.
3. Fonts the CSS needs are copied into `src/dashboard/fonts/` (SIL OFL) because `node_modules` goes away.
4. The page JavaScript has no automated test; every decision about what is shown (printed lines, tube, gauges) is made in Python and tested there.
5. The event stream gains nothing new this sprint; the console draws the five event kinds `events.jsonl` already has.

## STORY-UND-74: Watch a run in the console
**Points:** 5

**As the** owner, **I want** to open the console and see my runs, pick one, and watch its log, stages and gauges (live while it runs), **so that** I can see what a pipeline is doing without reading JSON.

**Acceptance criteria**
1. `understudy dashboard [folder] [--port N]` serves `/` on 0.0.0.0 (owner, 2026-11-01); the folder defaults to `build/runs`.
2. A rack tab per run, newest first; with no runs the page says so.
3. The printer shows one line per event with its clock; failures are marked.
4. The tube shows one lamp per top-level stage (complete, running, failed).
5. Four gauges (STAGES, FAILED, JEV, ELAPSED) read the run's own files; none is decoration.
6. A running run's new lines appear without reload; the stream ends when the run finishes.
7. Themes (3) and light/dark/auto still work and are remembered.
8. Only the page files, fonts and run folders are reachable; no path escapes.

## STORY-UND-75: Delete the last Node
**Points:** 3

**As the** owner, **I want** one toolchain, **so that** every change is paid for once.

**Acceptance criteria**
1. `package.json`, lockfile, eslint config, `.nvmrc`, every `.mjs` and the node tests are deleted.
2. `bin/understudy` starts the Python CLI; `bobp make run` and `bobp make dashboard` use it.
3. `bobp make install`, `test`, `lint`, `check` work with Python only; `docs/SDLC.md` says so (Tank).
4. README, USER_GUIDE, SKETCHES, DOMAIN, CHANGELOG and the epic doc no longer mention Node as live; ADR records the end of the Node side.
5. The epic's purge list has no open item.
