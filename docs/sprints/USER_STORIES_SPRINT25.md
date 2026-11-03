# Sprint 25 User Stories: the tool fixes the categories, and payments know what they paid for

*   **Planning Size** (optional): 29 points
*   **Branch**: `sprint-25` (cut from `sprint-24`, which is not merged yet)
*   **Source**: Owner, 2026-11-03 (`OWNER_DECISIONS_SPRINT22.md` 10 to 13b: the export's categories are a mess and the tool should fix them; the ISO 18245 list is the clean taxonomy; the owner's own entries are allowed where ISO has no good match; connect lump-sum payments to the merchants they paid; Venmo and Zelle later)
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

When this sprint is done, every merchant in the household run has one category from a clean list (the ISO 18245 merchant categories plus the owner's own entries) chosen by the tool, not copied from Monarch or Amex, and the owner can correct any of them with a pin. Each credit card payment shows which charges it settled and what they were for, so the report says what the lump sums bought. The household's spending list is built from the tool's categories.

**Order.** UND-96 first (the list). UND-97 reads it. UND-98 and UND-99 read UND-97's categories; UND-99 also reads UND-98's transfers. UND-100 last.

## Assumptions made for the owner

1. The branch is stacked on `sprint-24` because it is not merged; merging both in order is the owner's call.
2. The taxonomy is the 13 ISO groups and 280 names already in `src/sketch/mcc.py`, plus a shipped starting file of the owner's additions under a "Household" group: Rent, Mortgage, Tuition, Income, Transfer and Loan repayment (decision 12). The owner copies and edits that file; Jev never writes a name.
3. Jev chooses in two steps, a group and then a name in it (the list is too long for one question), the way new categories are named today. A merchant that fits nothing, or where Jev is unsure (0.7 or below), goes to the review list.
4. The export's own `Category` is not shown to Jev, does not choose a category, and does not decide a transfer. It is only compared with the tool's answer, in a disagreement report, so the owner can see where they differ.
5. A transfer is a record the run links as the two halves of a payment, or whose payee's category is "Household: Transfer"; the owner's pins override Jev.
6. A payment settles the card's charges oldest first until its amount is reached, never past it; credits (refunds) stay with their refund link and are not part of the allocation. On the baseline Amex file this puts 11 of 12 payments within $832 (4.6% at most); the first payment mostly pays the earlier balance and stays partly unexplained, with its amount shown.
7. No figure is promised for Ridgewood income and expenses this sprint: they now depend on Jev's categories, so the UAT reports how far they are from the owner's earlier file ($363,349 and $205,042) and which payees account for the difference.
8. Venmo and Zelle histories, stepping and pause, replay of a log, decision detail and the editor are not in this sprint.

---

## STORY-UND-96: A clean list of categories
**Points:** 5

**As the** owner,
**I want** one list of categories made of the ISO 18245 merchant categories and my own entries,
**so that** every merchant can be put in a category that means the same thing every time.

### Acceptance Criteria
1. The list has every ISO 18245 group and name in use (13 groups, 280 names) plus each entry of the owner's additions file, each written "Group: Name".
2. A starting additions file ships with the household sketch with Rent, Mortgage, Tuition, Income, Transfer and Loan repayment under the group "Household".
3. `--with additions=<path>` uses the owner's file instead; a path that does not exist stops the run and names it.
4. An additions line with no group or no name, or one that repeats an ISO name or another addition, stops the run before any Jev request and names the line.
5. A pin names a category in this list; a pin naming anything else stops the run before any Jev request and names the line and the category.

---

## STORY-UND-97: The tool puts every merchant in a category
**Points:** 8

**As the** owner,
**I want** Jev to choose a category from the clean list for every merchant,
**so that** the messy categories from Monarch and Amex stop mattering.

### Acceptance Criteria
1. Each merchant gets one category from the list, chosen by Jev in two steps (a group, then a name in it); Jev never writes a category.
2. A merchant is placed when each choice is above 0.7, or at least 0.4 and at least twice as sure as the runner-up; otherwise it is for review, with Jev's best guess, its probability and the reason (`below_0.7` or `none_of_these`). (Amended in Phase 2: on the first real run a long list spread Jev's probability, so right answers such as MTA at 0.67 and FreshDirect at 0.67 fell under 0.7 and 73% of records went to review.)
3. The export's own Category is not shown to Jev, is not offered as an option and does not change the answer: the run asks Jev the same questions for the same merchants whatever the export's categories say.
4. A pinned merchant is placed in its pinned category, is never asked about, and is not in the review list.
5. `review.jsonl` is still one line per merchant, most records first, with the best guess and the reason.
6. Every record carries its merchant's category (or none, when for review) and whether it came from Jev or a pin.

