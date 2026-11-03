# Sprint 25 Task Board: the tool fixes the categories, and payments know what they paid for

*   **Goal**: Every merchant gets one category from a clean list (ISO 18245 plus the owner's additions) chosen by Jev, not copied from Monarch or Amex; transfers come from text-found links and the tool's categories; each credit card payment shows the charges it settled and what they were for; spending is built from the tool's categories.
*   **Tier**: Tier 1 (Major)
*   **Total Points** (optional): 29
*   **Branch**: `sprint-25` (cut from `sprint-24`, not merged)
*   **Status**: Planning — awaiting Morpheus Step 3a Review
*   **Plan**: `docs/sprints/USER_STORIES_SPRINT25.md` (Gate 1 approved after one rejection), `ARCH_SPRINT25.md` (Gate 2 approved after one amendment), security design gate: no blocking findings. Decisions: `OWNER_DECISIONS_SPRINT22.md` 10 to 13b. Baselines: `data/Transactions_2026-11-02T19-14-07.csv` (Monarch) and `data/activity-11-03-2026.csv` (Amex, from 2025-11-01).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-03*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. Each phase is one build task followed by its three gates; a phase is not done until Morpheus passes it. Edit files with Edit/Write only (owner rule). The first live run of the new categorization costs about 1,650 Jev requests (about four minutes); later runs reuse the capture. Real-data checks use the two baselines with `since=2025-11-01`.

### Phase 1: A clean list of categories (UND-96, 5 pts)
*Phase goal: the ISO list plus the owner's additions as one list, with its checks; pins are checked against it.*
- [x] **Task 1.1:** Tests first, then generic `map.unique`; the `additions` source and shipped starting file `examples/household/additions.jsonl`; the `taxonomy` stages ("Group: Name"); checks before any Jev request (missing path, line without group or name, repeated name); pins checked against this list instead of the export's categories; docs. **L2** (one sketch, one stage, one data file; pattern known). (*Owner: Neo | Trace: UND-96 AC1-5, ADR-0055 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 1.2:** UAT: 13 ISO groups and 280 names plus six additions; an owner's file replaces the shipped one; each bad additions line and a bad pin stops the run naming it before any Jev request. **L2**. (*Owner: Trin | Trace: UND-96 AC1-5 | Verification: UAT verdict and evidence in `agents/CHAT.md` and `docs/sprints/UAT_PLAN_SPRINT25.md`*)
- [x] **Task 1.3:** Security quick pass: the additions file as a new local input. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 1): ...` in `agents/CHAT.md`*)
- [x] **Task 1.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT25 sections 3-5, ADR-0055 | Verification: result in `agents/CHAT.md`*)

### Phase 2: Jev puts every merchant in a category (UND-97, 8 pts)
*Phase goal: a two-step Jev choice from the clean list replaces placing by export categories; the export's category is no longer shown or used.*
- [x] **Task 2.1:** Tests first (a Jev double that fails if it is shown an export category), then `categorize_merchant.yaml` (group, then name, then status), `household.yaml` wired to it, `place_merchant.yaml` and `name_merchant.yaml` removed, pins and `review.jsonl` kept, `category` and `category_source` on every record, progress printed; docs. **L3** (a new Jev flow, the pipeline's order of stages changes, failure cases). (*Owner: Neo | Trace: UND-97 AC1-6, ADR-0055 | Verification: `bobp make test`, `bobp make lint`*)
- [x] **Task 2.2:** UAT on the real files, live: every merchant placed or for review; the same questions whatever the export's categories say (run once on a copy of the export with its categories scrambled); pinned merchants never asked; a replay costs no requests. **L3**. (*Owner: Trin | Trace: UND-97 AC1-6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [x] **Task 2.3:** Security review: what Jev now sees (less) and the additions names as options. **L2**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 2): ...`*)
- [x] **Task 2.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT25 sections 3-4, ADR-0055 | Verification: result in `agents/CHAT.md`*)

### Phase 3: Kinds follow links and the tool's categories (UND-98, 5 pts)
*Phase goal: link candidates found from text; a transfer is a link or "Household: Transfer"; a crosswalk shows tool and export side by side.*
- [ ] **Task 3.1:** Tests first, then `candidates` from the record's own text (never Category), kind from link or category, merchants for review stay unplaced, `crosswalk.jsonl` with the flag, Ridgewood income and expenses in the summary, `transfer_basis` renamed; docs. **L3** (the order of the pipeline and a rule other stories depend on). (*Owner: Neo | Trace: UND-98 AC1-6, ADR-0056 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 3.2:** UAT on the real files: a mislabeled bank-side payment still links; no label decides a kind; the crosswalk and its flag; Ridgewood figures reported against the earlier file with the payees that account for the difference. **L3**. (*Owner: Trin | Trace: UND-98 AC1-6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 3.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 3): ...`*)
- [ ] **Task 3.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT25 section 4, ADR-0056 | Verification: result in `agents/CHAT.md`*)

