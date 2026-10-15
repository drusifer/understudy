# Sprint 2 Task Board: Play a JSON API, and any web page without changing it

*   **Goal**: `understudy run examples/http` plays a JSON API, and `understudy run examples/web` plays an unmodified page through its accessibility snapshot with a name-and-target adapter. Every target stops cleanly when a run stalls.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 12 (UND-6 5, UND-7 5, UND-8 2)
*   **Branch**: `sprint-2`
*   **Stories / Arch**: `docs/sprints/USER_STORIES_SPRINT2.md`, `docs/sprints/ARCH_SPRINT2.md` (sprint 1 board: `docs/sprints/TASKS_SPRINT1.md`)
*   **Status**: Plan approved (Morpheus 3a) — executing
*   **Commits**: one local commit per phase after Morpheus's review (`Phase <N>: ...`); publishing only via `bobp make push` when the owner asks (SDLC §6). No back-compat (owner rule).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` present (verified 2026-10-15). No Tank Phase 0: ARCH §7 adds no dependency, language or make target. (*Owner: Mouse*)

---

## Sprint Execution Phases

### Phase 1: Run-loop and loader groundwork (ADR-0010, ARCH §3)
*Phase goal: every target stops cleanly on a stall; targets are checked field by field; act results reach the log; program start/stop is shared.*
- [x] **Task 1.1:** `run.mjs` stall rule (`stallMs` 10 s after the first move, outcome `stalled`, message with the `showing` hint); `part.mjs` per-kind target field check (unknown field → `UsageError` naming known fields); `library.play` records the last non-empty act result as `response`; `look` also outputs `view`; new guard `showing { text }`; extract `src/targets/program.mjs` from `process.mjs`. TDD. (*Owner: Neo | Verification: `bobp make test` fail 0 (new tests: stalled, unknown field, response, showing); `bobp make lint` exit 0*)
- [x] **Task 1.2:** UAT: stall test names last state + hint; `check` on an adapter with `target.hook` → exit 2 naming known fields. (*Owner: Trin | Verification: `bobp make test && bobp make lint`*)
- [x] **Task 1.3:** Review vs ARCH §4 stall rule / §5 fields. (*Owner: Morpheus | Verification: review; commit `Phase 1`*)

### Phase 2: HTTP target and the vending-machine example — UND-6
*Phase goal: a JSON API is played to its end state, started or attached, with error statuses logged.*
- [x] **Task 2.1:** `src/targets/http.mjs` (free port + `{port}`, start via `program.mjs`, ready-wait 10 s, GET-state view, request act returning `{ status }`, connection-lost `RunError`, attach mode); `examples/http/` (`server.mjs`, adapter < 150 lines, part with no transport words). Tests against an in-process `node:http` server + the example end to end with a Jev double. (*Owner: Neo | Verification: `bobp make test`; `bobp make run ARGS="check examples/http"` exit 0*)
- [x] **Task 2.2:** UAT UND-6 AC1–9: live `bobp make run ARGS="run examples/http --steps 20"` exit 0; attach mode against a hand-started server (left running); error status in a step line; kill server mid-run → exit 1. (*Owner: Trin | Verification: live run (capped) + `bobp make test && bobp make lint`*)
- [x] **Task 2.3:** Review vs ADR-0008. (*Owner: Morpheus | Verification: review; commit `Phase 2`*)

### Phase 3: Hookless page target — UND-7 AC3–6
*Phase goal: the page target reads the accessibility snapshot and acts by role + name; all hook code is gone.*
- [x] **Task 3.1:** `src/targets/aria.mjs` (snapshot text → title/text/controls; hidden absent, disabled dropped, options carry their list); `page.mjs`: view from `ariaSnapshot()`, act by `getByRole` (click/check/selectOption, 5 s, "no longer on the page" `RunError`), hook wait and `callHook` deleted. Tests: aria parser on recorded snapshots; actions on a fake page. (*Owner: Neo | Verification: `bobp make test`; `grep -rn __understudy src` empty*)
- [x] **Task 3.2:** UAT: parser cases (disabled, hidden, combobox options, links); no hook code left. (*Owner: Trin | Verification: `bobp make test && bobp make lint`*)
- [x] **Task 3.3:** Review vs ADR-0007. (*Owner: Morpheus | Verification: review; commit `Phase 3`*)

### Phase 4: Generic page app and the unmodified web example — UND-7 AC1–2, 7–8
*Phase goal: `examples/web` is a plain page with a name-and-target adapter, played live to "Welcome aboard".*
- [ ] **Task 4.1:** `src/apps/page.mjs` (phase/project/options/act per ARCH §4); `part.mjs` fills it in for a `page` adapter without `app`, `check` says `(page, generic page app)`; `examples/web`: hook removed from `app.js`, adapter = name + target (≤ 10 lines), part ends with `showing`. (*Owner: Neo | Verification: `bobp make test`; `bobp make run ARGS="check examples/web"` exit 0*)
- [ ] **Task 4.2:** UAT UND-7 AC1–8 live: `run examples/web --steps 20` exit 0 with `button:...` ids; page with `window.__understudy` played identically; remove the `showing` guard → stalled with the hint; no Chromium left running; `bobp make test-live` green (3 examples). (*Owner: Trin | Verification: live runs + `bobp make check`*)
- [ ] **Task 4.3:** Review. (*Owner: Morpheus | Verification: review; commit `Phase 4`*)

### Phase 5: Docs — UND-8
*Phase goal: the docs describe three targets and hookless pages only.*
- [ ] **Task 5.1:** `docs/ADAPTERS.md`, `docs/USER_GUIDE.md`, `docs/WALKTHROUGH.md` (HTTP + hookless web with real runs), `README.md`; ADR-0007..0010 in `docs/DECISIONS.md`, ADR-0002 marked superseded. (*Owner: Neo | Verification: `grep -rn "__understudy" docs README.md examples src` empty*)
- [ ] **Task 5.2:** UAT: cold-read "wire up my API" and "play my page" from the docs alone; every command in the docs runs. (*Owner: Trin | Verification: inspection + `bobp make run` of each documented command*)
- [ ] **Task 5.3:** Review. (*Owner: Morpheus | Verification: review; commit `Phase 5`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Verification: `bobp make distclean && bobp make install && bobp make check`; SDLC §10*)
- [ ] **Task C.2:** Groom, lessons, chat report `SPRINT_2`. (*Owner: Oracle | Verification: `bobp chat-report --moniker SPRINT_2`*)
- [ ] **Task C.3:** End-to-end user test vs `docs/sprints/UAT_PLAN_SPRINT2.md`. (*Owner: Smith | Verification: `bobp chat "*user approve"`*)
- [ ] **Task C.4:** Retro → backlog. (*Owner: All | Verification: retros in CHAT.md*)
- [ ] **Task C.5:** Launch; merge to `main` / push / version only when the owner says (SDLC §6–7). (*Owner: Cypher | Verification: `bobp chat "*pm launch"`*)
