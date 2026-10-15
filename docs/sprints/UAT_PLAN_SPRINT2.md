# Sprint 2 Acceptance Test Plan (UAT): Play a JSON API, and any web page without changing it

*   **Owner**: Trin (per phase) / Smith (end to end) · **Date**: 2026-10-15 · **Branch**: `sprint-2` at `181b681`
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT2.md` · **Status**: PASSED — Smith approved

## 1. Scope of Acceptance Testing

UND-6 (HTTP target), UND-7 (hookless web page, generic page app), UND-8 (docs), through the real
`understudy` command via `bobp make run`. Live runs use real Jev (owner-approved, capped at 20
steps). Out of scope: free-text fields, MCP, auth (stories' Out of Scope).

## 2. Preconditions & Test Environment Setup

| Item | Value |
|---|---|
| Machine | Raspberry Pi (linux arm64), Node v24.13.0, Playwright 1.62.1 Chromium |
| Setup | `bobp make install` from clean (Tank's sdlc-check) |
| Key | `TYPESAFE_API_KEY` set; unset for key tests |
| Evidence | outputs posted to `agents/CHAT.md`; logs in `build/runs/{vending-http,signup-web}/` |

## 3. Scenario-Driven Acceptance Test Cases

### `UAT-UND6-01`: play the API live
`bobp make run ARGS="run examples/http --steps 20"` → server started on a free port, `coin:1`,
`buy:water`, outcome `done`, exit 0; each step line has `response.status`. **PASS** (twice).

### `UAT-UND6-02`: attach to a running service
Hand-started `PORT=18765 node examples/http/server.mjs`, adapter with a full `url` and no
`command` → played to `done`; `GET /machine` still answers 200 afterwards. **PASS**.

### `UAT-UND6-03`: a refused move is logged, not fatal
End-to-end test (`tests/examples.test.js`) buys before paying: step 1 `response: {status: 402}`,
run continues to `done`. **PASS**.

### `UAT-UND7-01`: play the unmodified page live
`bobp make run ARGS="run examples/web --steps 20"` → `button:Free`, `button:Light`,
`button:Accept`, outcome `done`, exit 0; no understudy code in `index.html`/`app.js`; adapter
4 lines; `check` says `(page, generic page app)`. **PASS**.

### `UAT-UND7-02`: a leftover hook is ignored
Copy of `examples/web` whose `app.js` defines a `window.__understudy` that throws if called →
played identically, hook never called. **PASS**.

### `UAT-UND8-01`: docs
Documented commands run as written; links clean; ADR-0007..0010 recorded, ADR-0002 superseded.
`grep __understudy` is clean in README, ADAPTERS, USER_GUIDE, WALKTHROUGH, examples and src; it
still matches history (sprint records, the ADR-0002 record) on purpose. **PASS** with that
reading of UND-8 AC2 (agreed by Morpheus: no-back-compat applies to code and live docs, not to
history).

## 4. Negative & Error Handling Test Cases

| ID | Scenario | Expected (exit) | Result |
|---|---|---|---|
| `UAT-ERR-01` | API server exits after a coin | `node server.mjs exited with code 5 before the end state` (1) | PASS |
| `UAT-ERR-02` | started server never listens | `no first move from http://127.0.0.1:N within 0.3 s - nothing answered GET /state` (1, unit) | PASS |
| `UAT-ERR-03` | connection dropped | `lost the connection to <url>: ...`, outcome `connection-lost` (1, unit) | PASS |
| `UAT-ERR-04` | web part without its `showing` end | `stalled: nothing to do for 10 s after step 3 ... add a showing guard` (1) | PASS |
| `UAT-ERR-05` | `hook: 'x'` in a page target | `target.hook is not a page target field (known: root, page)` (2) | PASS |
| `UAT-ERR-06` | http adapter without `state` | `target.state is required for an http target (the path a look GETs, e.g. /status)` (2) | PASS after DEF-05 |
| `UAT-ERR-07` | `{port}` url with no `command` | refused at `check` (2) | PASS after DEF-06 |
| `UAT-ERR-08` | control gone before the move | `could not press button "Free" - it is no longer on the page (...)` (1, unit) | PASS |
| `UAT-ERR-09` | Chromium after runs | no headless Chromium process left | PASS |

## 5. Defect Summary & Gate Outcome

| Defect ID | Severity | Description | Assignee | Status |
|---|---|---|---|---|
| `DEF-05` | Major | http adapter without `state` passed `check`, then failed after 10 s with `GET undefined` | Neo | Resolved (181b681) |
| `DEF-06` | Minor | `{port}` without `command` only caught at run time | Neo | Resolved (181b681) |

**Gate outcome**: PASSED. rubric UAT: COVER=S STEPS=A FAIL=S DATA=A EVID=A.
