# Sprint 17 Acceptance Test Plan (UAT): Dedupe, transfers, refunds and new categories

* **Sprint**: `SPRINT_17`
* **Author**: Trin (*qa)
* **Date**: 2026-10-27
* **Branch**: `sprint-17`
* **Status**: Phase 5 UAT re-run PASSED 2026-10-29 after the DEF-UND54-01 fix (destination policy in `_check_destination_policy`); phases 1 to 4 retain their prior verdicts

## 1. Scope

* **User stories covered:** `UND-49` to `UND-55`; Phase 5 completes the output contract and persistence checks. Live Jev quality and owner acceptance remain separate from synthetic verification.
* **Environment:** Sprint 17 worktree, CPython 3.12.15, `mcp` 2.3.0, Node 24. Synthetic CSVs in temporary directories; the owner's real files were read locally for counts only and no snapshot was kept.

## 2. Phase 1: source servers and hydration (UND-49)

### `UAT-UND-49-01` Each export is served as JSONL records
* **Story/AC:** UND-49 AC 1, 2.
* **Command:** `bobp make test-py` (`tests/python/test_sources.py`, `test_hydrate.py`).
* **Expected:** each server offers `describe` and `read_transactions`; records carry `source`, `source_row_number`, `transaction_date`, `amount`, `merchant`, `account` and every original column in `raw_record`.
* **Result:** Pass. 16 Python tests, 0 failures. Record fields asserted for Monarch (account `Card (...1111)`, `Original Statement` kept) and Amex (US date `01/02/2026` normalized to `2026-01-02`, original kept). Both tools have a description.

### `UAT-UND-49-02` Counts on the real files
* **Story/AC:** UND-49 AC 3.
* **Command:** `hydrate("monarch", ...)` and `hydrate("amex", ...)` on the owner's files, from the Sprint 17 worktree; counts printed, snapshots deleted.
* **Expected:** Monarch 14,522 records and Amex 4,321, an Amex row with several lines counting once.
* **Result:** Pass. Monarch 14,522 records in 15 pages; Amex 4,321 records in 5 pages; line counts of the written files equal the record counts.

### `UAT-UND-49-03` A bad file stops the run before anything is written
* **Story/AC:** UND-49 AC 4.
* **Commands:** `python -m src.etl.source_server amex <file without an amount column>` and `... monarch <missing file>`; tests `test_a_missing_file_stops_before_anything_is_written`, `test_a_missing_column_stops_before_anything_is_written`.
* **Expected:** exit 2, a message naming the file and the column or the reason; no output directory or file created.
* **Result:** Pass. `understudy: Amex CSV /tmp/bad_amex.csv is missing a required amount column (recognized: amount, transaction amount)`, exit 2; `understudy: Monarch CSV cannot be read: /tmp/does-not-exist.csv (No such file or directory)`, exit 2. Tests confirm the destination and its parent directory do not exist afterwards.

### `UAT-UND-49-04` No household data in the repository; repeatable snapshot
* **Story/AC:** UND-49 AC 5 (and the traceability of AC 2).
* **Command:** tests use only temporary files built in the test; `git check-ignore data/activity.csv`; `test_the_snapshot_is_the_same_on_every_run`.
* **Expected:** fixtures are made up; `data/` is ignored; two hydrations of one file give the same hash.
* **Result:** Pass. `data/` is ignored (`.gitignore`); identical SHA-256 on both runs; the snapshot is written as `.part` and renamed on success, so a failed run leaves no partial file.

* **Phase 1 UAT verdict:** **PASSED**. No defects. One bug was found in review and fixed before the gate (an f-string docstring that would have left the `read_transactions` tool without a description); a test now asserts both tools are described.

## 3. Phase 2: one record per purchase (UND-50)