### Phase 4: Allocate payments to charges, as generic stages (UND-99 part 1, 4 pts)
*Phase goal: `map.allocate` and `map.top`, tested on their own.*
- [ ] **Task 4.1:** Tests first, then `map.allocate` (oldest first, never past the amount, remainder, a charge in at most one payment, a charge dated after the payment never used) and `map.top` (the largest few rows per group); docs. **L2**. (*Owner: Neo | Trace: UND-99 AC1, AC5, ADR-0057 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 4.2:** UAT on the Amex baseline outside the sketch: 11 of 12 payments within 5%, the first unexplained by $10,437, settled plus open equals all charges to the cent. **L2**. (*Owner: Trin | Trace: UND-99 AC1, AC5, AC6 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 4.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 4): ...`*)
- [ ] **Task 4.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT25 section 3, ADR-0057 | Verification: result in `agents/CHAT.md`*)

### Phase 5: Payments know what they paid for (UND-99 part 2, 4 pts)
*Phase goal: `payments.jsonl`, `settled_by` on each charge, the open balance.*
- [ ] **Task 5.1:** Tests first, then the `pay_*` stages in the household: payments from the linked card-side halves, the Amex pool, `payments.jsonl` with the five largest categories, `settled_by`, `open_balance`, a card with no payments left open; docs. **L3** (depends on kinds, categories and the allocation; failure cases). (*Owner: Neo | Trace: UND-99 AC1-7 | Verification: `bobp make test`, `bobp make lint`*)
- [ ] **Task 5.2:** UAT on the real files: 12 payment lines, each payment's breakdown by category, the open balance of about $28,444, the first payment marked unexplained. **L3**. (*Owner: Trin | Trace: UND-99 AC1-7 | Verification: UAT verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 5.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 5): ...`*)
- [ ] **Task 5.4:** Code review. **L2**. (*Owner: Morpheus | Trace: ARCH_SPRINT25 sections 4-5, ADR-0057 | Verification: result in `agents/CHAT.md`*)

### Phase 6: Spending by the tool's category (UND-100, 3 pts)
*Phase goal: `spending.jsonl` and the console's list use the tool's categories.*
- [ ] **Task 6.1:** Tests first, then the `spend_*` stages take the tool's category (`unplaced` for a merchant for review), no export category in the list, transfers and the card payments themselves out; docs. **L2**. (*Owner: Neo | Trace: UND-100 AC1-4 | Verification: `bobp make test`, `bobp make lint`, `bobp make test-browser`*)
- [ ] **Task 6.2:** UAT on the real run and in the console: the list is ISO and Household categories only; shares add to 1; amounts equal `spending_total`. **L2**. (*Owner: Trin | Trace: UND-100 AC1-4 | Verification: UAT verdict and screenshot noted in `agents/CHAT.md`*)
- [ ] **Task 6.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 6): ...`*)
- [ ] **Task 6.4:** Code review. **L1**. (*Owner: Morpheus | Trace: ARCH_SPRINT25 section 5 | Verification: result in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make check`, and `docs/SDLC.md` "Last verified" updated*)
- [ ] **Task C.2:** Document grooming, ADR-0055 to ADR-0057, lessons. Chat report only if the owner asks. (*Owner: Oracle | Trace: N/A — closeout | Verification: ADRs in `docs/DECISIONS.md`; groom noted in `agents/CHAT.md`*)
- [ ] **Task C.3:** End-to-end user testing on the baselines and the console, against `docs/sprints/UAT_PLAN_SPRINT25.md`, and lesson review. (*Owner: Smith | Trace: UND-96..100 | Verification: Smith acceptance verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task C.4:** Sprint retrospective and backlog grooming. (*Owner: Mouse | Trace: N/A — closeout | Verification: retros in `docs/sprints/RETRO_SPRINT25.md`, posted in `agents/CHAT.md`*)
- [ ] **Task C.5:** Sprint launch and release announcement; merge `sprint-25` (with `sprint-24` before it) into `main` only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch recorded in `agents/CHAT.md`*)
