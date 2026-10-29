# Sprint 17 Task Board: Dedupe, transfers, refunds and new categories

* **Goal**: Turn Sprint 16's reconcile-and-categorise ETL into the owner's real cleanup: each export served as JSONL by its own source server, purchases merged with the sign flipped, transfers paired and kept out of spending, refunds linked to their merchant, merchants placed in one of 180 categories or given a new MCC-named one, and a JSONL result.
* **Tier**: Tier 1 (Major)
* **Total Points**: 29 (UND-49 to 55)
* **Branch**: `sprint-17` (from `main` at 5786fc8)
* **Status**: Planned — awaiting Morpheus plan review. Stories approved at Smith Gate 1 and architecture at Gate 2 on 2026-10-27.
* **Scope**: `docs/sprints/USER_STORIES_SPRINT17.md`, `docs/sprints/ARCH_SPRINT17.md`. Private CSVs and run output stay under ignored `data/` and `build/runs/`; tests use synthetic fixtures with the same columns and shapes (sign-flipped pairs, repeated amounts, transfers, refunds).

## Stage 0: SDLC Gate (Blocker)

- [x] **Task S0.1:** `docs/SDLC.md` exists; ARCH_SPRINT17 §7 finds no new language, package manager, runtime version or standard make target, so no Tank Phase 0 is scheduled. (*Owner: Mouse | Verification: Morpheus's build-environment check in the architecture; Python packages added through SDLC §4.*)

## Sprint Execution Phases

### Phase 0: Spike - settle the four unverified facts
*Phase goal: Answer the architecture's four Phase 0 questions with evidence, record the controller-language decision, and unblock the MCC source, before any story code. Synthetic data only; a live Jev probe needs the owner's go-ahead and key.*

- [x] **Task 0.1:** Spike (`*spike`): (1) express the controller's stages, gates and failure branch in `python-statemachine`'s YAML representation; (2) read `typesafe-sdk`'s Noul and Choice answers for per-answer probabilities, batching, timeout and error types; (3) serve and call a paged tool over stdio with the official `mcp` Python SDK at 1,000 rows per page; (4) find the MCC list source and its licence. (*Owner: Neo, with Morpheus | Verification: findings in `agents/morpheus/spike_sprint17.md`, one answer per question with the command or page that proves it; scratch code not merged.*)
- [x] **Task 0.2:** Decide (`*lead decide`): controller in Python (replacing `src/etl/run.mjs`, `categories.mjs`, `csv.mjs`) or Node for this sprint; record the MCC source; raise anything that fails to the owner. (*Owner: Morpheus | Verification: decision recorded in the findings file and as ADR-0038 in `docs/DECISIONS.md`; if the MCC list cannot be committed, the owner is asked before Phase 4.*)

**Gate:** the four questions are answered and the controller language is decided. If the decision needs the owner (MCC licence, a live Jev probe), Phase 1 waits.

### Phase 1: Source servers and hydration (UND-49)
*Phase goal: Each export is served as JSONL by its own MCP source server and staged for SQLMesh.*

- [x] **Task 1.1:** Implement (`*impl`): Monarch and Amex source servers (`describe`, `read_transactions`), column validation before serving, the hydration stage that pages them into per-run JSONL snapshots with counts and hashes; synthetic fixtures with multi-line Amex rows. (*Owner: Neo | Verification: unit tests for both servers and the hydration stage; missing file and missing column refuse before paging; `bobp make test`.*)
- [x] **Task 1.2:** UAT (`*uat`): UND-49 AC 1-5 on synthetic files, including the multi-line row and the no-household-data check. (*Owner: Trin | Verification: UAT rows for `UND-49` in `docs/sprints/UAT_PLAN_SPRINT17.md`, commands and captured counts.*)
- [x] **Task 1.3:** Review (`*review`): server contract, page limit, error messages, privacy. (*Owner: Morpheus | Verification: review verdict recorded; commit `Phase 1: ...` per the SDLC.*)

### Phase 2: One record per purchase (UND-50)
*Phase goal: A purchase in both exports becomes one record; the Amex account is detected or given.*

- [x] **Task 2.1:** Implement: `purchase_pairs` SQL model (sign-flipped, one-to-one inside a date-and-amount group, exact merchant text first), Amex-account auto-detection with `--amex-account` override and its refusals, summary counts. (*Owner: Neo | Verification: SQLMesh model tests for repeated amounts (two $4.50), one-sided rows, other-account coincidences; controller tests for detection tie and none; `bobp make test`.*)
- [x] **Task 2.2:** UAT: UND-50 AC 1-5 on synthetic data; the real-file counts (4,276 of 4,321 paired; 45 unmatched) measured locally by Trin, counts only. (*Owner: Trin | Verification: UAT rows for `UND-50`; the real-file counts are an owner-run acceptance step, not committed.*)
- [x] **Task 2.3:** Review: pairing rule against ADR-0039, determinism, no data in fixtures. (*Owner: Morpheus | Verification: verdict recorded; commit `Phase 2: ...`.*)
- [x] **Task 2.4 (added 2026-10-27 after the owner chose 2026 year to date):** Implement the period: `period_start` variable, period-scoped inputs in `purchase_pairs`, the `period_scope` model for the summary counts, `--since`-aware account detection. (*Owner: Neo | Verification: SQLMesh tests for rows before the start, undated rows and the scope counts; detection test that only in-period matches count; `bobp make test`. Reviewed with Phase 3.*)
- [ ] **Task 2.5:** Re-measure on the fresh exports when the owner has put them in `data/` (counts only) and record the numbers in `UAT_PLAN_SPRINT17.md`. (*Owner: Trin | Verification: UAT row `UAT-UND-50-04` with paired, unpaired, left-out and in-period counts.*)

### Phase 3: Transfers and refunds (UND-51, UND-52)
*Phase goal: Transfer legs are paired and kept out of spending; refunds link to an original charge or are marked without one.*

- [x] **Task 3.1 (done 2026-10-27; business days added at the owner's suggestion, holidays from the `holidays` package; the owner then ruled that Venmo and Zelle payments are expenses and real transfers are between own accounts, so unpaired candidates go to Jev, Task 3.2):** Implement: `transfer_pairs` SQL (label/description rule, 3 days, one-to-one nearest date) with the spending summary exclusion and the other-labels counts; `refund_candidates` SQL (same merchant key, earlier, amount at least the refund's). (*Owner: Neo | Verification: SQLMesh model tests for pairing, same-amount same-week, refunds not marked transfers, no later-dated original; `bobp make test`.*)
- [x] **Task 3.2:** Implement: a thin Jev client (`typesafe-sdk`, pinned, a double in tests); the refund stage (Choice among the five most recent originals, answer validated against the list, stored with confidence); the transfer-payee stage (one Noul per distinct payee of an unpaired transfer candidate: own bank or card account, as against a person, a payment app such as Venmo or Zelle, or a merchant; above 0.7 external transfer, below 0.3 spending, between review). (*Owner: Neo | Verification: unit tests with a double for off-list answer, single and multiple candidates, no candidate, Venmo and Zelle judged as spending, a savings-bank payee judged as an external transfer, Jev unreachable stops the stage, one request per distinct payee.*)
- [x] **Task 3.3:** UAT and review: UND-51 AC 1-6 and UND-52 AC 1-4 on synthetic data; Morpheus reviews the SQL and the Jev stage together. (*Owner: Trin, then Morpheus | Verification: UAT rows and verdict recorded; commit `Phase 3: ...`.*)

### Phase 4: Categories (UND-53, UND-55)
*Phase goal: Each merchant fits an existing category or gets a new MCC-named one, with every Jev answer validated.*

- [x] **Task 4.1:** Implement: the merchant fit stage (Noul and Choice in one request, 0.3 and 0.7 bands, batches, reuse per merchant key, count of requests printed before the first call) and the Monarch category list as data. (*Owner: Neo | Verification: unit tests with a Jev double for each band, off-list answer, reuse count, Jev unreachable stops the run; `bobp make test`.*)
- [x] **Task 4.2:** Implement: the naming stage (group Choice, name Choice, Noul rubric for the top three names, best above 0.7, review otherwise), new categories offered to later batches, MCC list as data with a missing-file refusal. (*Owner: Neo | Verification: unit tests for pass, all-fail to review, no invented names, later merchants offered the new name.*)
- [x] **Task 4.3 (a live Jev trial is held for the owner's go-ahead):** UAT and review: UND-53 AC 1-4 and UND-55 AC 1-5 with a Jev double; Morpheus reviews the rubric text and the stage order. A live Jev probe on a handful of synthetic merchants only with the owner's go-ahead. (*Owner: Trin, then Morpheus | Verification: UAT rows and verdict recorded; commit `Phase 4: ...`.*)

### Phase 5: JSONL result and summary (UND-54)
*Phase goal: One JSONL file and a counts-only summary, byte-identical on a repeat.*

- [x] **Task 5.1:** Implement: `final_records` SQL, `COPY` to `result.jsonl` in a fixed order, the Sprint 17 summary counts, `--out` with the unwritable-path refusal, removal of `review.csv`. (*Owner: Neo | Verification: end-to-end test on synthetic data with a Jev double: record fields, counts, byte-identical rerun, unwritable output, `bobp make test`.*)
- [x] **Task 5.2:** UAT: UND-54 AC 1-5, plus a 4,700-pair synthetic scale run as in Sprint 16. (*Owner: Trin | Verification: UAT rows for `UND-54`, timing recorded.*)
- [x] **Task 5.3:** Review: output contract, privacy, the breaking change noted in CHANGELOG and USER_GUIDE. (*Owner: Morpheus | Verification: verdict recorded; commit `Phase 5: ...`.*)

## Sprint Closeout

- [x] **Task C.1:** Tank `*devops sdlc-check`: clean setup, `bobp make check`, SDLC record updated for any added Python packages. (*Owner: Tank | Verification: `bobp make distclean`, `bobp make install`, `bobp make check`; `docs/SDLC.md` records verification.*)
- [ ] **Task C.2:** Oracle `*ora groom`: ADR-0038 and ADR-0039, USER_GUIDE ETL section, CHANGELOG, lessons, chat archive after launch. (*Owner: Oracle | Verification: artifact rubrics pass; `bobp chat-report --moniker SPRINT_17` after launch.*)
- [ ] **Task C.3:** Smith `*user test`: end-to-end acceptance against `UAT_PLAN_SPRINT17.md`, with the owner's own run on the real files (the 4,276 and 45 counts). (*Owner: Smith | Verification: UAT rubric verdict and the owner's acceptance in `agents/CHAT.md`.*)
- [ ] **Task C.4:** All personas post retrospectives and backlog items. (*Owner: All | Verification: each persona's retro in `agents/CHAT.md`.*)
- [ ] **Task C.5:** Cypher `*pm launch`. (*Owner: Cypher | Verification: launch recorded in `agents/CHAT.md`; merge and push only when the owner asks.*)
