# Architecture Document: Sprint 24, what the money goes on, typed inputs, and the statechart you can see

*   **Status**: Draft — awaiting Smith Gate 2
*   **Author**: Morpheus
*   **Last Updated**: 2026-11-02
*   **Scope**: Sprint 24 Architecture (stories: `USER_STORIES_SPRINT24.md`; decisions: `OWNER_DECISIONS_SPRINT22.md` 4 and 9)

---

## 1. Executive Summary & System Overview

Four changes on three existing parts: the household sketch (`examples/household/household.yaml`), the sketch model (`src/sketch`), and the console (`src/dashboard`).

* **Household (UND-93, UND-94):** a record is a transfer by label or by link; a ranked `spending.jsonl` and a spending total come from existing rows with two small generic stages.
* **Console, money (UND-95):** the run description gains a short list read from `spending.jsonl`.
* **Typed inputs (UND-87):** a sketch declares `inputs`; the loader injects defaults and checks limits; the console draws a control per kind.
* **Statechart (UND-82):** the server lays the machine out in Python from the Sprint 23 story and sends the boxes, arrows and lit state as JSON; the page only draws SVG.

**Non-goals:** stepping, replay, decision detail, the editor (Sprint 25); any browser-side layout library (ADR-0048 keeps one toolchain).

## 2. System Context & Boundaries

The owner uses the console in a browser on the home network; it reads run folders and starts runs as child processes behind one access secret (ADR-0049). No new external service. Trust: the sketch file and the run folder are the owner's; the browser is the one place that renders text from them, so state names, guards and categories are set with `textContent`, never as markup.

## 3. Component & Container Architecture

### Component Inventory
| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `household.yaml` (`labeled`, `standing`) | Transfer basis: label, link, both or none; kind from it (UND-93) | `linked` rows | `transfer_basis`, `kind`; basis counts in `summary.json` |
| `household.yaml` (`spend_*`) | Category per record, grouped, ranked, shared (UND-94) | `typed`/`finished` rows | `spending.jsonl`, `spending_total` in `summary.json` |
| `stages_rows.py` | New generic stage `map.share` (each row's share of a field's total); sorting uses the existing `reduce.max` with a large `take` | rows | rows |
| `src/sketch/loader.py`, `model.py`, `check.py`, schema | `inputs:` declaration: kinds, limits, defaults; defaults injected into the template variables; `--with` values checked against them | sketch YAML, `--with` | `Sketch.inputs`; one-line errors naming the input |
| `src/dashboard/runs.py` | Lists each sketch's inputs; checks submitted values against the declaration before starting | sketch, request body | `inputs` in `/api/sketches`; 400 with a sentence |
| `src/dashboard/chart.py` (new) | Layered layout of the machine and the lit state, pure Python | `run_started` states and transitions, `state_entered`, run state | `chart` JSON: nodes, edges, labels, size, current, last move, ended |
| `src/dashboard/view.py`, `reads.py` | Add `chart` and `spending` to a run's description | run folder | JSON |
| `page.js`, `controls.js`, `page.css` | Draw the chart (SVG), the spending list, and the four controls | JSON | DOM (text via `textContent`) |

## 4. Runtime Interaction & Critical Flows

1. **Typed values:** the console lists a sketch with its declared inputs; the owner sets controls; Play posts `with` values for every input (defaults included); the server checks each against the declaration, then starts `understudy run` with `--with name=value`; the loader checks again (the CLI path) and fills any missing declared input from its default.
2. **Transfer:** `labeled` classifies each record's basis from its Category and its partner; `standing` makes it a transfer when the basis is not `none`; `counted` tallies the basis into `summary.json`.
3. **Spending:** rows of kind purchase or refund get `spend_category` (the export's Category, else Jev's, else `uncategorized`), are grouped with a `cost` sum, given a share of the total, sorted by amount and written; a group by a constant gives the total for `summary.json`.
4. **Chart:** `describe` reads the events; `chart.layout(states, transitions)` returns the boxes and arrows once per run (cached on the story line); the current state and the last move come from the last two `state_entered` lines; the SSE refresh already redraws the page, so the light moves within a second.

