# Sprint 4 Task Board: Watch the understudy live

*   **Goal**: `understudy run <sketch> --watch` shows the statechart, the current state and each Jev decision live in a browser page, with pause/step/resume; `understudy watch <log>` replays a finished run; the log carries everything needed.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 16 (UND-13 3, UND-14 5, UND-15 3, UND-16 3, UND-17 2)
*   **Branch**: `sprint-4`
*   **Stories / Arch**: `docs/sprints/USER_STORIES_SPRINT4.md`, `docs/sprints/ARCH_SPRINT4.md` (sprint 3 board: `docs/sprints/TASKS_SPRINT3.md`)
*   **Status**: Approved (Morpheus plan review) — Phase 1 in progress
*   **Commits**: one local commit per phase after Morpheus's review (`Phase <N>: ...`); publishing only via `bobp make push` when the owner asks (SDLC §6). No back-compat (owner rule).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` present; `sprint-4` cut from `main` (a3f7633). No Tank Phase 0: ARCH §7 adds no dependency, language or make target. The `eslint.config.js` browser-globals block is Tank's, in Phase 3. (*Owner: Mouse*)

---

## Sprint Execution Phases

### Phase 1: The log tells the whole story — UND-13
*Phase goal: every run's stdout and log start with a `start` line and carry `state` lines, idle looks folded; step and final lines unchanged.*
- [x] **Task 1.1:** `src/watch/turnGraph.mjs` label function (shared); `seat.mjs` XState `inspect` → changes, idle-look folding, `drainChanges()`; `src/stream.mjs` (`emit` to stdout + log + listeners); `run.mjs` writes `start`, flushes state lines after looks and steps. Tests: folding (idle looks counted, a moving look listed), labels, run lines order, step/final fields unchanged. TDD. (*Owner: Neo | Verification: `bobp make test`; `bobp make lint`*)
- [x] **Task 1.2:** UAT UND-13 AC1–5 (`bobp make test-live` green ×5; each log starts with `start`, ≥1 `state` line per step, an idle wait is one `idle_looks` number) then Morpheus review vs ADR-0014. (*Owner: Trin → Morpheus | Verification: `bobp make test-live` + `bobp make check`; commit `Phase 1`*)

### Phase 2: Graph layout and the watch server — UND-14 (server side)
*Phase goal: the statechart becomes SVG geometry, and a token-guarded local server streams a run's events over SSE.*
- [x] **Task 2.1:** `src/watch/turnGraph.mjs` (`turn:` → nodes/edges, all five examples), `src/watch/layout.mjs` (ranked columns, back-edge arcs, geometry); `src/watch/server.mjs` (127.0.0.1, token path, static files, SSE history-then-live with `end`, busy port → `UsageError`, 404s). Tests over real HTTP on a free port. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 2.2:** UAT (graph of each example has every state and transition; SSE late join gets history; wrong token 404; busy port refused) then Morpheus review. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 2`*)

### Phase 3: The live page and `run --watch` — UND-14
*Phase goal: `run <sketch> --watch` serves a page that draws the diagram, moves the highlight, and lists decisions live, for all four targets.*
- [x] **Task 3.1:** `src/watch/page.html|page.mjs|page.css` (SVG diagram, highlight + last transition, status, decision feed: options, pick + confidence, off-list, MCP args, answer; ended state; no reconnect loop); `cli.mjs` `--watch [--port N]`; `run.mjs` starts the server before the target and prints the URL. (*Owner: Neo | Verification: `bobp make test`; manual page check*)
- [x] **Task 3.2:** `eslint.config.js` browser-globals block for `src/watch/page.mjs`. (*Owner: Tank | Verification: `bobp make lint` exit 0*)
- [x] **Task 3.3:** UAT UND-14 AC1–9 live: drive the page with Playwright's Chromium during `run examples/cli --watch` and `examples/mcp --watch` (highlight moves ≤1 s, feed rows, reload mid-run, ended text); `--watch` output identical to a plain run; then Morpheus review. (*Owner: Trin → Morpheus | Verification: live + `bobp make check`; commit `Phase 3`*)

### Phase 4: Pause and step — UND-15
*Phase goal: the page pauses a live run before its next move, steps it one move at a time, resumes it; no Jev call while paused.*
- [x] **Task 4.1:** `src/watch/gate.mjs`; run loop `beforeMove()` before `takeStep`, idle limits minus `pausedMs()`, Ctrl-C releases; `POST /control`; page controls (enabled per state, disabled after the end); `--pause`; `--pause`/`--port` without `--watch` refused. Tests: gate unit, run with a gate (no Jev call while paused, 15 s paused not stalled, Ctrl-C while paused → interrupted). (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 4.2:** UAT UND-15 AC1–6 live (`run examples/http --watch --pause`, step ×2, resume; pause 15 s; Ctrl-C while paused) then Morpheus review. (*Owner: Trin → Morpheus | Verification: live + `bobp make check`; commit `Phase 4`*)

### Phase 5: Replay — UND-16
*Phase goal: `understudy watch <log>` replays a finished run on the same page from the log alone.*
- [ ] **Task 5.1:** `src/watch/replay.mjs` (read + check: start line, JSON per line, missing final), `cli.mjs` `watch <log> [--port N]`, page replay mode (play / pause / step back / step forward / click a step; ended or "log ends without a final line"). Tests: reader refusals, replay served. (*Owner: Neo | Verification: `bobp make test`*)
- [ ] **Task 5.2:** UAT UND-16 AC1–5 (replay each example's live log in Chromium; click step 2; a sprint 3 log refused; Ctrl-C exit 0) then Morpheus review. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 5`*)

### Phase 6: Docs — UND-17
*Phase goal: the guides show how to watch, replay and step, with a real screenshot.*
- [ ] **Task 6.1:** USER_GUIDE "Watch a run", SKETCHES §7 log lines, README opening + screenshot (`docs/images/watch.png` from a real run, taken with Playwright), ADR-0014..0016 (Oracle). (*Owner: Neo + Oracle | Verification: every documented command runs*)
- [ ] **Task 6.2:** UAT cold read then Morpheus review. (*Owner: Trin → Morpheus | Verification: inspection; commit `Phase 6`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Verification: `bobp make distclean && bobp make install && bobp make check`*)
- [ ] **Task C.2:** Groom, lessons, UAT plan `docs/sprints/UAT_PLAN_SPRINT4.md`, chat report `SPRINT_4`. (*Owner: Oracle*)
- [ ] **Task C.3:** End-to-end user test vs the UAT plan. (*Owner: Smith*)
- [ ] **Task C.4:** Retro → backlog. (*Owner: All*)
- [ ] **Task C.5:** Launch; merge / push / version only when the owner says. (*Owner: Cypher*)
