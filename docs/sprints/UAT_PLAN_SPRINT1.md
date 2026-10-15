# Sprint 1 Acceptance Test Plan (UAT): MVP first run — an understudy plays a CLI app and a web page

*   **Owner**: Trin (per-phase) / Smith (end to end) · **Date**: 2026-10-15 · **Branch**: `sprint-1` at `a2fff13`
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT1.md` · **Status**: PASSED — Smith approved

## 1. Scope of Acceptance Testing

All five stories (UND-1..5) through the real `understudy` command, as an automation author
would use it. Live runs call real Jev (owner-approved, capped at 20 steps or fewer). Out of
scope: HTTP targets, recard migration, MCP, multi-actor (see stories' Out of Scope).

## 2. Preconditions & Test Environment Setup

| Item | Value / how to get it |
|---|---|
| Machine | Raspberry Pi (linux arm64), Node v24.13.0 |
| Setup | `bobp make install` (and `bobp make install-browser` where Chromium is missing) |
| Key | `TYPESAFE_API_KEY` set in the environment (unset for the key tests) |
| Chromium | Playwright 1.62.1's bundled build; `/usr/bin/chromium` present as fallback |
| Evidence | stdout/stderr captured in `agents/CHAT.md` posts; logs in `build/runs/<adapter>/` |

## 3. Scenario-Driven Acceptance Test Cases

### Test Case `UAT-UND1-01`: play the CLI example live
1. `bobp make run ARGS="run examples/cli --steps 20"`
2. **Expect**: first stderr line names adapter, program and log file; one JSON line + one
   readable line per step; final line `{"final":true,"outcome":"done",...}`; exit 0; the
   `.jsonl` file holds exactly the stdout lines.
- **Result**: PASS — 3 steps (size:medium, milk:whole/oat, confirm:order), exit 0. Log == stdout is asserted by `tests/run.test.js`.

### Test Case `UAT-UND1-02`: the step cap
1. `understudy run examples/cli --steps 1`
2. **Expect**: `stopped after 1 step without reaching the end state (last state: answering)`, final line `step-cap`, exit 1, no program left running.
- **Result**: PASS (after DEF-02).

### Test Case `UAT-UND2-01`: play the web example live
1. `understudy run examples/web --steps 20`
2. **Expect**: page served on 127.0.0.1, headless; outcome `done`; exit 0; no Chromium process afterwards (`ps -eo args | grep [c]hrom`).
- **Result**: PASS — plan:free, theme:light, terms:accept; no Chromium left.

### Test Case `UAT-UND2-02`: one part format, no transport words
1. `grep -niE 'browser|page|click|process|program|terminal|typed|stdin' examples/*/part/*.yaml`
2. **Expect**: no matches; both parts have the same states.
- **Result**: PASS.

### Test Case `UAT-UND3-01`: `check` on good parts
1. `understudy check examples/cli` and `examples/web` without a key.
2. **Expect**: `examples/cli: part OK - 5 states, 1 question, adapter coffee-cli (process)`, exit 0.
- **Result**: PASS (both).

### Test Case `UAT-UND5-01`: adapters are small and documented
1. `wc -l examples/*/adapter.mjs`; read `docs/ADAPTERS.md` cold; `understudy library examples/web`.
2. **Expect**: each < 150 lines; the doc answers "add my own guard" and "add a new kind of target" without reading `src/`; every name it lists is in `library`.
- **Result**: PASS — 51 and 24 lines.

## 4. Negative & Error Handling Test Cases

| ID | Command | Expected (exit) | Result |
|---|---|---|---|
| `UAT-ERR-01` | `run examples/web` with no key | `understudy run needs a TypeSafe key: set TYPESAFE_API_KEY` (2), nothing started | PASS |
| `UAT-ERR-02` | `check` on a copy with `src: lok` | file, `states.looking.invoke.src`, `no actor "lok" - did you mean "look"?` (2), no stack | PASS |
| `UAT-ERR-03` | `check` on a copy with `Pick 3 steps` | `next.instructions carries a number in the question...` (2) | PASS |
| `UAT-ERR-04` | `check examples/nope` / `check package.json` | `no such directory` / `not a directory - give the example directory...` (2) | PASS (after DEF-01) |
| `UAT-ERR-05` | `run ... --steps` / `--steps 0` | `--steps needs a number, e.g. --steps 20` / `must be a positive whole number (got "0")` (2) | PASS (after DEF-03) |
| `UAT-ERR-06` | `run examples/web --headed` | `no option "--headed" for run` (2) | PASS |
| `UAT-ERR-07` | CLI app copy that exits 4 after one answer | `node app.mjs exited with code 4 before the end state` (1), final `app-exited` | PASS |
| `UAT-ERR-08` | web copy without the hook | after 10 s: `no first move from <url> within 10 s - the page never exposed window.__understudy (it showed: "...")` (1); no Chromium left | PASS |
| `UAT-ERR-09` | Playwright's Chromium missing (`PLAYWRIGHT_BROWSERS_PATH=/nonexistent`) | falls back to `/usr/bin/chromium`, run passes; with no Chromium at all the hint `run: bobp make install-browser` (2) — unit-tested, as this Pi has a system Chromium | PASS |

## 5. Defect Summary & Gate Outcome

| Defect ID | Severity | Description | Assignee | Status |
|---|---|---|---|---|
| `DEF-01` | Minor | missing directory / file reported as "no adapter.mjs" | Neo | Resolved (a2fff13) |
| `DEF-02` | Minor | "stopped after 1 steps" | Neo | Resolved (a2fff13) |
| `DEF-03` | Minor | `--steps` with no value said `(got "")` | Neo | Resolved (a2fff13) |
| `DEF-04` | Cosmetic | `understudy: understudy run needs a TypeSafe key...` repeats the name (text fixed by UND-4 AC1) | Cypher | Backlog |

**Gate outcome**: PASSED. rubric UAT: COVER=S STEPS=A FAIL=S DATA=A EVID=A.