## 5. Interface & Contract Specifications

* **`inputs:`** in a sketch: `name: { kind: choice, options: [..], default: x }`, `{ kind: range, min, max, step, default }`, `{ kind: count, min, max, default }`, `{ kind: switch, default: on|off }`, each with an optional `label`. Values reach templates as text (`on`/`off` for a switch). `understudy check` refuses an unknown kind, a default outside the limits, a choice with no options or a default not among them.
* **`/api/sketches`:** each entry gains `inputs: [{name, kind, label, options|min|max|step, default}]`; `with` keeps the undeclared names (plain text boxes).
* **`/api/runs/<id>`:** gains `chart` (`{nodes:[{id,x,y,w,h,final,current}], edges:[{from,to,path,label,taken}], width, height, ended}` or `null` when the log has no story) and `spending` (`{top:[{category,amount,share}], more, problem?}` or `null`).
* **`spending.jsonl`:** `category, count, amount, share`, sorted by amount; `summary.json` gains `spending_total` and `transfer_basis` (`label`, `link`, `both`, `none` counts), replacing `kind_changed_by_category`.

## 6. Cross-Cutting Concepts & Resilience

### Failure Modes & Error Handling
| Failure Mode | Trigger / Condition | System Behavior | User / Client Impact | Blast Radius |
|---|---|---|---|---|
| `Bad input declaration` | Unknown kind, default outside limits, empty choice | `check` and `run` stop naming the input | One plain line | The sketch |
| `Value outside limits` | `--with` or posted value not allowed | Refused before any run starts (400 from the console) | A sentence naming the input and its limits | None |
| `Log without a story` | `run_started` has no `states` | `chart` is null; the panel says so | No diagram | One run |
| `Unreadable spending.jsonl` | Malformed line | `spending.problem` names it; the page continues | A line in the summary panel | The summary panel |
| `Huge machine` | More than forty states | Layout wraps layers; boxes and labels never overlap (tested at 40) | Taller diagram | One panel |
| `Hostile text` | A state name or guard with markup | Drawn as text only | Nothing executes | None |

### Security & Privacy
* **Trust / access boundaries:** values typed in the console reach a child process as `--with` arguments (an argument list, no shell) only after the existing allow-list and the new limit checks; the access secret still guards Play.
* **Sensitive data:** `spending.jsonl` holds category names and totals, no merchant names; it is read through the same capped reader as the other run files.

## 7. Technical Stack & SDLC / Build Impact

* **Languages & Runtime:** Python 3.12, plain browser JavaScript and SVG.
* **Core Libraries & Tools:** none added (no `elkjs`, no chart library).
* **Build-Environment Check (CRITICAL):**
  * Does this design add a new language, package manager, runtime version, or external tool? **No**
  * All dependencies follow `docs/SDLC.md` change classes; no Tank Phase 0.

## 8. Architectural Decisions (ADRs) & Technical Debt

### Decision Records
* ADR-0052 (to record): a transfer is the widened label or a link to a record in another account; the label alone left $153,085 of card payments counted as income. Supersedes the "pairing is evidence only" part of ADR-0050; the owner's own labels still decide in both directions apart from the link. Alternative rejected: label only (fails the stated target); a Jev reading of payees (removed in Sprint 23, costs requests).
* ADR-0053 (to record): inputs are declared in the sketch with defaults, and the loader injects them; a template no longer repeats a default. Alternatives rejected: types guessed from the template (cannot know limits); a separate settings file (a second place to keep in step).
* ADR-0054 (to record): the chart layout is computed in Python and drawn by plain JavaScript. Alternatives rejected: elkjs in the browser (a second toolchain, ADR-0048); drawing from the event stream in the page (untestable without a browser).

### Acknowledged Technical Debt & Trade-offs
* A few purchases under a card-side label (Depop, Soho Deli, Levy Restaurants) are treated as transfers until the owner relabels them.
* The layout is a simple layered one (longest path from the initial state, back-edges drawn around the side); it is good for the machines we have and tested to forty states, not a general graph drawer.
* Undeclared `--with` names keep a text box; a sketch with many of them is not improved until it declares inputs.
