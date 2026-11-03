# Sprint 24 Task Board: what the money goes on, typed inputs, and the statechart you can see

*   **Goal**: The owner can see what the household money goes on (card payments no longer count as income; a ranked spending list in the run and the console), set a sketch's values with typed controls, and follow a run on a drawn statechart.
*   **Tier**: Tier 1 (Major)
*   **Total Points** (optional): 27
*   **Branch**: `sprint-24`
*   **Status**: Planning — awaiting Morpheus Step 3a Review
*   **Plan**: `docs/sprints/USER_STORIES_SPRINT24.md` (Gate 1 approved after one rejection), `ARCH_SPRINT24.md` (Gate 2 approved), security design gate: no blocking findings. Decisions: `OWNER_DECISIONS_SPRINT22.md` 4 and 9. Baseline: `data/Transactions_2026-11-02T19-14-07.csv`.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-02*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. Each phase is one build task followed by its three gates; a phase is not done until Morpheus passes it. Edit files with Edit/Write only (owner rule). Real-data checks use the baseline file and run live; the Jev answers are cached, so a repeat run costs few requests. Console changes are checked in a real Chromium (`bobp make test-browser`, 63 seconds, not a release gate).

### Phase 1: Card payments and moves between accounts are not spending (UND-93, 3 pts)
*Phase goal: a record is a transfer by label, by link, or both; the summary says which.*
- [x] **Task 1.1:** Tests first, then `labeled` and `standing` in `household.yaml` (label forms and the link make a transfer, nothing else does); `transfer_basis` counts replace `kind_changed_by_category`; update the household tests, `docs/USER_GUIDE.md` and `docs/SKETCHES.md`. **L2** (one sketch, tests and docs; pattern known). (*Owner: Neo | Trace: UND-93 AC1-6 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 1.2:** UAT on the baseline: no labeled or linked record is a purchase, refund or credit; positives outside Ridgewood under $30,000; Ridgewood unchanged. **L2**. (*Owner: Trin | Trace: UND-93 AC4-5 | Verification: UAT verdict and evidence in `agents/CHAT.md` and `docs/sprints/UAT_PLAN_SPRINT24.md`*)
- [x] **Task 1.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 1): ...` in `agents/CHAT.md`*)
- [x] **Task 1.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 sections 3-4, ADR-0052 | Verification: result in `agents/CHAT.md`*)

### Phase 2: Where the money goes (UND-94, 5 pts)
*Phase goal: `spending.jsonl` ranked by category, with shares and a total in the summary.*
- [x] **Task 2.1:** Tests first, then generic `map.share`; the `spend_*` stages and `spending.jsonl`; `spending_total` in `summary.json`; empty file when no spending; docs. **L2**. (*Owner: Neo | Trace: UND-94 AC1-6 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 2.2:** UAT on the baseline: order, shares sum to 100%, amounts sum to `spending_total`, categories from the export first. **L2**. (*Owner: Trin | Trace: UND-94 AC1-6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 2.3:** Security quick pass: category names and totals only. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 2): ...`*)
- [x] **Task 2.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 section 5 | Verification: result in `agents/CHAT.md`*)

### Phase 3: The console shows what the money goes on (UND-95, 3 pts)
*Phase goal: the run summary lists the top ten categories.*
- [x] **Task 3.1:** Tests first, then `spending` in the run's description (top ten, more, problem) and the summary-panel list with its CSS; text via `textContent`. **L2**. (*Owner: Neo | Trace: UND-95 AC1-4 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [x] **Task 3.2:** UAT in a real browser on the real run: ten rows, more count, no list for a run without the file, unreadable file named, 390 px, three themes. **L2**. (*Owner: Trin | Trace: UND-95 AC1-4 | Verification: UAT verdict and screenshots noted in `agents/CHAT.md`*)
- [x] **Task 3.3:** Security quick pass: rendering of run-folder text. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 3): ...`*)
- [x] **Task 3.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 sections 5-6 | Verification: result in `agents/CHAT.md`*)

### Phase 4: Inputs are declared (UND-87 part 1, 4 pts)
*Phase goal: a sketch declares typed inputs; the loader fills defaults and checks limits; the console's start refuses out-of-limit values.*
- [ ] **Task 4.1:** Tests first, then `inputs:` in the schema, model and loader (defaults injected), `check` messages naming the input, `--with` limit checks, `inputs` in `/api/sketches` and server-side value checks; `evening.yaml` declares its inputs and drops repeated defaults; docs. **L3** (schema, loader, CLI and server agree; failure cases). (*Owner: Neo | Trace: UND-87 AC1, AC4-7, ADR-0053 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 4.2:** UAT: each kind declared, each wrong declaration refused naming the input, `--with` out of limits refused, defaults used when left alone, the console refuses a bad posted value. **L3**. (*Owner: Trin | Trace: UND-87 AC1, AC4-6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 4.3:** Security review: values from the browser reach a child process; the checks and the argument list. **L2**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 4): ...`*)
- [ ] **Task 4.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 sections 4-6, ADR-0053 | Verification: result in `agents/CHAT.md`*)

