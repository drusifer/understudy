# Architecture Document: Sprint 23, household numbers you can trust and a run that tells its story

*   **Status**: Draft — awaiting Smith Gate 2
*   **Author**: Morpheus
*   **Last Updated**: 2026-11-02
*   **Scope**: Sprint 23 Architecture (stories: `USER_STORIES_SPRINT23.md`; decisions: `OWNER_DECISIONS_SPRINT22.md` 4-8)

---

## 1. Executive Summary & System Overview

The household sketch (`examples/household/household.yaml`) types each record by pairing candidate transfers, asking Jev about unpaired payees, and linking refunds. On the owner's real data this read $9,000 to $25,000 Charles Schwab deposits as refunds, so Ridgewood income was $404k against the owner's $363k.

**Drivers:** the owner's hand-edited export already says which records are transfers, and the sketch language must stay code-free (`classify`, `where`, `join`). **Goals:** kinds follow the export's Category; per-account totals; a per-merchant review list; kept pins; a story-telling event stream. **Non-goals:** the console UI for any of it (Sprint 24), a new taxonomy, a new threshold.

## 2. System Context & Boundaries

* **Owner** gives a Monarch export, an Amex export and optionally a pin file. The runner writes a run folder. The console reads the folder (read-only).
* **Jev** (TypeSafe) is the only external service; one request per merchant that is not pinned.
* **Trust:** all inputs are the owner's local files; no new network surface and no new secret. The pin file holds merchant names and category names (private financial data, same class as the exports; `.understudy/` and `data/` are git-ignored).

## 3. Component & Container Architecture

### Component Inventory
| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `household.yaml` (`typed` chain) | Kind from the export's Category (UND-89) | `records` with `Category` | `kind`, a `by_category` flag per record |
| `household.yaml` (`totals` stages) | Income, expenses, net per account and overall (UND-90) | `typed` | `totals.jsonl` rows, `summary.json` figures |
| `household.yaml` + `place_merchant.yaml` | Pins applied before Jev; runner-up recorded (UND-91, UND-92) | `pins` source, `merchants_and_categories` | `placed` rows, `review.jsonl` |
| `src/sketch/stages_rows.py` | New generic row actions: `sum` option of `group`, `without` | rows | rows |
| `src/sketch/sources/file.py` | Optional source with a default path (`pins`) | `--with pinned` | rows or none |
| `src/machine_runner.py` `RunRecord` | Writes `machine`, `state_entered`, `decision` and ending lines to `events.jsonl` (UND-81) | machine, stages | event lines |
| `src/dashboard/view.py` | Names a missing story line as an unreadable run | `events.jsonl` | state `unreadable` |

## 4. Runtime Interaction & Critical Flows

1. Runner loads the exports and the pin file (checked now: unknown category, missing merchant, missing explicit path stop the run before any Jev request, UND-92 AC4-5; a missing Category column stops it too, UND-89 AC5).
2. `typed`: a record is `transfer` when its Category is Transfer or Credit Card Payment, else `invalid` / refund / credit / purchase as today. The pairing (`legs`) stays as evidence and as a sink; the kind never depends on it (decision 8, assumption 3). The count of records whose kind differs from what the pairing alone would say goes in `summary.json` (UND-89 AC4).
3. Pinned merchants leave `merchants_and_categories` through `without` and are rejoined to their records as placed with level `pinned`; the rest go to Jev as now.
4. `place_merchant` now outputs the runner-up (level, probability) next to `status`.
5. `finished` marks status; `review` rows are grouped by payee with `sum` into `review.jsonl`, sorted by count descending; `totals` groups non-transfer records by account with `sum`.
6. Each state change appends a `state_entered` line (and each decision a `decision` line) as it happens; the first line is `machine`.

## 5. Interface & Contract Specifications

* **New sinks:** `review.jsonl` (`payee, count, amount, first, first_probability, second, second_probability, reason`), `totals.jsonl` (`account, income, expenses, net`; an `all` row last). Both declared in the sketch.
* **New source:** `pinned` (JSONL: `{payee, category}`), `--with pinned=<path>`, default `.understudy/pinned.jsonl`.
* **Changed kinds:** `external_transfer` is removed (the Category covers it); the Jev payee reading (`judge_payee.yaml`) goes with it, and so do its requests. Readers of `kind` (docs, `kinds.jsonl`, `finished`) are updated in the same phase.
* **Event lines:** `{"event":"machine","states":[...],"transitions":[{"from","event","to"}]}`; `{"event":"state_entered","state","caused_by"}`; `{"event":"decision","stage","options":[{"name","removed_by"|"held_by"}],"pick","probability"}`; the ending line carries `outcome` and any `error`.

## 6. Cross-Cutting Concepts & Resilience

### Failure Modes & Error Handling
| Failure Mode | Trigger / Condition | System Behavior | User / Client Impact | Blast Radius |
|---|---|---|---|---|
| `Missing Category column` | Monarch file without it | Stops before any Jev request | One plain line naming the column | None; no run folder output |
| `Bad pin` | Category not in taxonomy, or no merchant | Stops before any Jev request, names the line | Owner fixes the line | None |
| `Pin path missing` | `--with pinned=` path not found | Stops, names the path | Owner fixes the path | None |
| `Default pin file absent` | `.understudy/pinned.jsonl` not there | No pins; the run says so | None | None |
| `Old events log` | No `machine` line | Console shows unreadable, names the line | Owner sees why | One run row |
| `Jev fails` | As today | Run fails as today | As today | The run |

### Security & Privacy
* **Trust / access boundaries:** no new input from outside the machine; pin and review files are local, read by the runner and, for review, by the console under its existing read rules.
* **Sensitive data:** `review.jsonl` and `totals.jsonl` carry merchant names and amounts (same class as `records.jsonl`); they stay in the run folder, which is git-ignored. Pins never carry free text, so Jev's output is never written into a pin.

## 7. Technical Stack & SDLC / Build Impact

* **Languages & Runtime:** Python 3.12, existing sketch YAML.
* **Core Libraries & Tools:** no additions.
* **Build-Environment Check (CRITICAL):**
  * Does this design add a new language, package manager, runtime version, or external tool? **No**
  * All dependencies follow `docs/SDLC.md` change classes; no Tank Phase 0.

## 8. Architectural Decisions (ADRs) & Technical Debt

### Decision Records
* ADR-0050 (to record via Oracle): the export's Category decides transfer kind; pairing is evidence only; `external_transfer` and the payee reading are removed. Alternatives: fix the pairing rule to treat own-account deposits as transfers (rejected: the owner already labeled them, and the rule cannot know a Schwab deposit is the owner's own savings); keep Jev payee reading as a second opinion (rejected: costs requests, cannot beat the owner's label).
* ADR-0051 (to record): a sink is never also a source; pins come in as a separate source (decision 7).

### Acknowledged Technical Debt & Trade-offs
* The kind now depends on the export carrying the owner's categories; a raw bank export without them cannot be typed. Accepted: the owner edits the categories in Monarch, and the run refuses a file without the column.
* Pairing is kept only as evidence and a sink; if nothing reads `legs.jsonl` after Sprint 24 it should go.