---

## STORY-UND-98: Kinds and the report follow the tool's categories
**Points:** 5

**As the** owner,
**I want** transfers to come from the links between payments and from the tool's categories, not from Monarch's labels,
**so that** a messy label can never turn a card payment into income or a purchase into a transfer.

### Acceptance Criteria
1. A record is a transfer when the run links it to a record in another account as the two halves of a payment, or when its merchant's category is "Household: Transfer"; the export's label never decides.
2. A merchant the owner pins to "Household: Transfer" makes its records transfers; a merchant pinned elsewhere never does (unless linked).
3. The records the run tries to link are chosen from their own text (payment words in the description, statement or payee, and the card export's payment lines), never from the export's Category; a bank-side payment whose Category says something misleading (for example an income label) still links to its card-side payment received, and neither half counts as income or spending.
4. The run writes `crosswalk.jsonl`: one line per merchant with its records, its money, the export's most common category and the tool's category side by side, biggest first, and a flag where the two differ about money moving (the tool says transfer and the old label rule says not, or the reverse); the summary counts the flagged merchants. (The two systems use different words, so every merchant's words differ; the flag marks the ones that change what is counted. Amended at Gate 2.)
5. The summary says Ridgewood income and expenses (transfers left out) so the owner can compare them with the earlier file; no figure is promised.
6. A merchant for review is not a transfer by guess: until it is placed or pinned, its records stay purchases or credits and are listed as unplaced.

---

## STORY-UND-99: Payments know what they paid for
**Points:** 8

**As the** owner,
**I want** each credit card payment tied to the charges it settled,
**so that** the report shows what the lump sums were for.

### Acceptance Criteria
1. For each payment on a card (a transfer linked to the card's "payment received"), the card's charges are allocated to it oldest first until its amount is reached, never past it; a charge belongs to at most one payment.
2. The run writes `payments.jsonl`, one line per payment: its date, card, amount, how many charges it settled, the amount settled, the remainder (amount minus settled), and the five largest categories among the settled charges with their amounts and shares.
3. Each charge record says which payment settled it, or that it is still open.
4. The summary gives the open balance: the charges after the last payment, their count and amount.
5. A payment with no earlier unsettled charges (the first in the export) shows a remainder equal to its amount and says it is partly unexplained; it does not borrow charges from after its date.
6. On the baseline files, every payment after the first settles within 5% of its amount, and the settled amounts plus the open balance equal all the card's charges to the cent.
7. A card with no payments gets no `payments.jsonl` lines and all its charges are open.

---

## STORY-UND-100: Spending by the tool's category
**Points:** 3

**As the** owner,
**I want** the spending list built from the tool's categories,
**so that** it says what I really spend on, in one clean list.

### Acceptance Criteria
1. `spending.jsonl` and the console's list use the tool's category for each record (an ISO or Household category); a merchant for review shows as `unplaced`.
2. Transfers, including the card payments themselves, are not spending; the charges they settled are, once each.
3. The shares add to 1 within 0.001 and the amounts add to `spending_total` in the summary.
4. No category from the export appears in the list unless it is also in the clean list.

---

## Out of Scope
- Venmo and Zelle payment histories (the same "a lump becomes its details" idea, next sprint once the files are in hand).
- Stepping, pause, replay of a log, decision detail and the YAML editor (Sprint 26).
- A console button that turns a review line into a pin.
- Removing the old Monarch-label rules from older sketches or docs beyond the household.
- TLS for the console (SEC-005 accepted until 2027-01-30).

## Open Questions
None blocking. Assumption 7 (no figure promised for Ridgewood) is the owner's to overturn once the UAT shows how far Jev's categories are from the earlier file.
