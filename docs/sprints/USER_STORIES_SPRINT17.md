# Sprint 17 User Stories: Dedupe, transfers, refunds and new categories

*   **Total Points**: 27 (Tier 1)
*   **Branch**: `sprint-17` (to be cut from `main` once Sprint 16 is merged)
*   **Source**: owner, 2026-10-17 to 2026-10-27, recorded in `agents/CHAT.md` and `agents/morpheus/state.md`: reproduce the household transaction-cleaning procedure with understudy, starting from a Monarch export and an Amex export that overlap.
*   **Builds on**: Sprint 16 (`USER_STORIES_SPRINT16.md`). Its reconciliation matches only same-sign rows (26 matches on the owner's real files); these stories add the sign-flipped match (4,229 of 4,321 Amex rows), transfers, refunds and new category names.
*   **Platform**: the owner decided on 2026-10-27 that understudy moves to Python for all (`agents/cypher/platform_decision_2026-10-27.md`). The port is a separate epic; where these stories say "source server" and "sketch", the language they run in is for the architecture to settle.
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

When this sprint is done, the owner can point understudy at their Monarch and Amex exports and get back one JSONL file in which every transaction appears once, every transfer between accounts is paired and kept out of spending, every refund points back to the merchant it came from, and every merchant has a category. Jev makes the judgments (does this merchant fit an existing category, which new name fits) and code does the arithmetic and matching. It matters now because the two exports overlap by thousands of rows and the owner cleans them by hand today.

## Assumptions made for the owner

1. **Two sources only.** Monarch (14,522 rows, 2023-12-30 to 2026-10-17, six accounts) and Amex (4,321 rows, 2026-01-01 to 2026-10-16). Monarch rows for the other accounts (Ridgewood, Citi, Student Advantage and so on) are read and reconciled, but there is no export for them to merge with. If wrong: a third source needs its own source server, the same shape as the first two.
2. **Match rule for the same purchase:** same date and same amount with the sign flipped (Amex charges are positive, Monarch's are negative). In the real files 4,229 of 4,321 Amex rows match this way. If wrong: Morpheus widens the rule (a day either side, or the statement text).
3. **A transfer pairs on opposite amount in a different account within 3 days.** In the real files 43 of 70 rows Monarch labels "Credit Card Payment" pair this way. Monarch's own transfer labels are inconsistent ("Food & Dining: Credit Card Payment", "Transportation: Transfers"), so the label alone does not decide. If wrong: the window or the rule changes, the stories do not.
4. **A refund with no findable original charge** (for example the purchase was before 2026-01-01) still counts against its merchant, without a link. If wrong: such refunds go to the review list instead.
5. **One Jev decision per distinct merchant**, reused for every row of that merchant in the run, so cost follows the number of merchants, not rows. If wrong: cost grows with rows.
6. **Nothing is written back** to Monarch or Amex. The result is a new file.

---

## STORY-UND-49: Read my Monarch and Amex files as JSONL
**Points:** 3

**As the** owner, **I want** each export to be served as JSONL records by its own source server, **so that** understudy reads them like any other app it plays and later sources (a sheet, another bank) can be added the same way.

### Acceptance Criteria
1. A Monarch source server and an Amex source server each offer a tool that returns that export's rows as JSONL, one record per row, keeping every column of the file.
2. Each record says which source it came from and which row of the file it was, so any result can be traced to its original row.
3. Run against the real files, the Monarch server returns 14,522 records and the Amex server returns 4,321 (an Amex row whose details span several lines is still one record).
4. A file that does not exist, or whose columns are not the expected ones, stops the run before anything is read, saying which file and which column is wrong. Nothing is written.
5. The repository holds no household data: tests use small made-up files with the same columns, and `data/` is ignored by git.

---

## STORY-UND-50: One record per purchase
**Points:** 5

**As the** owner, **I want** a purchase that appears in both exports to become one record, **so that** my spending is counted once.

### Acceptance Criteria
1. An Amex row and a Monarch row on the Amex card with the same date and the same amount (signs opposite) become one record that carries both source rows.
2. Against the real files, 4,229 of the 4,321 Amex rows are matched; the other 92 are listed as unmatched with their date, description and amount, and still appear once in the result.
3. Two real purchases with the same date and amount (two coffees at $4.50) stay two records: each source row is matched at most once, to one counterpart.
4. A Monarch row that has no Amex counterpart (any other account, or an Amex row from before the export began) appears once, unchanged.
5. Running the same files twice gives the same matches.

---

## STORY-UND-51: Transfers paired and kept out of spending
**Points:** 5

**As the** owner, **I want** a payment from one account to another, such as a Ridgewood debit paying the Amex bill, recognised as a transfer, **so that** it is not counted as spending on either side.

### Acceptance Criteria
1. Two records in different accounts, with opposite amounts, within 3 days of each other and described as a payment or transfer, are linked to each other and both marked as a transfer. Neither is deleted.
2. Marked transfers are left out of the spending summary; the summary says how many transfers and what total they carry.
3. Against the real files, 43 of the 70 rows Monarch labels "Credit Card Payment" are paired. The other 27 appear in a review list with date, account and amount, and are not counted as spending until reviewed.
4. A refund is never marked as a transfer: Amex's 114 credits that are not payments stay as spending credits.
5. Two payments of the same amount in the same week pair one-to-one, not both to the same partner.

---

## STORY-UND-52: Refunds go back to the merchant
**Points:** 3

**As the** owner, **I want** a refund tied to the purchase it reverses, **so that** a merchant's spending shows what I actually paid.

### Acceptance Criteria
1. A refund is linked to an earlier charge from the same merchant whose amount is at least the refund's; the record shows the link and the merchant's spending falls by the refund.
2. When more than one earlier charge could be the original, Jev is asked to choose among them, and the record shows which one it chose and how sure it was.
3. A refund with no earlier charge in the data still counts against its merchant, marked as having no original charge, and is listed in the run summary.
4. A refund is never linked to a charge dated after it.

---

## STORY-UND-53: Every merchant gets a category, and a new one when none fits
**Points:** 8

**As the** owner, **I want** each merchant placed in one of my Monarch categories, and given a new category only when none fits, **so that** the result is categorised without me labelling merchants one at a time.

### Acceptance Criteria
1. For each distinct merchant, Jev is asked whether it fits any of the existing 180 Monarch categories; an answer below 0.3 sends the merchant to naming, above 0.7 to choosing among the existing categories, and between the two to the review list.
2. A merchant that fits is placed in the one existing category Jev chooses; the record shows the category and Jev's confidence.
3. A merchant that does not fit goes to a naming step in the sketch: Jev chooses a group and then a name from the MCC (ISO 18245) description list, and for each candidate name a yes or no question, judged against a written rubric, confirms it is a good name. The merchant is given the best name above 0.7; if none passes, it goes to the review list.
4. Once a new category is named it is available to every later merchant in the run, and the run lists the new categories it created and which merchants are in each.
5. The run never makes up a category name: every name in the result is either one of the 180 or one from the MCC list.
6. Jev is asked once per distinct merchant; the summary says how many Jev decisions were made and how many were reused.
7. If Jev cannot be reached, the run stops, says so and writes no result.

---

## STORY-UND-54: A reconciled JSONL file and a summary
**Points:** 3

**As the** owner, **I want** the run to end with one JSONL file and a short summary, **so that** I can check the result and use it elsewhere.

### Acceptance Criteria
1. The result is JSONL, one record per transaction, each with its date, amount, merchant, category, whether it is a transfer or a refund, links to its counterpart, and every source row it came from.
2. The summary says: records read per source, records in the result, duplicates merged, transfers paired, refunds linked, merchants categorised, new categories created, Jev decisions made, and the sizes of the review lists.
3. Re-running on the same files with the same Jev answers gives byte-identical output.
4. Run from `bobp make run`, and the result and summary are written under `build/` or a path the owner gives, never into `data/` or a tracked folder.
5. If the output path cannot be written, the run says so before reading anything and changes nothing.

---

## Out of Scope
- Google Sheets (or any MCP sheet source or sink); the source servers are written so one can be added later.
- Calendar de-duplication, trip grouping, travel tagging and merchant consolidation from the owner's procedure: later sprints.
- Exports for the Ridgewood, Citi and Student Advantage accounts (their rows come only from Monarch).
- Writing categories back to Monarch, and promoting learned categories or merchant rules for future runs.
- Amex history before 2026-01-01 (the export does not have it).
- Letting Jev write category names: it chooses only from the 180 and the MCC list.

## Open Questions
1. **Jev call limit.** Is there a number of Jev decisions per run that should stop it? Owner. Assumed: the start of the run shows how many distinct merchants it will ask about, and there is no hard cap.
2. **The 27 unpaired card payments.** Left for review, as written. Owner can say whether to treat them as transfers anyway. Assumed: review.
3. **Scale.** The owner's earlier boundary was about 4.7k rows; Monarch is 14.5k. Morpheus to confirm the design is comfortable at that size. Assumed: yes.
4. **MCC list source and licence.** Morpheus to verify before the sprint depends on it. Assumed: freely usable.
