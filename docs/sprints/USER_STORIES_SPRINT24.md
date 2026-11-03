# Sprint 24 User Stories: what the money goes on, typed inputs, and the statechart you can see

*   **Planning Size** (optional): 27 points
*   **Branch**: `sprint-24`
*   **Source**: Owner, 2026-11-02 (`OWNER_DECISIONS_SPRINT22.md` 4 and 9: typed inputs wanted; widen the transfer rule; "I want to know what I'm spending all that money on"); `OLD_VERSION_PARITY.md` rows 1 and 7; the Sprint 23 retro backlog.
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

When this sprint is done, the owner can see what the household money goes on: card payments and moves between accounts no longer count as income or spending, and a ranked list of spending by category appears in the run folder and in the console. The owner can set a sketch's values with the right control (a dial, a fader, a stepper, a switch) instead of typing text. The console draws the sketch's statechart with the current state lit, so a run can be followed as well as read.

**Order.** UND-93 first (UND-94 reads its kinds). UND-94, then UND-95 (the console shows UND-94's file). UND-87 and UND-82 are independent of the household stories and of each other; UND-82 reads the story Sprint 23 added to the event stream.

## Assumptions made for the owner

1. "Card-side labels" means a Category with a group in front that ends in `: Credit Card Payment`, `: Transfer` or `: Transfers` (the forms the earlier categorization wrote), as well as plain `Transfer` and `Credit Card Payment`. In the baseline file that is "Food & Dining: Credit Card Payment" (22 records) and "Transportation: Transfers" (44, of which 29 are Venmo and 10 are Bank Transfer). A few records under those labels are really purchases (Depop, Soho Deli, Levy Restaurants); they will count as transfers until relabeled in Monarch. The labels alone are not enough: the five largest card payments received (Amex "Electronic Payment", $133,047) are labeled as income, so a record that the run links to a record in another account as the two halves of a payment is a transfer too. With both, $20,038 of positive records outside Ridgewood remain, none of them card payments.
2. A record's spending category is the export's own `Category` when it has one, otherwise the category Jev placed it in, otherwise `uncategorized`. The owner's edited categories are the better answer where they exist.
3. Spending means money out of non-transfer records, net of refunds, so a refund lowers its category. Income is not part of the list.
4. Typed inputs: a sketch declares each input's kind (`choice`, `range`, `count` or `switch`), its limits and its default; a value left alone is the default. Inputs a sketch does not declare keep a plain text box.
5. The statechart arrows are labeled with the guard that decides them (`when`); an unguarded move (the event `ok`) has no label, since every arrow would say the same thing.
6. Stepping, pause and resume, replaying a finished run from its log, decision detail and the YAML editor are Sprint 25. Sprint 23 said they were Sprint 24; with the money stories added they do not fit.

---

## STORY-UND-93: Card payments and moves between accounts are not spending
**Points:** 3

**As the** owner,
**I want** records my export labels as card payments or transfers, in any of its forms, to count as transfers,
**so that** they never show up as income or as spending.

### Acceptance Criteria
1. Every record whose Category is `Transfer`, `Credit Card Payment`, or has a group in front and ends in `: Credit Card Payment`, `: Transfer` or `: Transfers`, has kind transfer in the run's output.
2. A record that the run links to a record in another account as the two halves of a payment has kind transfer, whatever its Category.
3. A record that has neither one of those labels nor such a link never has kind transfer.
4. On the baseline file, no record with one of those labels or such a link has kind purchase, refund or credit, and the records outside Ridgewood that are positive and not transfers fall from 169 records ($240,596) to under $30,000.
5. Ridgewood income stays $363,348.62 and expenses $205,042.27.
6. `summary.json` says how many records are transfers by label, by link, and by both.

---

## STORY-UND-94: Where the money goes
**Points:** 5

**As the** owner,
**I want** a ranked list of what I spend on, by category,
**so that** I can see where the money goes without reading five thousand records.

### Acceptance Criteria
1. The run writes `spending.jsonl` with one line per category: its name, how many records, its total amount, and its share of all spending.
2. Lines are sorted by amount, largest first.
3. A record's category is the export's Category when it has one, else Jev's placed category, else `uncategorized`.
4. Spending counts money out of purchases, refunds and credits that are not transfers, with refunds reducing their category; income and transfers are not in the list.
5. The shares add up to 100% within a rounding of 0.1, and the amounts add up to the run's expenses net of refunds in `summary.json`.
6. When a run has no spending the file is written and is empty.

---

## STORY-UND-95: The console shows what the money goes on
**Points:** 3

**As the** owner,
**I want** the console's run summary to list the top spending categories,
**so that** I see the answer when I open the run, without finding a file.

### Acceptance Criteria
1. For a run that has `spending.jsonl`, the summary panel lists the ten largest categories with amount and share, largest first, and says how many more there are.
2. A run without that file shows no such list and no empty heading.
3. The list is readable at 390 px width and in all three themes.
4. A `spending.jsonl` the console cannot read is named in the panel as unreadable, and the rest of the page still works.

---

## STORY-UND-87: The right control for each value
**Points:** 8

**As the** owner,
**I want** to set a sketch's values with a dial, a fader, a stepper or a switch,
**so that** I cannot type a value that makes no sense and I can see its limits.

### Acceptance Criteria
1. A sketch can declare an input with a kind: `choice` (a list of options), `range` (a minimum, a maximum and a step), `count` (a whole number with a minimum and maximum) or `switch` (on or off), and a default.
2. The console shows, for each declared input, a control of its kind with its current value readable, starting at the default.
3. Every control can be used from the keyboard and has an accessible name and value.
4. Pressing Play passes each value the owner set (and the default for each left alone) to the run.
5. A control cannot be set outside its limits, and a sketch whose declaration is wrong (an unknown kind, a default outside the limits, a choice with no options) is refused by `understudy check` with a message naming the input.
6. A value the sketch takes but does not declare keeps a plain text box.
7. The `evening` example declares its mood, weights, party size and evenings-only values.

---

## STORY-UND-82: See the statechart
**Points:** 8

**As the** owner,
**I want** the console to draw the sketch's machine, with the state it is in lit up,
**so that** I can follow a run as well as read its log.

### Acceptance Criteria
1. For a run whose log has the story, the console draws each state as a box, from the initial state downward, with final states double-bordered and an arrow for each move.
2. An arrow that has a guard is labeled with it; arrows with no guard are not labeled.
3. While the run goes, the state it is in is lit, and within one second of a change the light moves to the new state; the move just taken is highlighted.
4. When the run ends, the state it ended in stays lit and the diagram says how it ended.
5. For a run whose log has no story, the panel says so and shows no diagram.
6. The diagram is readable at 390 px width, in all three themes, and every state box has an accessible name (its state and whether it is current).
7. A machine of up to forty states is drawn without boxes or labels overlapping.

---

## Out of Scope
- Step, pause and resume, `run --watch`, replay of a finished run from its log, decision detail, the YAML editor (Sprint 25).
- Fixing mislabeled purchases (Depop, Soho Deli) in the export; the owner relabels them in Monarch.
- Putting income or per-account spending in the list; this is one household list.
- Changing the 0.7 threshold or the taxonomy.
- TLS for the console (SEC-005 accepted until 2027-01-30).

## Open Questions
None blocking. Assumption 1 (which labels count) is the owner's to overturn after seeing the baseline run.