### `UAT-UND-50-01` Sign-flipped pairs keep both source rows; repeated amounts stay separate
* **Story/AC:** UND-50 AC 1, 3, 4.
* **Command:** `bobp make test-etl` (`sqlmesh/tests/test_purchase_pairs.yaml`, 6 cases) and `bobp make test-py` (`tests/python/test_pairing.py`, 6 cases).
* **Expected:** a charge and its sign-flipped copy become one `paired` record carrying both source rows; two real $4.50 purchases on one day stay two records, paired by statement text; a coincidence in another account is not paired; unequal counts pair what they can; a same-date pair is never given up for a near-date one; a row posted a day or two apart pairs, nearest first; a row without a date is kept as `invalid_key`.
* **Result:** Pass. 8 SQLMesh model tests (2 earlier + 6 new) and 6 account-detection tests; the near-date case failed before the third pass was written and passes after.

### `UAT-UND-50-02` Real-file counts
* **Story/AC:** UND-50 AC 2, 5.
* **Command:** hydrate both real files into an ignored folder, detect the card, run SQLMesh for `etl.purchase_pairs`, query counts, delete the folder (counts only).
* **Expected:** most Amex rows pair; the rest are listed single; no source row is used twice; records = Monarch rows + Amex rows − pairs.
* **Result:** Pass. 14,567 records = 14,522 + 4,321 − 4,276. 4,276 of 4,321 Amex rows paired (60 by statement text and date, 4,147 by order within a date, 69 within three days); 45 Amex rows unpaired; no Monarch or Amex row used twice. The first run, with same-date pairing only, paired 4,207 and left 114; 95 of those 114 had a same-amount card row one to three days apart, which led to the third pass.

### `UAT-UND-50-03` The card account is found, or the run says what to pass
* **Story/AC:** ARCH_SPRINT17 section 6 (account detection) supporting UND-50 AC 1.
* **Command:** `bobp make test-py` (`test_pairing.py`).
* **Expected:** the account with the most sign-flipped matches is the card; no matches, a tie, an override matching nothing or two accounts is refused with "could not tell which Monarch account is the Amex card (candidates: ...); pass --amex-account <text>", account names shown without their digits.
* **Result:** Pass. All refusals asserted, including that no account number appears in the message. On the real files the card was detected without an override.

* **Phase 2 UAT verdict:** **PASSED**. No defects. Finding recorded: only 60 pairs match on statement text (Monarch's `Original Statement` rarely equals Amex's description exactly), so most pairs rely on being the only candidate in their date and amount group; it does not change counts but weakens the exact-first rule for busy days.

## 4. Phase 3: transfers and refunds (UND-51, UND-52)

### `UAT-UND-51-01` Transfer legs pair one-to-one on business days and both are kept
* **Story/AC:** UND-51 AC 1, 5, 6.
* **Command:** `bobp make test-etl` (`test_transfer_pairs.yaml`, 8 cases, `test_business_calendar.yaml`).
* **Expected:** a Ridgewood debit and the card's credit pair and both rows stay; two same-amount payments in a week pair one-to-one; a Friday payment landing Monday, or the Tuesday after a Monday holiday, is one business day; legs more than three business days apart, or in one account, do not pair; a refund is never a transfer; a merchant whose name contains "payment" is not a candidate.
* **Result:** Pass. 8 transfer cases and the calendar case pass (25 model tests in all).

### `UAT-UND-51-02` Unpaired candidates are judged by payee, Venmo and Zelle are spending
* **Story/AC:** UND-51 AC 3, 4.
* **Command:** `bobp make test-py` (`test_transfers.py`, a Jev double).
* **Expected:** one request per distinct payee; Venmo and Zelle judged as spending, a savings-bank payee as an external transfer, an unsure payee goes to review; Jev sees the payee, the owner's account names without numbers and the payment counts, never Monarch's category label; Jev unreachable stops the stage naming it.
* **Result:** Pass. 5 tests: decisions for 4 distinct payees from 6 records with 4 requests, no account number or category in the state, error message names "transfer payees".