### Phase 5: The right control for each value (UND-87 part 2, 4 pts)
*Phase goal: the console draws a dial, fader, stepper or switch per declared input.*
- [ ] **Task 5.1:** Tests first (browser), then the four controls in `controls.js` and `page.css`: keyboard use, accessible name and value, limits, defaults, undeclared names keep a text box; Play posts every value. **L3** (browser behavior across three themes and keyboard). (*Owner: Neo | Trace: UND-87 AC2-4, AC6 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [ ] **Task 5.2:** UAT in a real browser on `evening`: each control by mouse and keyboard, defaults, limits, a run started with the values, 390 px, three themes. **L3**. (*Owner: Trin | Trace: UND-87 AC2-4, AC6, AC7 | Verification: UAT verdict and screenshots noted in `agents/CHAT.md`*)
- [ ] **Task 5.3:** Security quick pass: values rendered back; no markup from option text. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 5): ...`*)
- [ ] **Task 5.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 sections 3, 5 | Verification: result in `agents/CHAT.md`*)

### Phase 6: The statechart is laid out (UND-82 part 1, 4 pts)
*Phase goal: the server lays the machine out and says which state is lit.*
- [ ] **Task 6.1:** Tests first (no browser), then `src/dashboard/chart.py` (layers, boxes, arrows, labels, no overlaps up to 40 states, back-edges) and `chart` in the run's description (current state, last move, ended, `null` without a story). **L3** (new algorithm, edge cases, interface to the page). (*Owner: Neo | Trace: UND-82 AC1-5, AC7, ADR-0054 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 6.2:** UAT on the real machines (household, evening, coffee) and a generated 40-state machine: layout checks, lit state from a real run's events, a log with no story. **L3**. (*Owner: Trin | Trace: UND-82 AC1-5, AC7 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 6.3:** Security quick pass: hostile state names and guards in JSON. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 6): ...`*)
- [ ] **Task 6.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 sections 3-5, ADR-0054 | Verification: result in `agents/CHAT.md`*)

### Phase 7: See the statechart (UND-82 part 2, 4 pts)
*Phase goal: the page draws the chart, lights the current state and says how the run ended.*
- [ ] **Task 7.1:** Tests first (browser), then the SVG drawing in `page.js` and `page.css`: boxes, double-bordered finals, arrows, guard labels, lit state moving within a second, highlighted move, ending, no-story message, accessible names, a hostile-name test. **L3**. (*Owner: Neo | Trace: UND-82 AC1-6 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [ ] **Task 7.2:** UAT in a real browser on a live run (the light moves) and a finished one, 390 px, three themes, a run with no story. **L3**. (*Owner: Trin | Trace: UND-82 AC1-6 | Verification: UAT verdict and screenshots noted in `agents/CHAT.md`*)
- [ ] **Task 7.3:** Security review: the hostile-name test, text only. **L2**. (*Owner: Switch | Trace: design gate condition | Verification: `security gate (phase 7): ...`*)
- [ ] **Task 7.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT24 sections 3-6 | Verification: result in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make check`, and `docs/SDLC.md` "Last verified" updated*)
- [ ] **Task C.2:** Document grooming, ADR-0052 to ADR-0054, lessons. Chat report only if the owner asks. (*Owner: Oracle | Trace: N/A — closeout | Verification: ADRs in `docs/DECISIONS.md`; groom noted in `agents/CHAT.md`*)
- [ ] **Task C.3:** End-to-end user testing on the baseline run and the console, against `docs/sprints/UAT_PLAN_SPRINT24.md`, and lesson review. (*Owner: Smith | Trace: UND-93, 94, 95, 87, 82 | Verification: Smith acceptance verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task C.4:** Sprint retrospective and backlog grooming. (*Owner: Mouse | Trace: N/A — closeout | Verification: retros in `docs/sprints/RETRO_SPRINT24.md`, posted in `agents/CHAT.md`*)
- [ ] **Task C.5:** Sprint launch and release announcement; merge `sprint-24` into `main` only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch recorded in `agents/CHAT.md`*)
