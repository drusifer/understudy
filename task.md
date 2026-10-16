# Sprint 6 Task Board: The dashboard, with atmosphere

*   **Goal**: `understudy dashboard <folder>` - a steampunk console: sketch rack, mood dial, faders, switches, Play, a state tube with power flowing by weight, a printer log; access panels save edits to the sketch; POWER off/on resets to factory defaults.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 25 (UND-27 3, UND-28 5, UND-29 3, UND-30 5, UND-31 2, UND-32 5, UND-33 2)
*   **Branch**: `sprint-6`
*   **Stories / Arch / Design**: `docs/sprints/USER_STORIES_SPRINT6.md`, `docs/sprints/ARCH_SPRINT6.md`, `docs/design/DASHBOARD.md` (sprint 5 board: `docs/sprints/TASKS_SPRINT5.md`)
*   **Status**: In progress - Phase 6
*   **Commits**: one local commit per phase after Morpheus's review (`Phase <N>: ...`); publishing only via `bobp make push` when the owner asks (SDLC §6).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` present; `sprint-6` cut from `main` (965bade). No Tank Phase 0: new deps are routine (§4); the eslint browser-globals line is Tank's, in Phase 4. (*Owner: Mouse*)

---

## Sprint Execution Phases

### Phase 1: Switch inputs and `when:` - UND-28 AC3-4
- [x] **Task 1.1:** `inputs.mjs` switch kind (`on/off/true/false`), `engine.gate` skips a test whose `when` switch is off, `check` refuses `when` naming a non-switch; app passes inputs to gates. TDD. (*Owner: Neo | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 1.2:** UAT + review vs ADR-0026. (*Owner: Trin → Morpheus | commit `Phase 1`*)

### Phase 2: The dashboard server and the rack - UND-27
- [x] **Task 2.1:** `src/dashboard/server.mjs` (token path, static, SSE, API skeleton, 16 KB bodies), `rack.mjs` (list, describe: inputs, factors, graph, check problem), `cli.mjs dashboard <folder> [--port] [--host]`; tests over real HTTP. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 2.2:** UAT UND-27 AC1-5 + review vs ADR-0023. (*Owner: Trin → Morpheus | commit `Phase 2`*)

### Phase 3: Play and Stop - UND-29 (server side)
- [x] **Task 3.1:** `runner.mjs` (one run, `makeWatch` relay, SIGINT stop, stderr capture, refusals, `dashboard` lines), `api/play`, `api/stop`; tests with a Jev double on `examples/evening`. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 3.2:** UAT UND-29 AC1-5 (server) + review. (*Owner: Trin → Morpheus | commit `Phase 3`*)

### Phase 4: The console's controls - UND-28, UND-29 (page)
- [x] **Task 4.1:** `page.html/mjs/css` from the approved design: rack, mood dial, faders, switches, Play/STOP, READY, POWER (dim); fonts from `@fontsource/*`; keyboard + accessible names. (*Owner: Neo | Verification: `bobp make test`, manual page check*)
- [x] **Task 4.2:** eslint browser-globals for `src/dashboard/page.mjs`. (*Owner: Tank | Verification: `bobp make lint`*)
- [x] **Task 4.3:** UAT + review. (*Owner: Trin → Morpheus | commit `Phase 4`*)

### Phase 5: The state tube and the printer - UND-30, UND-31
- [x] **Task 5.1:** `tube.mjs` (circle layout, finals inside, labels, ring arcs, blend), live highlight + flowing edge; printer feed (steps, held, removed, Jev, table with `11`, outcome). Unit tests for `tube.mjs`. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 5.2:** UAT UND-30/31 + review. (*Owner: Trin → Morpheus | commit `Phase 5`*)

### Phase 6: Access panels, saving, factory reset - UND-32
- [ ] **Task 6.1:** `settings.mjs` (allow-listed paths, YAML Document `setIn`, validate on a temp copy, `.factory/` copy, restore on power on), `api/edit`, `api/power`; panels on the page; `.gitignore` `.factory/`. Tests: comments kept, invalid refused, reset restores. (*Owner: Neo | Verification: `bobp make test`*)
- [ ] **Task 6.2:** UAT UND-32 + review vs ADR-0024/0025. (*Owner: Trin → Morpheus | commit `Phase 6`*)

### Phase 7: Docs, browser tests, the evening's switch - UND-33
- [ ] **Task 7.1:** `examples/evening` `together` switch; USER_GUIDE "The dashboard" + screenshot; SKETCHES switches/`when:`. (*Owner: Neo, Oracle*)
- [ ] **Task 7.2:** browser test driving the dashboard with a Jev double. (*Owner: Trin | Verification: `bobp make test-browser`*)
- [ ] **Task 7.3:** review. (*Owner: Morpheus | commit `Phase 7`*)

---

## Sprint Close
- [ ] **Task C.1:** `*devops sdlc-check`. (*Owner: Tank*)
- [ ] **Task C.2:** `*ora groom` - ADR-0023..0026, lessons, changelog, chat report. (*Owner: Oracle*)
- [ ] **Task C.3:** `*user test` against `docs/sprints/UAT_PLAN_SPRINT6.md`. (*Owner: Smith*)
- [ ] **Task C.4:** retro, `*pm launch sprint-6`. (*Owner: All → Cypher*)
