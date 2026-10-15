# Sprint 1 Task Board: MVP first run — an understudy plays a CLI app and a web page

*   **Goal**: `understudy run examples/cli` and `understudy run examples/web` each play a real app to its end state with live Jev, from parts written in the same YAML format. Broken parts and a missing key are refused before anything starts.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 13 (UND-1 5, UND-2 3, UND-3 2, UND-4 1, UND-5 2)
*   **Branch**: `sprint-1`
*   **Stories / Arch**: `docs/sprints/USER_STORIES_SPRINT1.md`, `docs/sprints/ARCH_SPRINT1.md`
*   **Status**: Plan approved (Morpheus 3a) — executing
*   **Commits**: one per phase, after Morpheus's review passes (`Phase <N>: <summary>`), never pushed (SDLC §6).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Verification: `test -f docs/SDLC.md`* — present, verified 2026-10-15, branch/commit rules added)

---

## Sprint Execution Phases

### Phase 0: Build environment changes flagged by Morpheus (ARCH §7) — Mechanism class
*Phase goal: the make targets the sprint needs exist before any Neo phase.*
- [x] **Task 0.2:** Add make targets `run` (`node bin/understudy.mjs $(ARGS)`, one-line hint while `bin/understudy.mjs` is missing), `install-browser` (`npx playwright install chromium`, network), `test-live` (runs `understudy run` on every `examples/*/` with `--steps 20`; passes trivially with no examples); update `docs/SDLC.md` §3/§5/§9 (second network target, browser outside the project, `make test` never calls Jev/Chromium). (*Owner: Tank | Verification: `bobp make help` lists run/install-browser/test-live; `bobp make check` exit 0*)

### Phase 1: Generic vocabulary (ARCH §5 "Library changes", ADR-U3) — UND-1/UND-2 foundation
*Phase goal: the moved core speaks "app/target/observe", not "game/peer/table"; every existing test still passes.*
- [x] **Task 1.1:** Rename in `src/library.mjs`, `src/seat.mjs`, `src/machine.mjs` and their tests: `services.peer`→`services.target`, `services.game`→`services.app`, event `TABLE`→`OBSERVE`, guards `table_changed`→`changed`, `quiet_table`→`quiet`, actor `ask_table`→`ask`, `view.lastTouch.seq`→`view.seq`; add generic `look` actor + `phase` guard (from `adapter.app.phase`), and the off-list re-ask in `play` (ADR-U4, record `offList`/`answer`, `RunError` on the second). TDD: new tests for `look`, `phase`, off-list once/twice. (*Owner: Neo | Verification: `bobp make test` fail 0; `bobp make lint` exit 0*)
- [x] **Task 1.2:** UAT phase 1: renamed names appear in `genericLibrary({})` keys; off-list tests cover "nothing sent to the target". (*Owner: Trin | Verification: `bobp make test && bobp make lint`*)
- [x] **Task 1.3:** Review against ARCH §5 and ADR-U3/U4. (*Owner: Morpheus | Verification: code review; commit `Phase 1`*)

### Phase 2: The `understudy` command, key check, library listing — UND-4, UND-5 AC3
*Phase goal: `understudy` exists with `run|check|library`, exit codes 0/1/2, and refuses `run` without a key.*
- [x] **Task 2.1:** `bin/understudy.mjs` + `bin` in `package.json`: argv parsing (`run <dir> [--steps N]`, `check <dir>`, `library [<dir>]`), `UsageError`→exit 2 with `understudy: <message>` and no stack; `run` with `TYPESAFE_API_KEY` unset/blank prints `understudy run needs a TypeSafe key: set TYPESAFE_API_KEY` and exits 2; `library` prints the grouped listing (ARCH §5 CLI output). Tests spawn the CLI with a clean env. (*Owner: Neo | Verification: `bobp make test`; `env -u TYPESAFE_API_KEY bobp make run ARGS="run examples/cli"` → exit 2 with that message*)
- [x] **Task 2.2:** UAT UND-4 AC1–2, UND-5 AC3; bad `--steps 0` → exit 2 naming the flag. (*Owner: Trin | Verification: `bobp make test && bobp make lint`*)
- [x] **Task 2.3:** Review (exit-code consistency ADR-U5). (*Owner: Morpheus | Verification: code review; commit `Phase 2`*)

### Phase 3: Part loader and `understudy check` — UND-3
*Phase goal: every mistake in a part is refused at load, before any app starts, with file, path, bad name and nearest name.*
- [ ] **Task 3.1:** `src/part.mjs`: load `<dir>/adapter.mjs` (default export shape check) and `<dir>/part/turn.yaml` + `questions.yaml`; questions: known `type`, prose literal check naming the question; turn file via `parseTurn` with generic + adapter library; `check` prints `<dir>: part OK - N states, M questions, adapter <name> (<kind>)`. Fixture parts under `tests/fixtures/parts/` (good, unknown guard, unknown actor, literal in question, bad YAML). (*Owner: Neo | Verification: `bobp make test`; `bobp make run ARGS="check tests/fixtures/parts/good"` exit 0*)
- [ ] **Task 3.2:** UAT UND-3 AC1–4: each fixture's exact message, exit 2, no stack trace, no key needed, nothing started. (*Owner: Trin | Verification: `bobp make test && bobp make lint`*)
- [ ] **Task 3.3:** Review. (*Owner: Morpheus | Verification: code review; commit `Phase 3`*)

