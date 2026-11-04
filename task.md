# Sprint 26 Task Board: see and drive the machine

*   **Goal**: The owner can hold a run before its next stage, step it and resume it; replay a finished run's story with play, pause, step, step back and a scrubber; and open any decision to see its options, the rules that removed or held them, the weights and the pick.
*   **Tier**: Tier 1 (Major)
*   **Total Points** (optional): 18
*   **Branch**: `sprint-26` (cut from `main`, which has Sprints 24 and 25)
*   **Status**: Planning — awaiting Morpheus Step 3a Review
*   **Plan**: `docs/sprints/USER_STORIES_SPRINT26.md` (Gate 1 approved), `ARCH_SPRINT26.md` (Gate 2 approved), security design gate: no blocking findings (Phase 2 gets a full review). Decision: `OWNER_DECISIONS_SPRINT22.md` 16.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-03*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. Each phase is one build task followed by its three gates; a phase is not done until Morpheus passes it. Edit files with Edit/Write only (owner rule). Use `ARGS` only with test targets that take a file pattern.

### Phase 1: The runner can be held (UND-83 part 1, 4 pts)
*Phase goal: a control file and the runner's gate; `paused` and `resumed` events.*
- [x] **Task 1.1:** Tests first, then `src/sketch/control.py` (`read_control` fail-open to run, `write_control` atomic, the gate with hold and step by `allow`), the gate called before each top-level stage in `run.py`, `paused` and `resumed` events; a held run makes no Jev request and no stage start; STOP and Ctrl-C end a held run. **L3** (concurrency with the runner; failure cases). (*Owner: Neo | Trace: UND-83 AC3-5, ADR-0058 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 1.2:** UAT with a real sketch and a fake clock: hold before stage 3, step twice, resume; a bad control file runs on; an old log reads as before. **L2**. (*Owner: Trin | Trace: UND-83 AC3-5 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 1.3:** Security quick pass: the control file as a new input to the runner. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 1): ...`*)
- [x] **Task 1.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT26 sections 3-5, ADR-0058 | Verification: result in `agents/CHAT.md`*)

### Phase 2: Drive it from the console and the command line (UND-83 part 2, 4 pts)
*Phase goal: pause, step, resume in the console; `run --watch [--pause]`; a held run reads as paused.*
- [x] **Task 2.1:** Tests first, then `Launcher.control`, `POST /api/pause`, `/api/step`, `/api/resume`, state `paused` in `view.py`, buttons with keyboard names in the page, `run --watch [--pause]` on 127.0.0.1 and the `--pause needs --watch` refusal; docs. **L3** (new control channel; process and thread). (*Owner: Neo | Trace: UND-83 AC1, AC2, AC4, AC6, ADR-0058 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [x] **Task 2.2:** UAT in the console and from the terminal: hold, `paused before <stage>` shown, step, resume, stop; a foreign run refused; no Jev request while held (counted). **L2**. (*Owner: Trin | Trace: UND-83 AC1-6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 2.3:** Security review (full): the POSTs, the run id, the control file path, the in-process server's binding. **L3**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 2): ...`*)
- [x] **Task 2.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT26 sections 3-6 | Verification: result in `agents/CHAT.md`*)

### Phase 3: The run as it was (UND-84 part 1, 3 pts)
*Phase goal: `replay(dir, at)` in Python and its API.*
- [x] **Task 3.1:** Tests first, then `src/dashboard/replay.py` (state, stages, gauges, printed lines, lit state, hold and ending after event N), `GET /api/runs/<id>/replay[?at=N]`, a refused unreadable log; docs. **L2**. (*Owner: Neo | Trace: UND-84 AC1, AC3, AC4, ADR-0059 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 3.2:** UAT on real run folders (the household full run and an evening run): event 0, a middle event, the last event; the last equals the live view; a log with a bad line is refused. **L2**. (*Owner: Trin | Trace: UND-84 AC1, AC3, AC4 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 3.3:** Security quick pass: the log is read-only data; the run id check. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 3): ...`*)
- [x] **Task 3.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT26 section 4, ADR-0059 | Verification: result in `agents/CHAT.md`*)

### Phase 4: Play it back (UND-84 part 2, 2 pts)
*Phase goal: the replay bar in the page.*
- [x] **Task 4.1:** Tests first (browser), then REPLAY on a finished run: play, pause, step, step back, scrubber, "event N of M", keyboard names, themes. **L2**. (*Owner: Neo | Trace: UND-84 AC1, AC2, AC5 | Verification: `bobp make test-browser`, `bobp make lint`*)
- [x] **Task 4.2:** UAT in a real browser in all three themes, light and dark: readable, reachable by keyboard, the diagram follows the cursor. **L2**. (*Owner: Trin | Trace: UND-84 AC1-5 | Verification: UAT verdict and screenshot noted in `agents/CHAT.md`*)
- [x] **Task 4.3:** Security quick pass: page text set as text. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 4): ...`*)
- [x] **Task 4.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT26 section 3 | Verification: result in `agents/CHAT.md`*)

### Phase 5: See the decision (UND-85, 5 pts)
*Phase goal: list a run's decisions, open one, jump to it in a replay.*
- [ ] **Task 5.1:** Tests first, then `decisions(dir)`, `GET /api/runs/<id>/decisions`, the list and panel in the page (options with weight and `removed_by`, blend, pick), the jump from a decision to its event in a replay, a run with none, an incomplete line. **L3**. (*Owner: Neo | Trace: UND-85 AC1-4 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [ ] **Task 5.2:** UAT on a coffee run and an evening run (they decide): every decision opens with its options, rule and pick; the jump lands on the right event; a household run says it has none. **L2**. (*Owner: Trin | Trace: UND-85 AC1-3 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 5.3:** Security quick pass: names from a log shown as text. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 5): ...`*)
- [ ] **Task 5.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT26 sections 4-5 | Verification: result in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make check`, and `docs/SDLC.md` "Last verified" updated*)
- [ ] **Task C.2:** Document grooming, ADR-0058 and ADR-0059, lessons. (*Owner: Oracle | Trace: N/A — closeout | Verification: ADRs in `docs/DECISIONS.md`; groom noted in `agents/CHAT.md`*)
- [ ] **Task C.3:** End-to-end user testing in the console against `docs/sprints/UAT_PLAN_SPRINT26.md`, and lesson review. (*Owner: Smith | Trace: UND-83..85 | Verification: Smith acceptance verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task C.4:** Sprint retrospective and backlog grooming. (*Owner: Mouse | Trace: N/A — closeout | Verification: retros in `docs/sprints/RETRO_SPRINT26.md`, posted in `agents/CHAT.md`*)
- [ ] **Task C.5:** Sprint launch and release announcement; merge `sprint-26` into `main` and push only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch recorded in `agents/CHAT.md`*)
