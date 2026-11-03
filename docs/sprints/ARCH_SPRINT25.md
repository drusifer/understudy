# Architecture Document: Sprint 25, the tool fixes the categories, and payments know what they paid for

*   **Status**: Draft — awaiting Smith Gate 2
*   **Author**: Morpheus
*   **Last Updated**: 2026-11-03
*   **Scope**: Sprint 25 Architecture (stories: `USER_STORIES_SPRINT25.md`; decisions: `OWNER_DECISIONS_SPRINT22.md` 10 to 13b)

---

## 1. Executive Summary & System Overview

The household sketch (`examples/household/household.yaml`) takes its categories and its transfers from Monarch's labels: Jev places a merchant in "a category in use" (built from the export), and a record is a transfer when its label says so. The owner has decided the labels are a mess (decision 10). This sprint replaces them:

* **A clean list** (UND-96): the ISO 18245 groups and names plus the owner's additions file.
* **Jev categorizes** (UND-97): every merchant, in two steps (group, then name), from that list; the export's category is never shown to Jev.
* **Kinds from links and categories** (UND-98): a transfer is a linked payment pair or a merchant in "Household: Transfer"; link candidates are found from the record's text, never its Category.
* **Payments own charges** (UND-99): oldest-first allocation of the card's charges to each card payment, with a stated remainder.
* **Spending from the tool's categories** (UND-100).

**Non-goals:** Venmo and Zelle histories (the allocation stage is written so they can reuse it), stepping, replay, the editor.

## 2. System Context & Boundaries

The owner gives a Monarch export, an Amex export, an additions file (a shipped starting file by default) and optional pins. Jev (TypeSafe) is the only external service. Nothing new crosses the network boundary; the additions file is a new local input of the same class as the pin file, and its names become Jev's answer options (the owner's own text, never Jev's output).

## 3. Component & Container Architecture

### Component Inventory
| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `household.yaml` (`taxonomy`, `candidates`, `kinds`) | The clean list; link candidates from text; kind from link or category | exports, additions, pins | `taxonomy` rows, `kind`, `transfer_basis` |
| `categorize_merchant.yaml` (new, replaces `place_merchant` and `name_merchant`) | Two Jev choices per merchant: a group, then a name in it | a merchant's facts, the taxonomy | `category` ("Group: Name"), status, best guess |
| `src/sketch/stages_rows.py` | New generic stages: `map.unique` (a repeat stops the run naming the line), `map.allocate` (oldest-first allocation), `map.top` (the largest few rows per group) | rows | rows |
| `household.yaml` (`pay_*`, `spend_*`) | `payments.jsonl`, `settled_by` on each charge, open balance, spending from the tool's category | typed records | `payments.jsonl`, `spending.jsonl`, `summary.json` |
| `household.yaml` (`crosswalk`) | Every merchant with the tool's category and the export's most common one side by side, flagged where they differ about money moving | records, categories | `crosswalk.jsonl` |
| `src/dashboard` | None: `spending.jsonl` keeps its shape, so the console list needs no change | | |

## 4. Runtime Interaction & Critical Flows

