# Sprint 16 User Stories: Staged local ETL with Jev-guided categories

*   **Total Points**: 18 (Tier 1)
*   **Branch**: `sprint-16`
*   **Source**: owner, 2026-10-17: reproduce the household transaction-cleaning procedure with understudy, starting from a Monarch export and an Amex export that overlap; recorded in `agents/CHAT.md` and `agents/morpheus/state.md`.
*   **Status**: Built and accepted (UAT and Morpheus review passed for phases 1 and 2); closeout in progress.
*   **Reconstruction note**: the originally approved text of this file was overwritten on 2026-10-27 and is not recoverable from git. This version was rebuilt from `ARCH_SPRINT16.md`, `UAT_PLAN_SPRINT16.md`, `task.md` and `agents/*/state.md`. The story IDs, scope and acceptance-criteria numbering follow the UAT plan; the wording and the point split (5, 8, 5) are Cypher's reconstruction, not the original.

## Goal

When this sprint is done, the owner can point understudy at their Monarch and Amex CSV exports and get a local review file in which the overlapping transactions are reconciled with their source rows kept, and every merchant has a category chosen by Jev from a fixed list. It runs on the owner's own machine, handles about 4,700 reconciled transactions, and keeps the private files out of git and chat.

## Assumptions made for the owner

1. **Reconciliation key is date plus amount, same sign, first slice only.** A pair is made only when a key occurs exactly once in each source; anything else stays separate and visible. If wrong: a better rule is a later story (planned in Sprint 17).
2. **Categories come from a fixed taxonomy of 46 category/subcategory pairs, always including `Misc / Other or not yet classified`.** If wrong: the taxonomy is data in a YAML file and can be replaced without changing the run.
3. **Jev is asked once per distinct merchant, not once per transaction**, and its choice is reused for every row with that merchant in the run. A new run may choose differently.
4. **Input is the two CSV files**; the flat JSONL records the run makes internally are not an input format.

---

## STORY-UND-46: Reconcile my Monarch and Amex exports
**Points:** 5

**As the** owner, **I want** the two exports read, checked and reconciled, **so that** a transaction that appears in both is recognised and nothing is lost or wrongly merged.

### Acceptance Criteria
1. Given a Monarch CSV and an Amex CSV, the run checks the required columns, keeps an untouched copy of each file for that run, and turns every row into one record that keeps its source, its row number and its original columns.
2. A transaction whose date and amount occur exactly once in each source becomes one reconciled row carrying both source rows.
3. A row that has no counterpart is kept unchanged; a date and amount that occurs more than once on either side stays as separate rows marked ambiguous, and no pairing is chosen by row order.
4. A missing or unreadable file, or a file missing a required column, stops the run before anything is created and names the source and the column; an incomplete command line says which input is missing and exits with code 2.

---

## STORY-UND-47: Jev places each merchant in a category from my list
**Points:** 8

**As the** owner, **I want** each distinct merchant placed in one category from a fixed list, **so that** the result is categorised without me labelling merchants one at a time.

### Acceptance Criteria
1. Jev is asked about distinct merchants only, with each merchant's description, transaction count and the offered category/subcategory pairs; rows with the same merchant are consolidated before a request is made.
2. Jev can choose only an offered pair; the chosen pair, Jev's confidence and the model are kept with the run.
3. An accepted choice is applied to every row with that merchant without asking again, and each result row still shows both of its source rows.
4. An empty answer or a pair that is not on the list becomes `Misc / Other or not yet classified` and is marked for review; it is never saved as free text.

---

## STORY-UND-48: A review file and a summary I can check
**Points:** 5

**As the** owner, **I want** a local review file and a summary at the end of the run, **so that** I can see what was matched, what was categorised and what needs my attention.

### Acceptance Criteria
1. The review file lists every reconciled row with its category, its match status and its source rows and original values.
2. The summary reports rows read per source, reconciliation counts (matched, unmatched, ambiguous), classified count, `Misc` count and review-required count, without printing transaction contents or account identifiers.
3. The run's files (copies of the inputs, the working database, logs, the review file and the summary) are written under `build/runs/<run-id>/`, which git ignores.
4. A run of 4,700 matching pairs across both sources (9,400 rows) with five repeated merchants completes locally, with the five merchants asked about in one request.
5. If a stage fails, including Jev being unreachable, the run is marked failed at that stage and no summary or review file is written that could be mistaken for a complete result.

---

## Out of Scope
- Google Sheets, MCP sources or sinks, and arbitrary or nested JSONL input.
- Matching with the sign flipped, pairing transfers between accounts, linking refunds, and naming new categories (planned in Sprint 17).
- Fuzzy merchant merging, and learning merchant mappings across runs.
- Live Jev calls on private data inside the automated tests (they use synthetic CSVs and a Jev double).
- Writing anything back to Monarch, Amex or a spreadsheet.

## Open Questions
1. **Owner review of the category comparison.** On 2026-10-18 Neo compared Jev's categories to the owner's workbook (4,666 of 4,672 transaction IDs matched; the workbook's own `Category` and `Category_Ontology` columns disagree on 2,522 rows). The owner has not yet chosen a baseline or a crosswalk. Assumed: not needed to close this sprint.
