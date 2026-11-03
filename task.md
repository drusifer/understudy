# Sprint 23 Task Board: household numbers you can trust, and a run that tells its story

*   **Goal**: The household run's income, expenses and net for an account match the owner's edited export, because transfers come from the owner's categories. Unsure merchants arrive as a per-merchant list, the owner's pins are kept, and the event stream carries states and decisions.
*   **Tier**: Tier 1 (Major)
*   **Total Points** (optional): 23
*   **Branch**: `sprint-23`
*   **Status**: Planning — awaiting Morpheus Step 3a Review
*   **Plan**: `docs/sprints/USER_STORIES_SPRINT23.md` (Gate 1 approved), `ARCH_SPRINT23.md` (Gate 2 approved), security design gate: no blocking findings. Decisions: `OWNER_DECISIONS_SPRINT22.md` 4-8. Baseline: `data/Transactions_2026-11-02T19-14-07.csv`.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-02*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. Each phase is one build task followed by its three gates; a phase is not done until Morpheus passes it. Edit files with Edit/Write only (owner rule). Real-data checks use the baseline file and run live, so each costs Jev requests; Trin replays a captured run where the check allows.

### Phase 1: Transfers come from the owner's categories (UND-89, 5 pts)
*Phase goal: a record's kind follows the export's Category; `external_transfer` and the payee reading are gone.*
- [x] **Task 1.1:** Tests first, then `typed` takes `transfer` from Category Transfer or Credit Card Payment, never otherwise; remove `external_transfer`, `judge_payee.yaml` and its stages; stop on a missing Category column before any Jev request; count changed kinds in `summary.json`; update `docs/USER_GUIDE.md`, `docs/SKETCHES.md` and tests that name `external_transfer`. **L2** (several files in one bounded area; pattern known). (*Owner: Neo | Trace: UND-89 AC1-5, ADR-0050 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 1.2:** UAT on the baseline: no Ridgewood record labeled Transfer or Credit Card Payment is a purchase, refund or credit; the nine Schwab deposits are transfers; a file without Category stops with one line. **L2**. (*Owner: Trin | Trace: UND-89 AC1-5 | Verification: UAT verdict and evidence in `agents/CHAT.md` and `docs/sprints/UAT_PLAN_SPRINT23.md`*)
- [x] **Task 1.3:** Security quick pass: the new Category read and the removed Jev call. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 1): ...` in `agents/CHAT.md`*)
- [x] **Task 1.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT23 sections 3-5, ADR-0050 | Verification: result in `agents/CHAT.md`*)

### Phase 2: Income and expenses I can check (UND-90, 3 pts)
*Phase goal: the summary gives income, expenses and net per account and overall, transfers set aside.*
- [x] **Task 2.1:** Tests first, then a `sum` option on `group` (generic, documented), the `totals` stages and `totals.jsonl`, and the net-spending figure in `summary.json`; accounts with no records left out. **L2**. (*Owner: Neo | Trace: UND-90 AC1-4 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 2.2:** UAT: Ridgewood income $363,348.62 and expenses $205,042.27 equal the baseline's sums to the cent; the overall figure uses the same rule. **L2**. (*Owner: Trin | Trace: UND-90 AC1-4 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 2.3:** Security quick pass: new sink holds merchant-class data in the ignored run folder. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 2): ...`*)
- [x] **Task 2.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT23 section 5 | Verification: result in `agents/CHAT.md`*)

### Phase 3: Merchants for review, as a list (UND-91, 5 pts)
*Phase goal: `review.jsonl`, one line per merchant, sorted by records, with Jev's top two guesses.*
- [x] **Task 3.1:** Tests first, then `place_merchant` outputs the runner-up beside `status`; `review.jsonl` with `payee, count, amount, top, top_probability, runner_up, runner_up_probability, reason`; sorted by count; empty file when nothing needs review. **L2**. (*Owner: Neo | Trace: UND-91 AC1-5 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 3.2:** UAT on a replayed household run: line count equals distinct review merchants; order; reasons. **L2**. (*Owner: Trin | Trace: UND-91 AC1-5 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 3.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 3): ...`*)
- [x] **Task 3.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT23 sections 4-5 | Verification: result in `agents/CHAT.md`*)

### Phase 4: Pinned categories are kept (UND-92, 5 pts)
*Phase goal: a pin file the owner edits; pinned merchants skip Jev and leave the review list.*
- [ ] **Task 4.1:** Tests first, then the `pinned` source (default `.understudy/pinned.jsonl`, absent means no pins and says so, a missing explicit path stops), the `without` action, pinned records placed with level `pinned`, taxonomy and shape checks before any Jev request, no pinned merchant in `review.jsonl`. **L3** (loader boundary, new action, failure cases, determinism). (*Owner: Neo | Trace: UND-92 AC1-6, ADR-0051 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 4.2:** UAT: a pinned merchant causes no Jev request and is placed as pinned; bad pins, a missing explicit path and an absent default file behave as the criteria say; two runs with the same pins agree. **L3**. (*Owner: Trin | Trace: UND-92 AC1-6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 4.3:** Security review: the pin file is a new local input parsed before any Jev request; no free text reaches a pin. **L2**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 4): ...`*)
- [ ] **Task 4.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT23 sections 4-6, ADR-0051 | Verification: result in `agents/CHAT.md`*)

### Phase 5: The run tells its story (UND-81, 5 pts)
*Phase goal: `events.jsonl` carries the machine, each state entered, each decision and the ending; old logs show as unreadable.*
- [ ] **Task 5.1:** Tests first, then `machine`, `state_entered`, `decision` and ending lines from `RunRecord`/the runner; the console names a missing story line as an unreadable run. **L3** (runner, sketches and console agree on one stream). (*Owner: Neo | Trace: UND-81 AC1-5 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [ ] **Task 5.2:** UAT on a new run and on an old run folder in the console: story lines present; the old run shows unreadable and names the line. **L2**. (*Owner: Trin | Trace: UND-81 AC1-5 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 5.3:** Security quick pass: decision lines carry option names and probabilities already in the run folder. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 5): ...`*)
- [ ] **Task 5.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT23 section 5 | Verification: result in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make check`, and `docs/SDLC.md` "Last verified" updated*)
- [ ] **Task C.2:** Document grooming, ADR-0050 and ADR-0051, lesson archiving. Chat report only if the owner asks. (*Owner: Oracle | Trace: N/A — closeout | Verification: ADRs in `docs/DECISIONS.md`; groom noted in `agents/CHAT.md`*)
- [ ] **Task C.3:** End-to-end user testing on the baseline household run, against `docs/sprints/UAT_PLAN_SPRINT23.md`, and lesson review. (*Owner: Smith | Trace: UND-89..92, UND-81 | Verification: Smith acceptance verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task C.4:** Sprint retrospective and backlog grooming. (*Owner: Mouse | Trace: N/A — closeout | Verification: retros in `docs/sprints/RETRO_SPRINT23.md`, posted in `agents/CHAT.md`*)
- [ ] **Task C.5:** Sprint launch and release announcement; merge `sprint-23` into `main` only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch recorded in `agents/CHAT.md`*)
