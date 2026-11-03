# Sprint 23 User Stories: household numbers you can trust, and a run that tells its story

*   **Planning Size** (optional): 23 points
*   **Branch**: `sprint-23`
*   **Source**: Owner, 2026-11-02 (`OWNER_DECISIONS_SPRINT22.md` 4-8, made after the 2026-11-02 household run); `OLD_VERSION_PARITY.md` for UND-81.
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

When this sprint is done, the household run's income, expenses and net spending for an account match the owner's own hand-edited export, because money moved between the owner's accounts is no longer counted as income, refund or spending. Merchants Jev is unsure about arrive as a short per-merchant list, and the owner's answers are kept and used on the next run so the same merchant is never asked about twice. The run's event stream also carries the machine's states and decisions, so the console can draw and replay a run in Sprint 24.

**Order.** UND-89 first (the other household stories read its kinds). UND-90 and UND-91 follow, then UND-92 (it reads UND-91's list). UND-81 is independent and can go any time after UND-89.

## Assumptions made for the owner

1. The baseline is `data/Transactions_2026-11-02T19-14-07.csv` (decision 8). For Ridgewood checking it gives income $363,349 and expenses $205,042 once Transfer and Credit Card Payment are set aside.
2. "Income" means money in and "expenses" means money out, for records that are not transfers. Refunds the owner categorized as Refund count as income, as the owner's own total does.
3. The owner's category wins in both directions: a record the export does not call Transfer or Credit Card Payment is not a transfer, even if the matching rule would pair it.
4. A pin names one merchant and one category from the taxonomy the run already uses. A pin never carries free text.
5. Typed inputs (decision 4) are wanted and stay in Sprint 24 with the YAML editor; the statechart diagram, stepping and replay also stay in Sprint 24. Only the event stream they need is here.

---

## STORY-UND-89: Transfers come from the owner's categories
**Points:** 5

**As the** owner,
**I want** a record my export labels Transfer or Credit Card Payment to be treated as a transfer,
**so that** savings I move into checking never show up as income, refunds or spending.

### Acceptance Criteria
1. Every record whose export Category is Transfer or Credit Card Payment has kind transfer in the run's output, whatever merchant it matches.
2. On the baseline file, none of the 244 Ridgewood records has kind purchase, refund or credit while its Category is Transfer or Credit Card Payment; the Charles Schwab deposits are transfers.
3. A record whose export Category is anything else never has kind transfer.
4. The run's summary says how many records changed kind because of the export's category.
5. If the Monarch file has no Category column, the run stops before any Jev request and says the column is missing.

---

## STORY-UND-90: Income and expenses I can check
**Points:** 3

**As the** owner,
**I want** the run's summary to give income, expenses and net for each account,
**so that** I can compare it with my own spreadsheet without opening the records.

### Acceptance Criteria
1. The summary lists, for each account, income (money in), expenses (money out) and net, none of which count transfers.
2. For Ridgewood on the baseline file, income is $363,348.62 and expenses is $205,042.27, equal to the cent to the baseline's own sums.
3. The summary also gives one net-spending figure across all accounts, with the same rule.
4. An account with no records in the run's period is left out, not shown as zero.

---

## STORY-UND-91: Merchants for review, as a list
**Points:** 5

**As the** owner,
**I want** the merchants Jev was unsure about written as one line each,
**so that** I decide about a few hundred merchants and not thousands of records.

### Acceptance Criteria
1. The run writes `review.jsonl` with one line per merchant that has any record for review.
2. Each line has the merchant's name, its number of records, its total amount, Jev's top two categories with their probabilities, and why it needs review (below 0.7, or none of these).
3. Lines are sorted by number of records, largest first.
4. The number of lines equals the number of distinct merchants among the records with status review.
5. When nothing needs review the file is written and is empty.

---

## STORY-UND-92: Pinned categories are kept
**Points:** 5

**As the** owner,
**I want** a category I choose for a merchant to be used on every later run,
**so that** Jev is never asked about that merchant again.

### Acceptance Criteria
1. A run reads a pin file, one line per merchant naming a category, from `--with pinned=<path>`; when no path is given it reads `.understudy/pinned.jsonl`.
2. A pinned merchant's records are placed in its pinned category, show they were pinned, and cause no Jev request.
3. A merchant that is pinned does not appear in `review.jsonl`.
4. If the default pin file does not exist, the run has no pins and says so; if a path given with `--with` does not exist, the run stops and names it.
5. A pin naming a category not in the taxonomy, or a line missing a merchant, stops the run before any Jev request and names the line.
6. Two runs with the same pins and the same files place the same merchants the same way.

---

## STORY-UND-81: The run tells its story
**Points:** 5

**As the** owner,
**I want** a run's event stream to record its states, the event behind each move and each decision,
**so that** the console can later draw the run and replay it from the log.

### Acceptance Criteria
1. The first line of a run's event stream (`run_started`) lists the sketch's states and the events between them.
2. Every move to a new state is a line naming the state and the event that caused it.
3. Every decision is a line giving its stage, its options, what removed or held each option, and the pick with its probability.
4. A run that ends records how it ended, including a failure and its message.
5. The console's description of a run says whether its log has the story (`story: true`) or not (`story: false`, for a log written before this sprint); nothing is rewritten, and the console shows a log without a story as it does today. (Amended during Phase 5: showing old logs as unreadable would have hidden every existing run for no gain until the Sprint 24 diagram needs the story. The owner is told.)

---

## Out of Scope
- The statechart diagram, step-by-step control, replay of a log, decision detail and the YAML editor (Sprint 24).
- Typed inputs: dial, faders, stepper, switches (Sprint 24).
- Changing the 0.7 threshold or the taxonomy's odd group names; the owner may adjust them later.
- A console button to promote review lines into pins; the owner edits the pin file for now.
- A target for how many records land in review (decision 8: none).
- TLS for the console (SEC-005 accepted until 2027-01-30).

## Open Questions
1. Do the odd taxonomy groups (Tiffany & Co. under Food & Dining: Department Stores) need their own fix? Owner; assumed no until the review list shows how much they cost.
