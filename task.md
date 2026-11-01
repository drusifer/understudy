# Sprint 22 Task Board: the console you can trust, see into, and start runs from

*   **Goal**: The owner can open the console and see at once how a run went, look inside a long run and at Jev's answers, and start, replay or stop a run behind an access secret. Command-line failures are one plain line.
*   **Tier**: Tier 1 (Major)
*   **Total Points** (optional): 29
*   **Branch**: `sprint-22`
*   **Status**: Plan approved by Morpheus (Step 3a); Phase 1 in progress
*   **Plan**: `docs/sprints/USER_STORIES_SPRINT22.md` (Gate 1 approved), `ARCH_SPRINT22.md` (Gate 2 approved), security design gate `agents/switch/reviews/2026-11-01-sprint-22-design-gate.md` (no blocking findings; SEC-005 accepted until 2027-01-30). Decisions: `OWNER_DECISIONS_SPRINT22.md`.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; Python-only and `security-scan` rows added 2026-11-01*)

---

## Sprint Execution Phases

Complexity levels follow the definitions in `agents/templates/_template_task.md`. Each phase is one build task followed by its three gates; a phase is not done until Morpheus passes it.

### Phase 1: A run says how it went (UND-76, 5 pts)
*Phase goal: the header, a failure banner, a summary panel and a disconnected marker tell the owner how a run went.*
- [x] **Task 1.1:** Record `outcome`, `with` and `outputs` in `run.json`; state, failure, summary and stalled marker in `describe`; banner, summary panel, "disconnected, retrying" and mobile header in the page; tests first. **L2** (several files in one bounded area; pattern known). (*Owner: Neo | Trace: UND-76 AC1-7 | Verification: `bobp make test` and `bobp make lint`*)
- [x] **Task 1.2:** UAT in a real browser: running, done, failed and unreadable runs; server stopped and restarted; 390 px. **L2**. (*Owner: Trin | Trace: UND-76 AC1-7 | Verification: UAT verdict and screenshots noted in `agents/CHAT.md` and `docs/sprints/UAT_PLAN_SPRINT22.md`*)
- [x] **Task 1.3:** Security quick pass: the new `run.json` fields (`with` values are paths as typed). **L1**. (*Owner: Switch | Trace: SEC-004 | Verification: `security gate (phase 1): ...` in `agents/CHAT.md`*)
- [x] **Task 1.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT22 section 3 | Verification: result in `agents/CHAT.md`*)

### Phase 2: See inside a run (UND-77, 5 pts)
*Phase goal: nested stages as groups with progress, honest gauges, rack badges.*
- [ ] **Task 2.1:** Groups and iteration counts from stage names (decision D-S22-1); real-fraction gauges only (D-S22-2); rack badges and grouping by sketch; tests first. **L2**. (*Owner: Neo | Trace: UND-77 AC1-5 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 2.2:** UAT on the real household run (937 stage events): groups, in-progress lamp on a growing run, a run with no nested stages. **L2**. (*Owner: Trin | Trace: UND-77 AC1-5 | Verification: UAT verdict in `agents/CHAT.md` and the UAT plan*)
- [ ] **Task 2.3:** Security quick pass: no new input or surface. **L1**. (*Owner: Switch | Trace: N/A — quick pass | Verification: `security gate (phase 2): ...` in `agents/CHAT.md`*)
- [ ] **Task 2.4:** Code review. **L1**. (*Owner: Morpheus | Trace: D-S22-1, D-S22-2 | Verification: result in `agents/CHAT.md`*)

### Phase 3: Find a line in the log (UND-88, 3 pts)
*Phase goal: filter and jump in the printer.*
- [ ] **Task 3.1:** Text, failures-only and stage filters; jumps to start, first failure, end; empty-result message; live lines obey the filter; tests for the server's failure index first. **L2**. (*Owner: Neo | Trace: UND-88 AC1-4 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 3.2:** UAT on 1,876 lines and on a failed run. **L1**. (*Owner: Trin | Trace: UND-88 AC1-4 | Verification: UAT verdict in `agents/CHAT.md`*)
- [ ] **Task 3.3:** Security quick pass: filters are client-side text, written with `textContent`. **L1**. (*Owner: Switch | Trace: N/A — quick pass | Verification: `security gate (phase 3): ...` in `agents/CHAT.md`*)
- [ ] **Task 3.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT22 section 3 | Verification: result in `agents/CHAT.md`*)

### Phase 4: See Jev's judgements (UND-78, 5 pts)
*Phase goal: a list of Jev reads from the capture files, flagged by confidence, with two real gauges.*
- [ ] **Task 4.1:** `jev_reads` over `CaptureStore` (levels, probabilities, top, margin, flag below 0.7, missing and pruned notes); the list in the page; confidence and asked-vs-reused gauges; tests first against the committed coffee capture. **L2**. (*Owner: Neo | Trace: UND-78 AC1-6 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 4.2:** UAT on a replayed run, a live-captured household run (counts only, no private values printed), a run with no Jev and a run whose captures were pruned. **L2**. (*Owner: Trin | Trace: UND-78 AC1-6 | Verification: UAT verdict in `agents/CHAT.md`*)
- [ ] **Task 4.3:** Security review: the list reads capture files from a run id taken from the URL. **L2**. (*Owner: Switch | Trace: SEC-006 (id check) | Verification: `security gate (phase 4): ...` in `agents/CHAT.md`*)
- [ ] **Task 4.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT22 section 4 | Verification: result in `agents/CHAT.md`*)