### `UAT-UND-51-03` Real-file transfer counts (fresh exports, counts only)
* **Story/AC:** UND-51 AC 3, 4.
* **Command:** hydrate, detect, run SQLMesh through `refund_candidates`, query counts, delete the run.
* **Expected:** every leg is used at most once; the unpaired candidates are the ones Jev will judge.
* **Result:** Pass. 155 transfer candidates: 40 paired (20 pairs, 24 at gap 0 and 16 at gap 1 business day, all one-to-one), 115 unpaired, across 25 distinct payees (Venmo 59 records, Bank Transfer 18, Ridgewood Savings Bank 7, Zelle 6). That is 25 Jev requests. Live Jev decisions are not run in this phase (owner's go-ahead needed); the owner checks the final Venmo/Zelle outcome on the acceptance run.

### `UAT-UND-52-01` Refunds link to their original, or are marked
* **Story/AC:** UND-52 AC 1, 3, 4.
* **Command:** `bobp make test-etl` (`test_refund_candidates.yaml`, 4 cases).
* **Expected:** one earlier same-merchant charge at least the refund's links without asking; several are listed most recent first with the full count (five shown); none is marked `no_original`; a later-dated charge, a smaller charge, a transfer leg and income are not offered or counted as refunds.
* **Result:** Pass.

### `UAT-UND-52-02` Jev chooses among several originals, never off the list
* **Story/AC:** UND-52 AC 2.
* **Command:** `bobp make test-py` (`test_refunds.py`, a Jev double).
* **Expected:** only refunds with several originals are asked; the choice and its confidence are kept; an answer that is not offered links nothing; one original or none asks nothing; Jev unreachable stops the stage naming it; two identical charges get distinct option names.
* **Result:** Pass. 5 tests. Real files: 65 refunds need a choice (65 requests), 27 link directly, 18 have no original.

### `UAT-UND-52-03` Jev client behaviour
* **Story/AC:** supports UND-52 AC 2 and UND-51 AC 3.
* **Command:** `bobp make test-py` (`test_jev.py`, a fake SDK client).
* **Expected:** a Choice returns the option, its confidence and every probability; a Noul returns the probability of yes; no key is refused naming `TYPESAFE_API_KEY`; an unreachable service is an error, not an answer.
* **Result:** Pass. 4 tests.

* **Phase 3 UAT verdict:** **PASSED** for the SQL and the Jev stages with doubles. Open for the acceptance run: the live Jev outcome on the real payees and refunds (needs the owner's go-ahead and key), and persistence of the decision rows, which belongs to the controller in Phase 5.

## 5. Phase 4: categories (UND-53, UND-55)

### `UAT-UND-53-01` What Jev may offer, and which merchants it is asked about
* **Story/AC:** UND-53 AC 1.
* **Command:** `bobp make test-etl` (`test_category_inputs.yaml`).
* **Expected:** the offered categories are the Monarch labels in use, without "transfer"/"payment" labels and without Amex-upload-style labels; the merchants to place are the distinct merchants of spending records, with paired transfer legs and external-transfer payees left out, each with a record count, up to three amounts and up to three statement texts.
* **Result:** Pass. 28 model tests in all (2 new here).

### `UAT-UND-53-02` Fit, choose, review, reuse
* **Story/AC:** UND-53 AC 1 to 4.
* **Command:** `bobp make test-py` (`test_categorize.py`, `test_jev.py`, a Jev double).
* **Expected:** one request per distinct merchant asking a Noul and a Choice together; above 0.7 places the merchant in the Choice's category with the fit probability and confidence; between 0.3 and 0.7, or an answer that is not offered, goes to review (a suggestion is kept for the owner); the request count is announced before the first request; a Jev failure stops the stage naming it and nothing is placed.
* **Result:** Pass. 59 Python tests in all (15 new for categorize, the batched client and the shared request wrapper). Review found that after a Jev failure the queued merchants could still be sent (16 requests against a limit of 8 in a test with 40 merchants); a shared wrapper (`GatedJev`: concurrency limit, request counter, stop after the first failure) now serves the refund, transfer and category stages, with its own tests.

### `UAT-UND-55-01` A new category is named from the MCC list, never made up
* **Story/AC:** UND-55 AC 1 to 5.
* **Command:** `bobp make test-py` (`test_categorize.py`, `test_mcc.py`).
* **Expected:** a merchant that fits nothing is named by a group Choice, a name Choice and a rubric Noul on the top three names; the best above 0.7 becomes a new category, otherwise the merchant goes to review; a new category is offered to later merchants and shared (merchant and record counts kept); every category in the result is an offered one or an MCC name; an unreadable MCC list stops the run before naming.
* **Result:** Pass. Venmo and Zelle (tested) share one MCC-named category with 65 records; a merchant whose names all fail the rubric goes to review and creates nothing; a made-up answer is never placed. The MCC list is 13 groups and 280 names (largest group 58) from the MIT `iso18245` package.

### `UAT-UND-53-03` Real-file workload (fresh exports, counts only)
* **Story/AC:** UND-53 AC 3, UND-55 (cost).
* **Command:** hydrate, detect, run SQLMesh through `merchant_candidates` and `offered_categories`, query counts, delete the run.
* **Result:** Pass. 87 offered categories (4,906 labelled Monarch records); 819 distinct merchants covering 5,034 records (475 with one record, 35 with more than 20). That is 819 fit requests plus 3 per merchant needing naming. No live Jev call was made; the owner's go-ahead and key are needed, and the quality of the placements (and whether Venmo/Zelle land in the wire-transfer name) is for the owner to judge on the acceptance run.

* **Phase 4 UAT verdict:** **PASSED** for the SQL inputs and the stages with doubles. Open: a live Jev trial on a small sample; persistence of the decision rows (controller, Phase 5).

*Self-check: rubric UAT: COVER=A STEPS=A FAIL=A DATA=A EVID=A (phases 1 to 4; the plan grows with each phase).*

## 6. Phase 5 test plan: JSONL result and summary (UND-54)

### Coverage by layer

| Layer | What it proves | Evidence | Why this layer |
|---|---|---|---|
| Unit / model | Source validation, account selection and period boundaries, one-to-one purchase/transfer rules, refund candidate rules, Jev probability boundaries and off-list answers, category reuse, decision persistence | `test_sources.py`, `test_pairing.py`, `test_transfers.py`, `test_refunds.py`, `test_categorize.py`, `test_decisions.py`; SQLMesh fixtures | Deterministic rules belong here; CLI runs would obscure boundary failures and multiply runtime. |
| CLI unit | Python forwards parsed paths, period and account to the controller, emits result JSON, and returns exit 1 for run failures or exit 2 for preflight refusals | `test_etl_cli.py`; Node option parsing in `tests/cli.test.js` | Replace only the controller boundary with an `AsyncMock`; do not launch MCP/SQLMesh or contact Jev to verify argument wiring. |
| Controller integration | Real MCP source processes, real SQLMesh/DuckDB, stored decision tables, final JSONL and summary, confidence joins, transfer exclusions, identical bytes, and failure cleanup | Existing shared `ControllerTests` run and `FailureTests`; Jev double is the external-service boundary | Persistence, SQL generation, subprocess arguments and publication require the real components. Multiple assertions share one happy-path run. |
| Volume | 4,700 synthetic opposite-sign pairs produce 4,700 rows and reuse one merchant decision 4,699 times | Existing `ScaleTests` | One representative volume run; not a duplicate of every business-rule case. |
| CLI process smoke | The actual Node-to-Python bridge preserves exit 2 on missing input, without a traceback or paid request | Existing `tests/cli.test.js` Python bridge case; `bobp make run` refusal below | Confirms process/import/exit wiring that mocked argument tests cannot establish. |
| Live owner acceptance | Actual Jev quality for real payees, refund choices and categories | Held for owner direction | Doubles prove contracts and deterministic handling, not the quality of Jev judgments. |

No browser coverage is relevant to this CLI. No new end-to-end success or scale run is added for UAT: reuse the existing integration/volume tests, add only uncovered unit assertions. The Python Make target currently runs all Python tests and has no supported file/pattern filter; its invocation necessarily includes existing integration cases. This is a tooling limitation, not a reason to add more full-system tests. JavaScript and SQLMesh suites passed before handoff and are unchanged in this UAT increment; reuse their 302/29 passing results. Run the configured `lint` gate after test edits; it covers JavaScript, while Python currently has no configured linter.

### `UAT-UND-54-01` One JSONL record, links, source rows and confidence
* **Story/AC:** UND-54 AC 1; UND-52 AC 2; UND-53 AC 2.
* **Preconditions:** temporary synthetic `Files` fixture in `test_controller.py`: 13 Monarch rows, 7 Amex rows, original headers; Jev double only.
* **Command:** `bobp make test-py` (`ControllerTests`).
* **Expected:** 12 result records after excluding one earlier Monarch row and merging seven pairs; 6 purchases, 2 transfer legs, 1 external transfer, 2 refunds, 1 credit. Paired records carry both original source rows; single-source records carry a null counterpart. Transfer links are reciprocal. Store refund links to the earlier 45.00 charge with confidence 0.8; a placed existing category also carries confidence 0.8.
* **Result:** Pass, 2026-10-27 22:51:32: Python suite 81/81, including category confidence 0.8. The assertion shares the existing controller fixture; no additional integration scenario was added.

### `UAT-UND-54-02` Summary totals agree with the fixture
* **Story/AC:** UND-54 AC 2; UND-51 AC 2, 4.
* **Command:** `bobp make test-py` (`ControllerTests.test_the_summary_counts_without_naming_transactions`).
* **Expected:** 12 records; 2 paired transfer legs totaling 1,000.00 across both legs; external savings payee count 1; net spending 661.20 after refunds, excluding transfers; 1 direct and 1 Jev-chosen refund; MCC-named category listed; transaction descriptions excluded from summary.
* **Result:** Pass in the 81-test UAT run. Summary arithmetic and counts match the synthetic fixture. Prior 29/29 model-test evidence is reused for unchanged SQL.

### `UAT-UND-54-03` Repeat output is byte-identical and scale reuses decisions
* **Story/AC:** UND-54 AC 3; UND-53 AC 3.
* **Command:** `bobp make test-py` (`ControllerTests.test_a_rerun_with_the_same_files_and_answers_is_byte_identical`, `ScaleTests`).
* **Expected:** result.jsonl and summary.json match byte for byte between identical inputs/answers, including a relative output path; 4,700 synthetic pairs produce 4,700 records with one Jev request and 4,699 reused decisions.
* **Result:** Pass in the 81-test UAT run: byte-identical JSONL and summary; 4,700-pair run 18.40 seconds. Pre-handoff time was 18.54 seconds. The current target repeated this existing volume case because it lacks filtering, not because UAT required another scale scenario.

### `UAT-UND-54-04` Destination and CLI options reach the controller
* **Story/AC:** UND-54 AC 4; UND-50 AC 6.
* **Commands:** `bobp make test-py` (`CliTests.test_options_reach_the_controller_and_success_is_json`); prior passing Node CLI option test.
* **Expected:** `--monarch`, `--amex`, `--out`, `--since 2026-01-01`, `--amex-account Platinum` reach the Python controller unchanged except typed paths; stdout is one JSON result and exit 0. The existing controller integration proves a supplied temporary destination receives actual files; the CLI unit test proves forwarding rather than rerunning the pipeline.
* **Result:** **FAIL, DEF-UND54-01.** Option forwarding passes, but the same AC prohibits private output in tracked folders or `data/`, while production preflight checks only writability. Unit regression `CliTests.test_output_in_a_tracked_source_directory_is_refused_without_starting_the_controller` supplies tracked `src/` as `--out` and stubs the controller, so no source-tree output is written. Actual exit **0**, expected **2**; controller invocation is accepted. Reproduced 22:54:36 in `bobp make test-py`: 82 tests, 81 passed, 1 failed. Successful live Jev invocation through the Make front door remains an owner acceptance step.

### `UAT-UND-54-05` Preflight refusal leaves sources unread and output untouched
* **Story/AC:** UND-54 AC 5.
* **Commands:** `bobp make test-py` (`CliTests.test_a_read_only_directory_is_refused_before_source_validation`, existing non-directory/missing-source/bad-date cases).
* **Expected:** a real chmod 0555 directory and a child below it are refused with `cannot write`, exit 2, before source validation or constructing Jev; directory remains empty and permissions restored during cleanup. A regular-file destination is also refused. Root skips the permission test because it bypasses POSIX permissions.
* **Result:** Pass in the 81-test UAT run, with no skips: real read-only directory refusal occurs before source validation, no output is created, permissions restored. This verifies filesystem permissions, not the separate destination-policy rule in AC4.

### `UAT-UND-54-06` Failed stages publish nothing and errors retain their exit codes
* **Story/AC:** UND-53 AC 4; UND-54 output integrity.
* **Command:** `bobp make test-py` (`FailureTests`, `CliTests.test_a_controller_failure_is_exit_one_with_one_actionable_error_line`).
* **Expected:** Jev failure leaves no result or summary; a failure after writing staged JSONL removes result.jsonl.part as well and marks `failed_stage: output` in run.json. Python CLI returns 1 and exactly `understudy: Jev unavailable` on stderr for a controller failure, with empty stdout. Missing-source CLI process returns 2, no traceback, no run files.
* **Result:** Pass in the 81-test UAT run; the existing real SQLMesh/output cleanup checks pass, with the CLI error-format assertion added at unit level.

### Phase 5 gate evidence
* Python acceptance increment at 22:51:32: `Ran 81 tests in 84.322s`, `OK`, no skips. Final regression run at 22:54:36: `Ran 82 tests in 84.444s`, `FAILED (failures=1)`, no skips. Failure: `AssertionError: 0 != 2 : private run output must not be accepted under tracked src/`. Captured log: `agents/trin/phase5_destination_regression.log`.
* Project lint at 22:52:14: `bobp make lint`, exit 0, no ESLint findings. This configured gate covers JavaScript; Python has no configured lint target.
* Make-front-door refusal smoke: deferred because UAT halted on the destination-policy defect. Prior actual Node-to-Python refusal test passed in the 302-test JavaScript suite.
* Judge trace: no `judge-trace` target listed in this worktree. No trace audit or UAT pass claimed; address the unavailable target before eventual pass sign-off.
* Owner acceptance: live Jev judgments and private-data quality remain unverified by this synthetic gate.

### Defect and next gate

| Defect | Severity | Requirement / reproduction | Diagnosis | Next action |
|---|---|---|---|---|
| DEF-UND54-01 | Major | UND-54 AC4; unit test accepts `--out <checkout>/src`, actual 0 versus expected 2 | Shared `_check_writable` in `src/etl/controller.py` verifies existence/directory/OS permission only; it has no destination-policy restriction. Both CLI and direct controller use it. | Neo: after diagnosis confirmation, reject project `data/` and tracked/unignored project destinations, preserve ignored build and owner-specified external destinations, including resolved-path checks. Retain the failing unit regression and add permitted/forbidden/symlink boundary tests at unit level before one integration smoke. |

**Re-run 2026-10-29 (DEF-UND54-01 fixed):** `_check_destination_policy` in `src/etl/controller.py` refuses `data/` and any project path that `git check-ignore` does not ignore (resolved paths, so symlinks into `src/` are caught); ignored `build/` and outside paths pass. The failing regression now passes, and `test_destination_policy_boundaries` covers data/, tracked `tests/` and `docs/`, ignored `build/runs`, an outside path and a symlink into `src/`. `bobp make test-py`: 83 tests OK (4,700-pair synthetic run 20.03 s); `bobp make lint` exit 0. UND-54-04 now **Pass**. Live Jev and real-file acceptance stay with the owner (Task C.3).

**Phase 5 UAT original verdict: FAILED (superseded by the re-run above).** No production edits made during QA. No private inputs or live Jev calls. Handoff to Neo for the targeted fix; Smith/Morpheus approval and task 5.2 completion remain pending. `rubric UAT: COVER=A STEPS=A FAIL=S DATA=S EVID=A` describes the test plan, not product acceptance.
