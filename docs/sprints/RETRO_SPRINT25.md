# Sprint 25 Retro: the tool fixes the categories, and payments know what they paid for

Delivered: UND-96 a clean category list, UND-97 Jev puts every merchant in a category, UND-98 kinds follow links and the tool's categories (with a crosswalk), UND-99 payments tied to the charges they settled (`payments.jsonl`, `settled_by`, `open_balance`), UND-100 spending by the tool's category. Five phases of gates passed; 491 tests, 22 browser tests.

## What went well

* **Real-file UAT found the defects:** merged records carried the bank's date and the order of a day's charges mattered; both only showed on the full Amex file, and both were fixed test-first.
* **Generic parts stayed generic:** `map.allocate`, `map.top`, `map.nest`, `map.share by`, `map.weigh places`, `map.unique`, `map.smallest` know nothing about households; the household only wires them.
* **Owner decisions were recorded as they came** (decisions 10 to 15) and the stories carried the targets that the real data confirmed (11 of 12 payments within 5%, open balance $28,443.67).

## What went wrong

* **Edit-only slipped again** (Neo): one `sed` to tick tasks in `task.md`; the result was right, the habit is not.
* **The init steps were skipped on the first resume** and had to be done afterwards on the owner's correction.
* **A replay is refused after sketch edits**, so a check on the full data can cost a live run (about seven minutes, 2,300 requests).
* **"Unplaced" is 38.6% of spending:** Jev leaves many merchants for review and the owner has not pinned them.

## By persona

* **Neo:** tests first held; friction was the YAML comment rule (`#` in a key must be quoted) and a stage named like its own `into`. **Trin:** UAT on the real files each phase; the allocation sensitivity was found there. **Morpheus:** ADR-0055 to ADR-0057. **Oracle:** two lessons. **Mouse:** six phases of 3 to 4 tasks, sized right. **Cypher:** stories carried measurable targets. **Smith:** gate 1 and 2 earlier; end-to-end acceptance below.

## Backlog (feeds `docs/BACKLOG.md`)

* Owner: pin the own-account merchants (Ridgewood Savings Bank and others) and the $20,000 "Deposit"; work down `review.jsonl` to cut "unplaced" below 38.6%. (Owner)
* The monarch `Category` requirement is now only for the crosswalk: make it optional. (Neo)
* A run with no open charges writes no `open_balance`: write a zero. (Neo)
* Venmo and Zelle histories using `link`'s business-day matching; stepping, replay and decision detail in the console; the YAML editor. (Cypher)
* Dead theme CSS from the old console still remains. (Neo)
* Whether to merge `sprint-24` and then `sprint-25` into `main` and push. (Owner, not done)