### Phase 5: Start, replay and stop: the server side (UND-79 part 1, 5 pts)
*Phase goal: the `Launcher`, the secret and the POST routes, tested without a browser.*
- [ ] **Task 5.1:** `runs.py` `Launcher` (sketch list with check results, start, stop, replay ids, one run per sketch, child cap 4, stderr tail, `stopped` marking); POST routes with the secret check, `Origin` check, 8 KB cap and per-address pause; root check on file-valued `--with`; `--sketches` and the printed secret in `cli.py`; tests first, including every refusal in `ARCH_SPRINT22` section 6. **L3** (new process boundary, security design, several components). (*Owner: Neo | Trace: UND-79 AC1-3, 5-6, 8-10; SEC-005, SEC-006 | Verification: `bobp make test`, `bobp make lint`, `bobp make security-scan`*)
- [ ] **Task 5.2:** Verify the refusals against a running console with `curl`: no secret, wrong secret, sketch outside the folder, `../`, symlink out, extra argument, second Play, fifth child, foreign `Origin`, oversize body. **L3**. (*Owner: Trin | Trace: UND-79 AC8-10 | Verification: UAT verdict with the request list in `agents/CHAT.md`*)
- [ ] **Task 5.3:** Security review of the diff against the design gate's threat model. **L3**. (*Owner: Switch | Trace: SEC-005, SEC-006, UND-79 AC8-9 | Verification: `security gate (phase 5): ...` in `agents/CHAT.md` and a review file*)
- [ ] **Task 5.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ADR-0049, ARCH_SPRINT22 sections 3-6 | Verification: result in `agents/CHAT.md`; ADR-0049 recorded*)

### Phase 6: Start, replay and stop: the page (UND-79 part 2, 3 pts)
*Phase goal: the sketch list, the form, Play, Replay, Stop and the secret box.*
- [ ] **Task 6.1:** Sketch list with greyed-out failures, `--with` fields, Play, Replay, Stop, "enter access secret" box kept in `sessionStorage`, controls off with a reason without the secret, can't-start message, controls unlock when a run ends; tests for any new server answers first. **L2**. (*Owner: Neo | Trace: UND-79 AC1-2, 4-7, 10 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 6.2:** UAT by hand in a real browser: start the coffee sketch live-free (replay), start the household with the real files (counts only), stop a run, wrong secret, phone width. **L3**. (*Owner: Trin | Trace: UND-79 AC1-10 | Verification: UAT verdict in `agents/CHAT.md` and the UAT plan*)
- [ ] **Task 6.3:** Security review: where the page keeps and sends the secret; no secret in URL or log. **L2**. (*Owner: Switch | Trace: UND-79 AC8; SEC-005 | Verification: `security gate (phase 6): ...` in `agents/CHAT.md`*)
- [ ] **Task 6.4:** Code review. **L1**. (*Owner: Morpheus | Trace: UND-79 | Verification: result in `agents/CHAT.md`*)

### Phase 7: The promises (UND-80, 3 pts)
*Phase goal: one-line command failures, `understudy runs`, keyboard and contrast, a written browser check.*
- [ ] **Task 7.0:** Approve how any browser-check tool is installed and run, and record it in `docs/SDLC.md` before it is used (UND-80 AC7). **L1**. (*Owner: Tank | Trace: UND-80 AC7 | Verification: `docs/SDLC.md` change and `bobp make install`*)
- [ ] **Task 7.1:** Busy-port and missing-folder messages, `--help` text with examples, run id printed at the end of `run`, `understudy runs`; focus outlines and accessible names; contrast fixes per theme; tests first for the CLI. **L2**. (*Owner: Neo | Trace: UND-80 AC1-5 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 7.2:** Write and run the browser check (rack, live follow, failed banner, start and stop) and the keyboard and contrast pass; record them in the UAT plan. **L2**. (*Owner: Trin | Trace: UND-80 AC4-6 | Verification: the UAT plan section and its results*)
- [ ] **Task 7.3:** Security quick pass: no new surface. **L1**. (*Owner: Switch | Trace: N/A — quick pass | Verification: `security gate (phase 7): ...` in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check, and `bobp make security-scan` clean. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make distclean && bobp make install && bobp make check` and `bobp make security-scan`*)
- [ ] **Task C.2:** Document grooming (PRD statuses, ARCH.md, README, USER_GUIDE, CHANGELOG, ADR-0049), lessons, chat report. (*Owner: Oracle | Trace: N/A — closeout | Verification: `bobp chat-report --moniker SPRINT_22 --summary "..."`*)
- [ ] **Task C.3:** End-to-end user test against `UAT_PLAN_SPRINT22.md` and the UAT check; lesson review. (*Owner: Smith | Trace: UND-76 to UND-80, UND-88 | Verification: Smith verdict in `agents/CHAT.md`*)
- [ ] **Task C.4:** Retrospective and backlog grooming. (*Owner: Mouse | Trace: N/A — closeout | Verification: retros posted in `agents/CHAT.md`*)
- [ ] **Task C.5:** Launch decision. (*Owner: Cypher | Trace: N/A — release decision | Verification: decision recorded in `agents/CHAT.md`*)