### Phase 4: The run loop — UND-1 AC2–5 (with test doubles)
*Phase goal: `run` plays any target to its end state with a step cap, first-move timeout, unexpected-exit stop and JSON step log — proven with a fake target and a judge double.*
- [ ] **Task 4.1:** `src/run.mjs` from `seed/recard/tools/jev/runner.mjs` (`playSeat`, `run(dir, { steps, makeJudge, makeTarget })`): key check → load part → start target → seat loop; step cap (default 50) message; 10 s first-move timeout; process-exit check; Jev error wrap; SIGINT→`QUIT`; stdout JSON + stderr summary + `build/runs/<name>/<ts>.jsonl`, first stderr line names the log, final line with `outcome`; target closed in `finally`. Delete `seed/recard/tools/jev/runner.mjs` and `seed/recard/tools/botRequests.mjs`. (*Owner: Neo | Verification: `bobp make test` (tests: done, step-cap, off-list twice, app exited, no first move, Jev error) fail 0*)
- [ ] **Task 4.2:** UAT UND-1 AC2–5 against the fakes: log file lines == stdout lines; final line present on every outcome. (*Owner: Trin | Verification: `bobp make test && bobp make lint`*)
- [ ] **Task 4.3:** Review against ARCH §4 sequence and §6 failure table. (*Owner: Morpheus | Verification: code review; commit `Phase 4`*)

### Phase 5: Process target and the CLI example — UND-1 AC1, live
*Phase goal: a real CLI program is played to its end state by live Jev.*
- [ ] **Task 5.1:** `src/targets/process.mjs` (spawn, buffered lines + `seq`, `act({input})`, `exited`, `describe`, `close` via `waitUntilDead`); `examples/cli/`: `app.mjs` (tiny interactive program with a few prompts and an end state), `adapter.mjs` (<150 lines), `part/turn.yaml`, `part/questions.yaml`; add `@typesafe-ai/sdk ^0.6.0` (SDLC §4). Unit tests for the target against a fixture program. (*Owner: Neo | Verification: `bobp make test`; `bobp make run ARGS="check examples/cli"` exit 0*)
- [ ] **Task 5.2:** UAT UND-1 AC1–4 live: `bobp make run ARGS="run examples/cli --steps 20"` exit 0, `outcome: done`; kill the app mid-run → exit 1 naming the program + code. (*Owner: Trin | Verification: live run (owner-approved, capped) + `bobp make test && bobp make lint`*)
- [ ] **Task 5.3:** Review. (*Owner: Morpheus | Verification: code review; commit `Phase 5`*)

### Phase 6: Page target and the web example — UND-2
*Phase goal: the same kind of part plays a web page in headless Chromium.*
- [ ] **Task 6.1:** `src/targets/page.mjs` from `seed/recard/tests/harness/multiplayer.mjs` (`startStaticServer(root)`, `launchChromium`, hook-driven `view/act/talk/say`, `describe`=URL, Chromium-missing → `UsageError` with the install hint); `examples/web/` (`index.html`, `app.js` exposing `window.__understudy`, `adapter.mjs` <150 lines, `part/`); add `playwright ^1.62.1`. Delete `seed/recard/tests/harness/multiplayer.mjs`. (*Owner: Neo | Verification: `bobp make test` (server traversal 404, hook-missing timeout) fail 0*)
- [ ] **Task 6.2:** UAT UND-2 AC1–6: live `run examples/web --steps 20` exit 0; parts name no transport (grep); no `--headed`; no Chromium → exit 2 + hint (`PLAYWRIGHT_BROWSERS_PATH=/nonexistent`); no browser/server process left after any outcome. (*Owner: Trin | Verification: live run + `bobp make test-live` + `bobp make check`*)
- [ ] **Task 6.3:** Review. (*Owner: Morpheus | Verification: code review; commit `Phase 6`*)

### Phase 7: Adapter documentation — UND-5 AC1–2
*Phase goal: a developer can wire up a new app from one document and two examples.*
- [ ] **Task 7.1:** `docs/ADAPTERS.md`: adapter shape (target kinds, `app.phase/project/options/act`, optional `library`), target action shapes, part files and events, step log fields, exit codes; references both examples. (*Owner: Neo | Verification: `wc -l examples/*/adapter.mjs` each < 150; every name in the doc exists (`bobp make run ARGS="library"`)*)
- [ ] **Task 7.2:** UAT: follow the doc cold to answer "how do I add an HTTP-ish target / my own guard" with no source reading. (*Owner: Trin | Verification: inspection checklist in UAT plan*)
- [ ] **Task 7.3:** Review. (*Owner: Morpheus | Verification: code review; commit `Phase 7`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Verification: `bobp make distclean && bobp make install && bobp make check`; SDLC §10 list*)
- [ ] **Task C.2:** Document grooming, ADRs U1–U6 recorded, lessons, chat report. (*Owner: Oracle | Verification: `bobp chat-report --moniker SPRINT_1`*)
- [ ] **Task C.3:** End-to-end user usability testing against `docs/sprints/UAT_PLAN_SPRINT1.md` & lesson review. (*Owner: Smith | Verification: `bobp chat "*user approve"`*)
- [ ] **Task C.4:** Sprint retrospective & backlog grooming. (*Owner: All personas | Verification: Retros posted in CHAT.md*)
- [ ] **Task C.5:** Sprint launch; merge `sprint-1` → `main` and tag only when the owner says so (SDLC §6). (*Owner: Cypher | Verification: `bobp chat "*pm launch"`*)