1. **Checks first, before any Jev request:** the additions file (path exists, every line has a group and a name, no repeat of an ISO or earlier name) and the pins (each names a category in the clean list).
2. **Link by text:** the card export's payment lines and records with payment words in their description, statement or payee are candidates; they are paired by opposite amount in different accounts within three business days (the existing link stage). The export's Category is not read.
3. **Merchants:** the payees of records that are not linked halves; pinned ones leave the list; the rest are asked.
4. **Jev, per merchant:** step one chooses a group (13 ISO groups, Household, none_of_these); step two chooses a name in it. Both above 0.7 places the merchant; otherwise it goes to `review.jsonl`. Cost: about two requests per merchant (about 1,650 for the household's 820), each cached, so a repeat run or a replay costs none.
5. **Kind:** linked, or category "Household: Transfer", is a transfer; refund linking, credits and purchases follow as today. A merchant for review keeps its records as purchases or credits and is listed unplaced.
6. **Allocation:** for the Amex pool (records that came from the Amex export), each payment's amount is filled with that pool's charges dated on or before it, oldest first, stopping before the amount would be passed; what is left of the amount is the remainder. Each charge gets `settled_by` (a payment id) or stays open.
7. **Reports:** `payments.jsonl` (the payment, charges settled, amount, remainder, five largest categories), the open balance and spending total in `summary.json`, `spending.jsonl` by the tool's category.

## 5. Interface & Contract Specifications

* **New source:** `additions` (JSONL `{group, name}`), `--with additions=<path>`, default the shipped `examples/household/additions.jsonl` (Rent, Mortgage, Tuition, Income, Transfer, Loan repayment under "Household").
* **New sinks:** `payments.jsonl` (`payment_id, day, card, amount, charges, settled, remainder, unexplained, top: [{category, amount, share}]`) and `crosswalk.jsonl` (`payee, count, amount, tool_category, export_category, differs_on_money_moving`).
* **Changed:** every record gains `category` and `category_source` (`jev` or `pin`) and `settled_by`; `review.jsonl` keeps its shape; `spending.jsonl` keeps its shape with the tool's categories (`unplaced` for a merchant for review); `summary.json` gains `open_balance` and `ridgewood` income and expenses, and `transfer_basis` becomes `link`, `category`, `both`, `none`.
* **Disagreement, defined:** the tool and the export use different category systems, so their category words cannot be compared. A merchant is a disagreement when they differ about money moving: the tool says transfer and the Sprint 24 label rule says not, or the reverse. Both categories are shown so the owner can judge the rest by eye. (A reading of UND-98 AC4 that Smith should confirm.)
* **Pool, defined:** the Amex pool is the records that carry `other_Account #`. Other cards have no payment history to allocate from and are left open.

## 6. Cross-Cutting Concepts & Resilience

### Failure Modes & Error Handling
| Failure Mode | Trigger / Condition | System Behavior | User / Client Impact | Blast Radius |
|---|---|---|---|---|
| `Bad additions` | Missing path, a line without group or name, a repeated name | Stops before any Jev request, names the path or line | One plain line | None |
| `Bad pin` | A category not in the clean list | Stops before any Jev request, names the line | Owner fixes it | None |
| `Jev unsure` | Step one or two at 0.7 or below, or none_of_these | The merchant goes to `review.jsonl`; its records stay unplaced | Owner pins it | One merchant |
| `Jev fails` | Request error | The run fails as today | As today | The run |
| `No payments` | A pool with no payment lines | No `payments.jsonl` lines; every charge is open | Open balance equals the charges | None |
| `Payment before any charge` | The first payment in the export | Remainder equals its amount; marked unexplained | A line saying so | One payment |
| `Mislabeled payment` | A bank-side payment whose Category says income | Still links by text and is a transfer | None | None |

### Security & Privacy
* **Trust / access boundaries:** the additions file is a new local input, checked before any Jev request; its names are Jev's options only (Jev still chooses, never writes). No new endpoint or secret.
* **Sensitive data:** `payments.jsonl` and `crosswalk.jsonl` hold merchant names, amounts and category names in the git-ignored run folder, the same class as `records.jsonl`. Jev sees a merchant's name, statement text and a few amounts, as today, and no longer sees the export's categories.

## 7. Technical Stack & SDLC / Build Impact

* **Languages & Runtime:** Python 3.12, sketch YAML.
* **Core Libraries & Tools:** `iso18245` (already a dependency).
* **Build-Environment Check (CRITICAL):**
  * Does this design add a new language, package manager, runtime version, or external tool? **No**
  * All dependencies follow `docs/SDLC.md` change classes; no Tank Phase 0.

## 8. Architectural Decisions (ADRs) & Technical Debt

### Decision Records
* ADR-0055 (to record): the taxonomy is ISO 18245 plus the owner's additions; Jev chooses a group and then a name; the export's categories are not used. Alternatives rejected: building the list from the export (inherits the mess); one question over all 286 names (too long to answer reliably); letting Jev propose new names (Jev never writes).
* ADR-0056 (to record): a transfer is a text-found link or the category "Household: Transfer"; export labels never decide. Supersedes ADR-0052's label rule. Alternative rejected: keep the label rule as a hint (the owner called the labels a mess).
* ADR-0057 (to record): a card payment settles the card's charges oldest first, charges only, never past its amount, with a stated remainder. Alternatives rejected: matching a run of charges to the cent (no statement dates in the export, so no payment matches); counting credits in the allocation (gaps up to $6,304 on the baseline).

### Acknowledged Technical Debt & Trade-offs
* The first run costs about 1,650 Jev requests (about four minutes); a repeat is free from the capture.
* The allocation is approximate by nature: the remainder is shown, never hidden.
* Only the Amex pool is allocated until another card export exists.
* The Monarch-label disagreement is read as "differ about money moving", not as a comparison of category words.
