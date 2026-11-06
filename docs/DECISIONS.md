# Decisions

Newest first. Each record follows `agents/templates/_template_DECISION.md`, kept short.
Sprint 1 records were made by Morpheus in `docs/sprints/ARCH_SPRINT1.md` §8, sprint 2
records in `docs/sprints/ARCH_SPRINT2.md` §8 and sprint 3 records in
`docs/sprints/ARCH_SPRINT3.md` §8, sprint 4 records in `docs/sprints/ARCH_SPRINT4.md` §8
(all approved at Smith Gate 2, 2026-10-15) sprint 5 records in `docs/sprints/ARCH_SPRINT5.md` §8
and sprint 6 records in `docs/sprints/ARCH_SPRINT6.md` §8 (approved at Smith Gate 2, 2026-10-16). Records before
ADR-0011 say "adapter" and "part"; since ADR-0011 those are `hooks.mjs` and `sketch.yaml`.

---

# ADR-0062: The console draws a play from one plan, and holds a run before a beat through the control file

*   **Status**: Accepted
*   **Deciders**: owner (decisions 39 and 43), Morpheus
*   **Date**: 2026-11-05
*   **Related**: `docs/sprints/STORY_ARCH_SPRINT29.md`, UND-111 to UND-113, ADR-0054 (the chart), ADR-0058 (hold and step), ADR-0061

## 1. Context and Problem Statement

The console drew only the scene's flow (ADR-0054) and could hold a run only between flow beats, one after another (ADR-0058). The owner wanted the whole play drawn (files, beats, who reads what), a play started held or held before a chosen beat, and each step to say what it read and wrote.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Keep the flow chart and draw the plan as a second picture | Two drawing paths and two shapes in the log | Rejected |
| One plan built from the play file (`src/play/plan.py`), laid out by the existing router, carried in `run_started` | The first log line grows (household about 30 KB) | Selected: the picture of a run and of a play before it runs are the same data, and a replay needs no file |
| The page asks the server for the plan of a run's play by name | The play file may have changed since the run; the run's play path is not a listed play | Rejected |
| The runner writes `control.json` when it reaches the beat to hold before | The console and the runner both write one file; a step could be lost | Rejected |
| `control.json` gains `stop_at`; the runner only reads it; the console's next pause, step or resume writes the file without it | One more key; the beat is "spent" by the next console write | Selected |

## 3. Decision Outcome

* **Chosen Option:** `plan(document)` returns `{nodes, edges, props, initial}`; the reads come from the parameters an action declares as `Source` (the registry `check` uses), plus `each`, a Jev beat's options and state, and a call's bindings. `plan_layout` lays out every node and edge with the router of ADR-0054 (nodes carry `kind`, `write`, `flow`, `waits`, `action`, `with`; edges carry `kind`). `run_started` carries the plan; `overlay` lights it from events, for a run and for a replay. `GET /api/plan?play=` serves the plan of a listed play before any run. `Hold` holds before a beat that is `stop_at` whatever the mode, and a start takes `hold` or `hold_at` (checked against the flow beats; `--by-console` lets the console's child accept `--pause` and `--stop-at`). `beat_completed` carries `read`, `wrote` and (added beyond the story) `made`: names, row counts and column names only.
* **Consequences:** the old story line (`beats`, `transitions`) is gone; a run recorded before Sprint 29 shows "no plan" and no diagram (no back-compat, decision 41). The events log of the real household run grew from 594 KB to 1.06 MB. The household outputs stayed byte-identical on the real files. The page's diagram nodes became focusable buttons where a person can choose a beat, so the keyboard test and the accessible names changed with them.

---

# ADR-0061: A sketch is a play: a stage that is its interface, and a scene of beats

*   **Status**: Accepted
*   **Deciders**: owner (decisions 19 to 42, shaped in conversation 2026-11-04 and 05), Morpheus
*   **Date**: 2026-11-05
*   **Related**: `docs/sprints/STORY_ARCH_SPRINT28.md`, UND-105 to UND-110, `docs/PLAYS.md`, `docs/DOMAIN.md`; supersedes the file shape of ADR-0040, ADR-0043 and ADR-0053

## 1. Context and Problem Statement

A sketch had sources, sinks, inputs and a machine of states, and two ways to compute rows (a `kind: stage` source and a state) that did the same thing. The owner wanted the understudy metaphor carried into the domain model, to make it easier to understand, without adding redundant concepts, and wanted plays reusable inside other plays.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Rename only (sketch to play, machine to scene, states to beats) | Keeps two ways to compute rows | Rejected: "a distinction without a difference" (owner) |
| Move every computed source into the scene with `to:` | About 140 hand-ordered beats in household; inserting one edits a neighbor | Rejected |
| One kind of step, a beat; `to:` only where order or a choice matters, otherwise performed when read | The engine needs one translation point | Selected |
| A play and a scene as two file types | A second concept with the same shape | Rejected: one file type; a play calls a play |
| Return a called play's written files to the caller as files | Disk I/O in a loop; files are part of the set | Rejected (owner) |

## 3. Decision Outcome

* **Chosen Option:** a play has a **stage**, its whole interface (props, files read, files written with `access: write`), and a **scene** of **beats**. A beat with `to:`/`transitions:`/`final` is in the flow; a beat without them is performed when another beat first reads it, once. Jev is a beat. `from:` names an action's main input; `do: { write: x }` and `do: { play: x.yaml }` replace sinks and sketch calls. Running a play means providing its stage: from the command line (`--with` gives props and file paths) or from a call (`with:` binds props and the called play's files; what it writes is the beat's result; under `each` each written row carries the row it was played for). The loader's `engine_view` is the one place that turns the play into the engine's sources, sinks and machine, so run, capture and replay did not change. No back-compat: an old sketch is refused as unknown keys; old runs show as unreadable.
* **Consequences:** household's outputs stayed byte-identical (fixtures and a real replay) through every phase. Removed: `outputs:`, `{input, output}` pairs, `map.unpair`, `--source`. The engine's internal names and the console's JSON keys still use the old words behind the translation (debt in `docs/ARCH.md`).

---

# ADR-0060: Rules are tested on their own stages; a whole run is for what only a whole run shows

*   **Status**: Accepted
*   **Deciders**: owner (decision 17: the test pyramid), Morpheus
*   **Date**: 2026-11-03
*   **Related**: `docs/sprints/STORY_ARCH_SPRINT27.md`, UND-101 to UND-104, `docs/TEST_STRATEGY.md`

## 1. Context and Problem Statement

The gate took 96 to 101 s and grew every sprint. A measured run (`unittest --durations`) showed about 53 whole-household-sketch runs at about 2 s each, one browser test of 47.5 s that flaked, and a half-second wait to stop every test server.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Run tests in parallel | Hides the cost; the same work on more cores | Rejected (revisit only if the budgets are not met) |
| Only reorder the gate (lint first) | Saves nothing when the tests pass | Done as well, but not the fix |
| Test each rule on its own stage; keep a few whole runs | A stand-in can drift from a stage's real output | Selected |
| Compute contrast from the declared colors in Python | The themes draw text on textured gradients, so the answer would be wrong | Rejected |

## 3. Decision Outcome

* **Chosen Option:** `src/sketch/fragment.py` (`Fragment`, `read_stage`) computes any source of a sketch from written rows, with stubs for the stages and Jev reads behind it; `run_state` runs a machine state (a check) on its own; the run's `compute` is one shared function (`stage_computer`). Whole-sketch household runs: five, each with a reason. A moved test is proved by breaking its rule. Budgets are in `docs/TEST_STRATEGY.md`.
* **Consequences:** the unit suite is 29.4 s (was 94.6 s) and the gate 36.3 s (was 96 to 101 s). A stand-in (`placed_all`, the Jev double) can drift from the child sketch's real output; only the happy-path run and the child's own tests catch that. The browser suite keeps real-pixel contrast (about 100 s, over its 90 s budget by about 10 s).

---

# ADR-0059: A replay is computed in Python from the events up to N, with the live view's own functions

*   **Status**: Accepted
*   **Deciders**: Morpheus
*   **Date**: 2026-11-03
*   **Related**: `docs/sprints/ARCH_SPRINT26.md`, UND-84, UND-85, ADR-0054

## 1. Context and Problem Statement

The owner wants to play a finished run's story back. The page already draws a live run from `describe`; a replay must never disagree with it.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Replay in the page's JavaScript | A second implementation of the view | Rejected |
| Store a snapshot per event | Duplicates the log; grows with every run | Rejected |
| `replay(dir, at)` in Python: cut the events at N and apply the same functions (stage tree, gauges, printed lines, lit state) | Re-derives the view per step (0.03 s on 5,027 events); resends all lines so far | Selected |

## 3. Decision Outcome

* **Chosen Option:** `GET /api/runs/<id>/replay[?at=N]` and `/decisions`; the page draws the frame with its own drawing and times PLAY. The last event equals the live view (tested on real runs). A log with an unreadable line is refused, naming it.
* **Consequences:** fine to about 100,000 events; past that, send only new lines. The Jev count shows `-` until the last event because the log has no running total.

---

# ADR-0058: A run is held between top-level stages through a control file the console writes and the runner reads

*   **Status**: Accepted
*   **Deciders**: Morpheus, Switch (design and Phase 2 reviews)
*   **Date**: 2026-11-03
*   **Related**: `docs/sprints/ARCH_SPRINT26.md`, UND-83

## 1. Context and Problem Statement

The console must hold, step and resume a run it does not share a process with, without Jev being asked meanwhile.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| A socket or signal to the runner | More surface; lost on restart; hard to test | Rejected |
| Hold inside a stage | Would stop a Jev request half done | Rejected |
| `control.json` in the run folder `{mode, steps}`, read before each top-level stage | A stage in flight finishes first | Selected |

## 3. Decision Outcome

* **Chosen Option:** the runner's gate waits while `mode` is `hold` and lets one stage through per step (`steps` only grows, so old steps are never replayed); a missing, oversized or malformed file means `run`. The console writes it atomically, only for a run it started or the one `run --watch` serves, behind the secret, a same-origin request and an 8 KiB body cap. `run --watch` binds 127.0.0.1 and keeps its secret in `.understudy/watch.secret`, apart from the dashboard's.
* **Consequences:** a long stage delays a pause until it ends; a held run reads PAUSED, never stalled; holding is by top-level stage only.

---

# ADR-0057: A card payment settles the card's charges oldest first, never past its amount

*   **Status**: Accepted
*   **Deciders**: Morpheus
*   **Date**: 2026-11-03
*   **Related**: `docs/sprints/ARCH_SPRINT25.md`, UND-99, owner decision 12

## 1. Context and Problem Statement

A card payment is a lump sum; the export has no statement dates, so nothing says which charges it paid. The owner wants each payment tied to its charges.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Match a run of charges to the cent | No payment on the baseline matches exactly | Rejected |
| Count credits (refunds) in the allocation | Gaps up to $6,304 on the baseline | Rejected |
| Fill each payment with the card's charges dated on or before it, oldest first, stopping before its amount is passed; show the remainder | Approximate; the first payment is partly unexplained | Selected |

## 3. Decision Outcome

* **Chosen Option:** the generic stage `map.allocate`: payments in date order; charges by the card's own date (not the bank's), a day's charges smallest first (so the result does not depend on file order); whole cents; a charge in at most one payment; none dated after the payment. A payment is "unexplained" when more than 5% of it has no earlier charge.
* **Consequences:** on the baseline 11 of 12 payments settle within 5% (worst 4.6%); settled plus open equals all the card's charges to the cent. The rule is approximate by nature and the remainder is shown, never hidden. Only the Amex pool is allocated until another card export exists.

---

# ADR-0056: A transfer is a link found in the text or the category "Household: Transfer"; export labels never decide

*   **Status**: Accepted (supersedes the label rule of ADR-0052)
*   **Deciders**: Morpheus, owner decisions 10 and 11
*   **Date**: 2026-11-03
*   **Related**: `docs/sprints/ARCH_SPRINT25.md`, UND-98

## 1. Context and Problem Statement

The export's own categories are a mess (the owner's words), so a rule that reads them decides wrongly in both directions.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Keep the label rule as a hint | Inherits the mess | Rejected |
| Records linked as the two halves of a payment (found from their own text, within three business days), or whose merchant is in "Household: Transfer", or a card's own "payment received" text | Jev may not put every own-account merchant in Household: Transfer, so the owner pins them | Selected |

## 3. Decision Outcome

* **Chosen Option:** kinds read links, the tool's own category and the card's payment text; the export's `Category` is only compared with the tool's answer in `crosswalk.jsonl`, flagged where they differ about money moving.
* **Consequences:** `summary.json` counts `transfer_basis` as `link`, `category`, `both`, `payment` and `none`. Pins are part of the workflow (Charles Schwab is pinned as the owner's savings).

---

# ADR-0055: The category list is ISO 18245 plus the owner's additions; Jev chooses a group and then a name

*   **Status**: Accepted
*   **Deciders**: Morpheus, owner decisions 10 and 11
*   **Date**: 2026-11-03
*   **Related**: `docs/sprints/ARCH_SPRINT25.md`, UND-96, UND-97

## 1. Context and Problem Statement

Categories copied from the export are inconsistent. Every merchant should get one category from a clean list, chosen by the tool.

## 2. Considered Options

| Option | Costs / risks | Reason |
|---|---|---|
| Build the list from the export | Inherits the mess | Rejected |
| One question over all 286 names | Too long to answer reliably | Rejected |
| Let Jev propose new names | Jev would write text | Rejected (Jev chooses, never writes) |
| 13 ISO groups plus a "Household" group of the owner's additions (Rent, Mortgage, Tuition, Income, Transfer, Loan repayment); Jev picks a group, then a name in it | About two requests per merchant | Selected |

## 3. Decision Outcome

* **Chosen Option:** a merchant is placed when each choice is above 0.7, or at least 0.4 and twice the runner-up's (amended after the first real run sent 73% of records to review); otherwise it is listed in `review.jsonl`. The owner's pins override Jev and are checked against the list before any request. Every report, the spending list included, uses this category and `unplaced` for a merchant in review.
* **Consequences:** a live run asks again (about 2,300 requests, seven minutes); only `--replay` reuses answers. On the baseline 38.6% of spending is still `unplaced` until the owner pins more merchants.

---

# ADR-0054: The statechart's layout is computed in Python; the page only draws it

*   **Status**: Accepted
*   **Deciders**: Morpheus
*   **Date**: 2026-11-02
*   **Related**: `docs/sprints/ARCH_SPRINT24.md`, UND-82, ADR-0048

## 1. Context and Problem Statement

The old console drew each run's statechart with a browser layout library. The Python-served console (ADR-0048) has one toolchain and no Node, and the owner wants the diagram back with the current state lit.

## 2. Decision Drivers

* One toolchain; everything testable without a browser; the sketch's own machine is the source.
* The same machine must always give the same drawing, with no box or label on another and no arrow through a box.
* Text from a sketch must never become markup.

## 3. Considered Options

| Option | Benefits | Costs / risks | Reason selected or rejected |
|---|---|---|---|
| A layout library in the browser (elkjs) | A mature layout | A second toolchain and a large file; hard to test | Rejected |
| Lay out in the page's own JavaScript | No server change | No Python test of overlaps; logic split across two languages | Rejected |
| Lay out in Python, draw plain SVG in the page | Tested to 40 states without a browser; the page is about sixty lines | A simple layered layout, dense at 40 states | Selected |

## 4. Decision Outcome & Justification

* **Chosen Option:** **`src/dashboard/chart.py`** returns boxes, arrows (routed through the gaps between rows and the gutters beside them) and a lane for each label; `describe` adds the lit state, the move just taken and the ending; `page.js` draws SVG with `textContent` only.
* **Justification:** the overlap rules are unit-tested on generated 40-state machines and the real machines; a hostile state name is drawn as text (browser test).

### Consequences
- **Expected benefit:** the diagram follows a live run within a second (the page refreshes in 250 ms bursts from the event stream).
- **Costs or risks:** the layout is longest-path layering, so a dense machine is busy; a better drawer is a replacement of one module.

# ADR-0053: Inputs are declared in the sketch with defaults, and the loader injects them

*   **Status**: Accepted
*   **Deciders**: owner (2026-11-02, decision 4: typed inputs wanted), Morpheus
*   **Date**: 2026-11-02
*   **Related**: `docs/sprints/ARCH_SPRINT24.md`, UND-87

## 1. Context and Problem Statement

A sketch took values only as template variables, so the console could show a text box and nothing else: no limits, no kinds, no defaults it knew about. The owner wants a dial, faders, a stepper and switches.

## 2. Decision Drivers

* A control cannot be set outside its limits, in the console or on the command line.
* One place for a default; the template should not repeat it.
* No fallbacks: a wrong declaration is refused, naming the input.

## 3. Considered Options

| Option | Benefits | Costs / risks | Reason selected or rejected |
|---|---|---|---|
| Guess the kind from the template | No new syntax | Cannot know limits or options | Rejected |
| A settings file beside the sketch | Keeps the sketch plain | A second place to keep in step | Rejected |
| `inputs:` in the sketch (choice, range, count, switch) | One source for kind, limits, default and label | A new top-level key and a small module | Selected |

## 4. Decision Outcome & Justification

* **Chosen Option:** **`inputs:`**, validated by `src/sketch/inputs.py`, which both the loader and the console use. The loader reads the declaration before rendering and injects each default, so templates write `{{ tickets }}`. A number must be plain ASCII digits (SEC-010). Names the file uses but does not declare keep a text box.
* **Justification:** `evening` declares seven inputs and lost its repeated defaults; a bad value is refused in one line on the command line and with a 400 in the console.

### Consequences
- **Expected benefit:** typed controls, the same limits everywhere, defaults in one place.
- **Costs or risks:** the declaration is read with every value empty first, which works for every example sketch; the themes still hold dead styles from the old console's controls (new classes were named to avoid them).

# ADR-0052: A transfer is the widened label or a link to a record in another account

*   **Status**: Accepted (the label rule is superseded by ADR-0056: export labels no longer decide)
*   **Deciders**: owner (2026-11-02, decision 9), Morpheus
*   **Date**: 2026-11-02
*   **Related**: `docs/sprints/ARCH_SPRINT24.md`, UND-93, ADR-0050 (partly superseded)

## 1. Context and Problem Statement

ADR-0050 made the export's `Transfer` and `Credit Card Payment` decide what is a transfer. The owner's file still labels card-side payments as "Food & Dining: Credit Card Payment" and "Transportation: Transfers", and five large card payments received ($133,047) are labeled as income, so the all-account figures counted $240,596 of positive records outside Ridgewood as refunds or credits.

## 2. Decision Drivers

* The owner wants to know what the money goes on, with card payments out of both income and spending.
* The label alone cannot reach the five payments labeled as income; the run already links the two halves of a card payment.
* A label match must not catch a lookalike such as "Transferware".

## 3. Considered Options

| Option | Benefits | Costs / risks | Reason selected or rejected |
|---|---|---|---|
| The widened label only | Simple | Leaves $153,085 of card payments counted as income | Rejected (found at Gate 1) |
| Relabel in Monarch | The owner's data stays the source | Manual work for a few hundred records | Rejected by the owner |
| The widened label or a link | Positives outside Ridgewood fall to $20,038 | A few mislabeled purchases (Depop, Soho Deli) count as transfers | Selected |

## 4. Decision Outcome & Justification

* **Chosen Option:** **A record is a transfer when its Category is `Transfer` or `Credit Card Payment`, or ends in `: Credit Card Payment`, `: Transfer` or `: Transfers`, or when the run links it to a record in another account.** A new condition `ends` matches the end of text exactly. `summary.json` counts the basis (`label`, `link`, `both`, `none`).
* **Justification:** Ridgewood stays $363,348.62 income and $205,042.27 expenses; no labeled or linked record is a purchase, refund or credit.

### Consequences
- **Expected benefit:** the spending list (`spending.jsonl`, UND-94) is not distorted by card payments.
- **Costs or risks:** a purchase the export labels with a transfer form is a transfer until the owner relabels it.

# ADR-0050: The export's own category decides what is a transfer

*   **Status**: Accepted (the "never otherwise" part is superseded by ADR-0052: a link also makes a transfer)
*   **Deciders**: owner (2026-11-02, decision 8), Morpheus
*   **Date**: 2026-11-02
*   **Related**: `docs/sprints/ARCH_SPRINT23.md`, UND-89, `OWNER_DECISIONS_SPRINT22.md` 8

## 1. Context and Problem Statement

The household sketch paired candidate transfers, asked Jev whether each unpaired payee was one of the owner's accounts, and read a deposit from a known merchant as that merchant's refund. On the owner's real data, savings moved from Charles Schwab into checking ($3,000 to $25,000 at a time) came out as refunds and income, so Ridgewood income was $404k against the owner's $363k.

## 2. Decision Drivers

* The owner has already labeled these records by hand in Monarch (Transfer, Credit Card Payment).
* The sketch language stays code-free; fewer Jev requests is better; the owner's labels cannot be beaten by a guess.
* No back-compat: replace the old shape outright (owner rule).

## 3. Considered Options

| Option | Benefits | Costs / risks | Reason selected or rejected |
|---|---|---|---|
| Fix the pairing rule so own-account deposits are transfers | Works on raw exports | The rule cannot know a Schwab deposit is the owner's own savings | Rejected |
| Keep the Jev payee reading as a second opinion | Catches unlabeled transfers | About 25 requests per run; cannot beat the owner's label | Rejected |
| The export's Category decides; pairing kept as evidence only | Matches the owner's numbers to the cent; removes a Jev call and `external_transfer` | A raw export without the owner's categories cannot be typed | Selected |

## 4. Decision Outcome & Justification

* **Chosen Option:** **The export's Category decides.** A record is a transfer exactly when its Category is `Transfer` or `Credit Card Payment`, otherwise never. The links stay in `legs.jsonl`, and `summary.json` counts the records where category and pairing disagree. A file with no Category column stops the run before any Jev request.
* **Justification:** on the baseline file Ridgewood income is $363,348.62 and expenses $205,042.27, equal to the owner's file to the cent.

### Consequences
- **Expected benefit:** correct per-account totals; `judge_payee.yaml`, `judgments.jsonl` and the `external_transfer` kind are gone.
- **Costs or risks:** card-side records that the export labels with other groups ("Food & Dining: Credit Card Payment", "Transportation: Transfers") are no longer transfers; about 169 positive records worth $240,596 outside Ridgewood count as refunds or credits. Owner to relabel them in Monarch or widen the rule.

# ADR-0051: A sink is never also a source; the owner's pins come in as a separate source

*   **Status**: Accepted
*   **Deciders**: owner (2026-11-02, decision 7), Morpheus
*   **Date**: 2026-11-02
*   **Related**: `docs/sprints/ARCH_SPRINT23.md`, UND-91, UND-92

## 1. Context and Problem Statement

Jev is unsure about merchants (below 0.7, or none of the categories fit). The owner wants to answer once per merchant and never be asked again. A run's output folder is write-once history; a later run must not depend on files an earlier run wrote there.

## 2. Decision Drivers

* Runs stay reproducible: the same files and pins give the same result.
* Jev chooses and never writes text; the owner's answers are categories, not free text.
* No new sketch feature where an ordinary source will do.

## 3. Considered Options

| Option | Benefits | Costs / risks | Reason selected or rejected |
|---|---|---|---|
| A sink that is also a source | One file | A run reads and writes the same file; re-running an old run changes | Rejected |
| Pins only in the console | Friendly | Needs the console first; not scriptable | Rejected for now |
| `review.jsonl` out, `pinned.jsonl` in as a separate optional file source | Reproducible, scriptable, console button can come later | The owner edits a file for now | Selected |

## 4. Decision Outcome & Justification

* **Chosen Option:** **A per-merchant `review.jsonl` sink and a separate `pinned.jsonl` source** (`--with pinned=<path>`, default `.understudy/pinned.jsonl`, absent default means no pins, a missing explicit path stops the run). A pin is `{payee, category}` with a category the export uses; pins are checked before any Jev request, and a pinned merchant is placed from the file, marked `category_source: pin`, never asked about and left out of `review.jsonl`.
* **Justification:** a small optional file source (`optional: <name of the --with value>`) and four generic stages (`without`, `complete`, `known`, `set`) did it with no change to how runs are stored.

### Consequences
- **Expected benefit:** the review list shrinks each run; the same pins give the same records.
- **Costs or risks:** two pins for one merchant keep the first (not checked); a category's edge spaces must match (the export has `Pharmaceuticals ` with a trailing space); a pin file is edited by hand until the console offers a button.

## ADR-0049: The console starts runs as child processes, behind one access secret and an allow-list

*   **Status**: Accepted · **Deciders**: owner (watch and start; plain HTTP accepted until 2027-01-30), Morpheus, Switch · **Date**: 2026-11-01 · **Related**: Sprint 22 UND-79; [ARCH_SPRINT22](sprints/ARCH_SPRINT22.md); SEC-005 to SEC-009; owner decisions 1-2 of Sprint 22
*   **Context**: the owner wants to start, replay and stop runs without a terminal, from other devices, and the console listens on every network interface with no login for reading.
*   **Options**: (1) a login page; (2) run sketches inside the console's own process; (3) Play only from the machine itself; (4) child processes behind one startup secret and an allow-list.
*   **Decision**: (4). The console starts `understudy run` as a child process (an argument list, no shell, its own session; one per sketch, four in all), only for a sketch inside the folder given with `--sketches`, only with names that sketch takes, only with file values inside the project, after the same check `understudy check` makes. The access secret is made at each start, saved in `.understudy/dashboard.secret` (mode 0600, git-ignored) and never printed, and every POST needs it in a header from the same origin. Reading stays open.
*   **Consequences**: + no accounts or login page; a stolen browser tab loses the secret when it closes; every refusal is a sentence and a test. − the secret crosses the network in plain text (accepted by the owner until 2027-01-30; TLS flags are the fix); one shared secret has no audit trail; a console restart forgets the children it started. Rejected: (1) a second mechanism for one owner; (2) a stage could block or crash the console; (3) the owner works from other devices.

## ADR-0048: Node is removed; the console is Python-served, with plain browser JavaScript

*   **Status**: Accepted · **Deciders**: owner · **Date**: 2026-11-01 · **Related**: Sprint 21 UND-74, UND-75; [owner decisions 1-2](sprints/OWNER_DECISIONS_SPRINT21.md); epic `EPIC_PYTHON_PORT.md` slices C and D; supersedes the Node parts of ADR-0011, ADR-0018, ADR-0030
*   **Context**: after Sprint 20 the only Node left was a launcher and the dashboard's browser files, and a second toolchain (npm, eslint, node:test) was paid for by them alone.
*   **Options**: (1) keep Node for the page's tests and lint; (2) serve the page from Python, keep the browser script plain, decide everything testable in Python.
*   **Decision**: (2). `src/dashboard/server.py` (standard-library `http.server`) serves the page and a small JSON and server-sent-events API over `build/runs`; `page.js` only draws it. The console watches runs; it does not start them or edit YAML. Fonts are committed.
*   **Consequences**: + one toolchain, no `package.json`; the console shows only real data. − `page.js` has no automated test (checked by hand at UAT); the old play controls, dial, faders and YAML editor are gone and would be rebuilt from scratch if wanted.

## ADR-0047: The household ETL is a sketch; SQLMesh and the MCP source servers are gone

*   **Status**: Accepted · **Deciders**: owner · **Date**: 2026-10-30 · **Related**: Sprint 20 UND-71, UND-72; [owner decisions 36-40](sprints/OWNER_DECISIONS_SPRINT20.md); supersedes ADR-0046
*   **Context**: the household ETL was written before the sketch model had stages, `each`, Jev sources over rows or conditions. It kept its own controller, a database of SQL models and MCP servers that paged CSVs, so there were two ways to do everything.
*   **Options**: (1) wrap the old ETL in stages (done once, as a first cut, and rejected); (2) rebuild it from the sketch model's own parts and delete the old code.
*   **Decision**: (2). `examples/household/household.yaml` reads the CSVs as file sources and uses general stages (`convert`, `pair`, `link`, `earlier`, `group`, `classify`, `join` ...), three child sketches that ask Jev (`judge_payee`, `link_refund`, `place_merchant`) and one that folds (`name_merchant`, `each` with `reduce`). Dates and business days are Python (`dateparser`, `holidays`). A database is not a sketch concept; DuckDB stays only inside the stage helper that runs short queries.
*   **Consequences**: + one language, one runtime, a 90 s test suite became 11 s; every rule is visible in YAML or in a general, tested stage. − Category naming no longer does the old rubric check on three candidate names (Jev still only chooses), a refund candidate's option name now carries its record id, and `amex_account` is required instead of detected (`since` is optional).

## ADR-0045: `understudy run` and `understudy check` are the Python commands, now

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-29 · **Related**: STORY-UND-60; [Sprint 19 architecture](sprints/ARCH_SPRINT19.md)
*   **Context**: the owner wants one kind of sketch and no duplicates; the old Node `run` and `check` could break. A `sketch` subcommand beside the old `run` was proposed and rejected.
*   **Options**: (1) the Node launcher's `run` and `check` start the Python package and the old Node player is deleted; (2) a new subcommand beside the old command until the end of the epic; (3) one command that picks by file type.
*   **Decision**: (1). `src/cli.mjs` is a launcher (`run`, `check`, `etl run`) through one Python spawner. Everything the old `run` and `check` needed, which turned out to be the whole old player, was deleted in Phase 5: targets, apps, the watch page's server, the dashboard's server, the XState machine, nine npm dependencies and 41 Node test files. `library`, `watch` and `dashboard` answer that they are being rebuilt.
*   **Consequences**: + one command, one format, one runtime for sketches; git history keeps the old player. − the six old examples, the dashboard and the watch page do not run until slices B and C rebuild them; the dashboard's browser files are kept for slice C.

## ADR-0044: Weights are numbers or if/then/else

*   **Status**: Accepted · **Deciders**: owner · **Date**: 2026-10-29 · **Related**: STORY-UND-63; supersedes ADR-0030
*   **Context**: a decider's weight sometimes depends on the input (night workers ignore the weather). A `0 if segment = 'night_workers' else 0.3` string would need a parser and mixes two syntaxes.
*   **Options**: (1) a number, or the same `if`/`then`/`else` the owner uses for decisions; (2) SQL expressions evaluated by DuckDB; (3) a small expression language.
*   **Decision**: (1) (owner: "use 2"). No text is parsed that is not a YAML structure; a missing `else` is 0.
*   **Consequences**: + nothing to learn or parse; the JSON Schema covers it. − more lines than a one-line expression.

## ADR-0043: Jev is a source kind, and non-file sources capture and replay

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-29 · **Related**: STORY-UND-60, STORY-UND-65; [Sprint 19 architecture](sprints/ARCH_SPRINT19.md)
*   **Context**: a Jev judgement needs a rubric and data to read, and tests and live runs must never mix. Jev first appeared as a special `ask` step.
*   **Options**: (1) `kind: jev` source like a file or a future MCP source, with `instructions` and `criteria` as the rubric and `state` built from other sources, plus capture of every non-file source and one `--replay` flag; (2) a machine keyword for asking Jev; (3) a Jev double only in tests.
*   **Decision**: (1). A live read is captured under git-ignored `.understudy/cache/<run-id>/` with the run id, request hash and time, the last 5 runs kept together; `--replay [run-id|folder]` uses the latest run that captured every non-file source and never falls back to live; a request hash that no longer matches marks the run `stale` and carries on; `summary.json` says `mode`.
*   **Consequences**: + one testing mechanism for every future non-file source; the one real Jev answer is committed as `tests/fixtures/coffee/replay/`. − the capture holds real data (git-ignored); a source read several times with different params is not handled.

## ADR-0042: Conditions are explicit YAML, and sketches are read as YAML 1.2

*   **Status**: Accepted · **Deciders**: owner · **Date**: 2026-10-29 · **Related**: STORY-UND-61, STORY-UND-63
*   **Context**: conditions as strings need a parser; PyYAML reads an unquoted `70:30` as the base-60 number 4230.
*   **Options**: (1) a field, one operator and a value in YAML (`eq ne lt le gt ge in not_in has ends`, `and or not`, slices as `a:b`; `ends` added in Sprint 24); (2) SQL text; (3) a small expression language.
*   **Decision**: (1), read with ruamel.yaml (YAML 1.2, so slices stay text). `in` takes a list or a slice (start included, stop excluded); `has` is contains; a field a row lacks never matches; a condition compares a field with a fixed value only.
*   **Consequences**: + a JSON Schema and the checker validate every condition; no parser. − verbose next to one-line expressions.

## ADR-0041: One decider contract and one combination rule, the weighted blend

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-29 · **Related**: STORY-UND-63; supersedes ADR-0018
*   **Context**: the old engine multiplied `position ^ weight` factors, so a zero anywhere vetoed a candidate and the formula hid the owner's rules.
*   **Options**: (1) every decider returns weighted rows and a stage blends them as a weighted average per dimension, with vetoes written as `forbid` filters; (2) keep the multiplicative score; (3) a weighted sum.
*   **Decision**: (1). A row names only the dimensions it has an opinion on; the blend averages each dimension over the deciders that name it; `forbid` drops options and renormalises and always wins; a filter that empties a row fails the run unless the stage says `skip` or `fallback`. Joint combinations (a recipe on two options) are not built yet.
*   **Consequences**: + the owner's vetoes are readable rules, not a hidden zero. − no automatic "one weak factor sinks the candidate"; the owner writes down where a weak factor rules a candidate out.

## ADR-0040: A sketch is the owner's own pipeline; the loop is plain Python

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-29 · **Related**: [Epic](sprints/EPIC_PYTHON_PORT.md); [design notes](sprints/DESIGN_SKETCH_MODEL.md); supersedes ADR-0011
*   **Context**: understudy is a platform for automation, not an actor that plays an app. There is no single state machine for all sketches.
*   **Options**: (1) the owner writes their own python-statemachine YAML; the loop is Python (`src/machine_runner.py`, shared with the ETL); (2) one built-in turn machine; (3) a sketch with no machine.
*   **Decision**: (1). A sketch names sources, sinks, outcomes, data and a machine whose states name stages (ETL on DuckDB, `blend`, a subsketch, a sink); `then` and guarded `transitions` pick the next state. A subsketch declares `returns: { decider: [dimensions] }` and runs as a nested run in the same folder. Outputs are published last.
*   **Consequences**: + any decision can be written down without code; the ETL and sketches share one loop. − the old turn/play model and its tags and invoke are gone.

## ADR-0039: Purchases pair one-to-one inside a date-and-amount group

*   **Status**: Accepted · **Deciders**: Morpheus, owner · **Date**: 2026-10-27 · **Related**: STORY-UND-50; [Sprint 17 architecture](sprints/ARCH_SPRINT17.md)
*   **Context**: Sprint 16 paired a Monarch and an Amex row only when their date and amount occurred exactly once on each side and called every repeat ambiguous. On the owner's real files it paired 26 rows, because the two exports record the same purchase with opposite signs, and two real purchases of the same amount on the same day (two coffees) could never pair.
*   **Options**: (1) pair within each (date, absolute amount) group one-to-one, with the sign flipped, exact merchant text first and source row order only to break ties among otherwise identical rows; (2) keep "repeats are ambiguous" and send them to review: safe but leaves thousands of real duplicates counted twice; (3) ask Jev to judge each pair: matching is arithmetic, and about 4,300 paid calls would answer a deterministic question.
*   **Decision**: (1), restricted to the Monarch account that is the Amex card (auto-detected as the account holding the most sign-flipped matches, overridable with `--amex-account`). Rows without a counterpart stay single. Added in Phase 2 after the first real-file run: a third pass pairs leftovers when the amount is equal and the dates are one to three days apart (95 of the 114 Amex rows left unpaired by same-date pairing had such a partner), nearest date first, each row used once.
*   **Consequences**: + the real overlap pairs (fresh files, 2026-10-27: 4,475 of 4,489 Amex rows, 4,392 same date and 83 within three business days; 14 left single); two identical purchases stay two records. The near-date window counts business days (weekends and US federal holidays excluded) and matches in up to five rounds so identical fares all find a partner. − for rows identical in date, amount and merchant text the pairing among equals is arbitrary, which is harmless because nothing observable differs; the 3-day transfer window and label rule are tuned to one household's data.

## ADR-0038: ETL rules are SQL, each export is an MCP source server, the controller is Python

*   **Status**: Accepted · **Deciders**: Morpheus, owner · **Date**: 2026-10-27 · **Related**: STORY-UND-49 to 55; [Sprint 17 architecture](sprints/ARCH_SPRINT17.md); `agents/morpheus/spike_sprint17.md`
*   **Context**: the owner decided that understudy moves to Python for all, that no new ETL language or state machine representation is invented, and that there is to be no XML. Sprint 16's controller is Node and shares the run database with SQLMesh through a sequential handoff.
*   **Options**: (1) keep SQL on DuckDB for relational rules, serve each export from a Python MCP server, and write the controller in Python using `python-statemachine`'s YAML, `typesafe-sdk` and `mcp`; (2) keep the Node controller and only add SQL: smallest change, but keeps two runtimes against the owner's direction; (3) SCXML for the stage machine: a W3C standard, rejected by the owner (no XML), and its Python interpreters are abandoned.
*   **Decision**: (1). The Phase 0 spike showed the stage machine, guards and failure branch run from YAML; `typesafe-sdk` returns per-option probabilities; the `mcp` 2.x SDK pages 14.5k rows over stdio in about a second; the MCC list is the MIT `iso18245` package. The Python controller replaces `src/etl/run.mjs`, `categories.mjs`, `csv.mjs` and the ETL's use of `src/jev.mjs` outright, with no compatibility output (`review.csv` becomes `result.jsonl`).
*   **Consequences**: + one runtime for the ETL, no Node-DuckDB seam, the rules survive the Python port because they are SQL, a new source is a new server. − Sprint 16's Node ETL code is deleted after one sprint; `python-statemachine`'s schema has no `tags`, so the port epic must find another way to carry `move` and `safe`; `mcp` 2.x is new and renamed APIs (pin it); the licence of the network descriptions bundled in `iso18245` is not verified, so only its ISO descriptions and groups are offered to Jev.

## ADR-0037: SQLMesh owns deterministic ETL; Understudy coordinates Jev decisions

*   **Status**: Accepted · **Deciders**: Morpheus, owner, Tank · **Date**: 2026-10-17 · **Related**: STORY-UND-46, STORY-UND-47, STORY-UND-48; [Sprint 16 architecture](sprints/ARCH_SPRINT16.md)
*   **Context**: Sprint 16 reproduces a local Monarch and Amex cleanup workflow over roughly 4,700 reconciled transactions. SQL joins and transformations are standard ETL; Understudy must stage data-dependent steps and apply Jev's bounded category choices without using its limited answer-row memory as a transaction store.
*   **Options**: (1) SQLMesh models in SQL with YAML project configuration and local DuckDB: mature relational transforms with a run-scoped external decision table, at the cost of an isolated Python toolchain and a JSONL hydration stage; (2) dbt with DuckDB: familiar SQL/YAML models, but it also requires Python and offers no advantage for the sequential Jev handoff in this small local run; (3) custom Node joins/maps: fewer runtime components, but Understudy would own and maintain bespoke relational operations for reconciliation, grouping, and output.
*   **Decision**: (1) is accepted. Understudy validates and snapshots the local CSV exports, converts each flat row to an internal JSONL record with normalized fields and source provenance, then SQLMesh loads the JSONL records into DuckDB and owns deterministic relational transforms. Understudy coordinates named hydration and decision stages, asks Jev to choose from the fixed category/subcategory taxonomy (including Misc), and stores accepted merchant mappings in a run-scoped relation for reuse. This does not add arbitrary or nested JSONL input. CSV pagination and fetch mechanics remain below ETL operations if future MCP sources are added. Google Sheets/MCP I/O is deferred. Tank and the owner approved the isolated Python/SQLMesh mechanism; the Phase 0 clean setup and sequential SQLMesh/Node/DuckDB handoff probe passed.
*   **Consequences**: + uses a mature SQL engine for joins and row transforms while keeping qualitative decisions bounded and auditable. − introduces Python alongside Node and a second toolchain; CSV-to-JSONL hydration and SQLMesh JSONL loading add a staged interchange step. Synthetic end-to-end and SQLMesh model tests verify reconciliation, taxonomy mapping, review output, and failure behavior; private production CSVs and live Jev were not used for acceptance.

## ADR-0036: Gauges read the run's own lines; flair is visibly decoration

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-17 · **Related**: UND-42
*   **Context**: owner: per-theme flair with gauges - "yes real metrics in the gauges".
*   **Options**: (1) gauges computed in the page from the stream it already gets (start, step and `decided` lines), plus the run's limits added to the start line; (2) a separate metrics endpoint; (3) decorative gauges.
*   **Decision**: (1). `metersAfter`/`gaugesOf` are pure and unit-tested; the start line gains `limits: { steps, first_move_ms, stall_ms }`. Each theme draws the same five readings its own way (needle, hovering bars that stay within a small band round the value, card). Bulbs, leather and screws carry no meaning.
*   **Consequences**: + no new endpoint; a page joining mid-run rebuilds the readings from the history. − the start line has one more field.

## ADR-0035: The statechart is a layered flow laid out by ELK on the server

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-17 · **Related**: UND-41, UND-30
*   **Context**: owner: the states-round-a-circle tube was hard to follow ("is there a more standard visualization?"); edges crossed the middle and labels piled up.
*   **Options**: (1) a layered (Sugiyama) flow from `elkjs`, computed on the server and sent with the sketch; (2) `@dagrejs/dagre`; (3) improve the hand-made circle layout.
*   **Decision**: (1), top to bottom (it comes out square, so it fits the round tube and a phone without shrinking), orthogonal arrows, edge labels placed by ELK, model order kept so the initial state leads. The page only draws boxes, arrows and text. Steampunk keeps its round tube with a thin power ring on the rim; the other themes draw on a rectangular screen; the shares that the orb showed are a bar under the screen.
*   **Consequences**: + the standard statechart picture; no overlaps; no layout code in the page. − a new dependency; the layout is async, so describing a sketch waits for it.

## ADR-0034: Every Jev request carries the run's inputs; `pick.with` is removed

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-17 · **Related**: UND-40, UND-24
*   **Context**: owner: the questions' wording should follow the parameters ("see all"); fixed words like "two seats" contradicted the tickets input.
*   **Options**: (1) the run's inputs in every request's state, named in prose as `` `inputs.<name>` ``; (2) per-question `with:` lists, as `pick` had; (3) substituting values into the prose text before asking.
*   **Decision**: (1). `services.inputs` reaches the library's requests and the MCP app's score request; `pick.with` is removed outright; `check` refuses an undeclared `inputs.<name>`. (3) would put literal values in the prose, which the no-literals rule forbids - Jev reads the path from the state instead.
*   **Consequences**: + one rule for every question; wording cannot drift from the controls. − every request is a little larger; a sketch that used `with:` must drop it.

## ADR-0033: A run takes the caller's pause gate; the dashboard steps through it

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-17 · **Related**: UND-39, ADR-0016
*   **Context**: owner: step a run one move at a time from the dashboard, as `--watch` already can.
*   **Options**: (1) `runSketch({ gate })` - the caller makes a `createGate` and holds it; (2) the dashboard starts each run with `watch` and drives the watch server; (3) a second pause mechanism in the runner.
*   **Decision**: (1). The run loop already asks `gate.beforeMove()`; the dashboard's runner makes one gate per run, sends its changes to the pages as `{ event: 'dashboard', paused, waiting }`, and exposes `pause`/`step`/`resume`. Without a gate a run is unchanged.
*   **Consequences**: + one pause mechanism for both pages; paused time stays out of the idle limits. − a run takes either the watch page's gate or the caller's, not both.

## ADR-0032: Light and dark are a `data-mode` attribute; each theme's colours are variables

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-38
*   **Context**: owner: every theme in light and dark; the mode follows the device unless chosen (LIGHT / DARK / AUTO, remembered).
*   **Options**: (1) `data-mode` beside `data-theme`, each theme's other mode an override block, colours held in custom properties; (2) six separate theme stylesheets; (3) only `prefers-color-scheme` media queries.
*   **Decision**: (1). `modeOf(choice, isDeviceDark)` with a `matchMedia` listener sets `data-mode`; professional and starship were rewritten so their other mode only redefines variables; steampunk light is one override file, because steampunk's wood and brass live in `page.css`. Media queries alone (3) could not honour a fixed choice.
*   **Consequences**: + a mode switch is instant and follows the device live; a new theme declares its variables twice. − steampunk light is an override list that must follow `page.css` when panels change.

## ADR-0031: A hand-written JSON Schema for editors; check stays the full check

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-37
*   **Context**: owner asked how the YAML is documented; the reference is complete but editors gave no help while typing.
*   **Options**: (1) a hand-written draft-07 schema for the YAML language server, kept in step with `check` by tests; (2) generate the schema from `check`'s code; (3) make `check` run the schema.
*   **Decision**: (1). `ajv` (dev only) validates the examples and common mistakes; a test compares the schema's keys, target fields, input kinds and question types with the lists `check` exports. Examples carry a `# yaml-language-server: $schema=` line.
*   **Consequences**: + completion, hover text and underlines in any YAML-language-server editor, no runtime dependency; `check`'s precise messages unchanged. − the schema is a second description of the format, held to `check` only where the comparison test reaches (deeper rules - names, states, prose - are `check`'s alone).

## ADR-0030: A weight input is a share of the full weighting (3)

*   **Status**: Superseded by ADR-0041 and ADR-0044 (Sprint 19) · **Deciders**: owner · **Date**: 2026-10-16 · **Related**: UND-24, ADR-0017
*   **Context**: the evening's weight inputs moved from [0, 3] to [0, 10] so the faders read 1-10; used straight as exponents, 10 punished anything short of the best far harder (row F 0.67^10 = 0.02 against 0.67^3 = 0.30).
*   **Options**: (1) the input's share of its range times a full weight of 3; (2) keep the value as the exponent; (3) a per-input `max` field.
*   **Decision**: (1) - owner: "the slider is the percentage of the weighting applied (so 5 is = 1.5)". `inputs.weightsOf` turns the run's values into weights; `score` takes them as `weights`. A written number is still the exponent itself.
*   **Consequences**: + any range reads naturally and scores the same; the dashboard's sizes and the engine agree. − a person cannot weigh a factor above 3 from an input; a sketch wanting more writes the number.

## ADR-0029: Dashboard themes are a `data-theme` attribute and one stylesheet per theme

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-36
*   **Context**: owner: a professional theme and a Star Trek TNG one, beside the steampunk console. The tube's colours were hard-coded in the page script.
*   **Options**: (1) `<html data-theme>` with `page.css` as the default and a scoped stylesheet per theme, all loaded; script colours read from CSS custom properties; (2) swap one stylesheet link at run time; (3) a theme object in JavaScript styling every element.
*   **Decision**: (1). Theme rules sit under `:root[data-theme="..."]` so they beat the default without `!important`; the choice is `?theme=`, else localStorage, else steampunk.
*   **Consequences**: + an instant switch, mid-run; a new theme is one CSS file and one button. − every new piece of the console must be styled three times; the theme files are long override lists.

## ADR-0028: The bay behind the printer writes the whole sketch file

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-35
*   **Context**: owner: take the printer off to edit the sketch's YAML, saved as you type, and watch the tube change. The access panels' allow-list (ADR-0024) only lets listed values change.
*   **Options**: (1) a separate whole-file `write` beside the allow-listed `edit`, checked the same way on a copy; (2) widen the allow-list to every path; (3) a code-editor library with live parse and save.
*   **Decision**: (1). Same refusal check and factory copy as `edit`; refused while a run plays; the page sends writes one at a time after 500 ms of quiet, into a plain `<textarea>`.
*   **Consequences**: + any part of the sketch is editable, with the same safety (nothing failing `check` is written; POWER restores). − a whole-file write rewrites comments as typed, and no highlighting or completion; the drawers stay the precise way to change one value.

## ADR-0027: Count inputs, and inputs referenced as `{ input: <name> }`

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-34
*   **Context**: owner: replace the "seats together" toggle with a number-of-tickets selector (a brass stepper); the number must drive both the seats held and the together rule.
*   **Options**: (1) a `count` input kind and `{ input: name }` wherever a value or a gate bound is written; (2) a tickets-specific setting; (3) Jev choosing the count.
*   **Decision**: (1), in `values:` lists and gate `at_least`/`at_most` only. `check` validates the name and, for bounds, that it is a count or weight. On the dashboard a count is a stepper; weights stay analog faders.
*   **Consequences**: + one input feeds several places; other sketches get the stepper for free. − references are not allowed elsewhere yet (e.g. score ranges).

## ADR-0026: Switch inputs turn gates on and off (`when:`)

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-28
*   **Context**: owner: toggles on the console; a switch should turn a rule on or off.
*   **Options**: (1) a `switch` input and a `when: <switch>` word on a gate test; (2) switches that pick between whole gate sets; (3) a rule language with conditions.
*   **Decision**: (1). A test whose switch is off passes and needs no fact. `check` refuses `when:` naming anything but a switch. `--input name=on|off|true|false`.
*   **Consequences**: + no new language, one word. − a switch can only turn individual tests off, not swap rules.

## ADR-0025: Factory defaults are a copy kept at the first edit; POWER off-on restores

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-32
*   **Context**: owner: edits are saved to the sketch, with a reset to defaults - "turn it off and then back on".
*   **Options**: (1) copy `sketch.yaml` to `<folder>/.factory/<name>.yaml` before its first edit, restore all on POWER on; (2) git checkout; (3) keep edits only in memory.
*   **Decision**: (1). The copy is git-ignored and removed once restored.
*   **Consequences**: + works without git, one gesture undoes all. − a sketch edited by hand while the console has a copy is overwritten by the reset.

## ADR-0024: Panel edits replace only the edited value's text, checked on a copy first

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-32
*   **Context**: saving must keep a hand-written `sketch.yaml` readable, and never write a sketch that fails its checks.
*   **Options**: (1) find the value through `yaml.parseDocument` source ranges and replace just that text, then `loadSketch` a temp copy of the sketch directory; (2) edit the YAML Document and re-serialise; (3) write and roll back on failure.
*   **Decision**: (1). (2) was tried in Phase 6 and reflowed long lines and padded every flow list. Only allow-listed paths (inputs' defaults and choices, factor range/order/ask, a question's `looks_at`) can change.
*   **Consequences**: + byte-for-byte the rest of the file; nothing invalid is written. − a key the file does not have yet falls back to (2).

## ADR-0023: The dashboard is its own server beside the watch page; runs go through runSketch

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-27, UND-29
*   **Context**: owner: a steampunk console over a folder of sketches - set inputs, press Play, watch.
*   **Options**: (1) a second local server built like the watch page (token path, local files, SSE) with a small JSON API, running sketches in-process through `runSketch` and reading their stdout lines; (2) extend the per-run watch server; (3) spawn `understudy run` processes.
*   **Decision**: (1). `listenOn`/`readBody` are shared with the watch server; the watch page's `turnGraph` is reused. A STOP pressed while a run's servers start is held and delivered on its start line.
*   **Amendment (owner, 2026-10-16)**: the dashboard is served at the root (`http://<host>:<port>/`), with no token in the URL - not needed on the owner's network. With `--host 0.0.0.0` anyone who reaches the port can play and edit sketches; the watch page keeps its token path.
*   **Consequences**: + the CLI and the console run sketches the same way. − one run at a time; two browsers share it.

## ADR-0022: Several servers in one MCP target

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-20
*   **Context**: owner: enrichment from more MCP servers (a ratings service beside the box office), each named the MCP way.
*   **Options**: (1) one target holding several clients; (2) one target per server with the run switching between them; (3) a proxy server merging tools.
*   **Decision**: (1). `servers:` (inline, or names in a `servers.json`); tools are `<server>/<tool>` only when there are several, so one-server sketches, ids and logs are unchanged. A server that will not start stops the others and is named.
*   **Consequences**: + a sketch plays any mix of local and remote servers. − with several, ids are longer; a failure anywhere ends the run.

## ADR-0021: Walking away is a guard plus a tagged final state

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-25
*   **Context**: owner: when nothing passes, the understudy leaves and the run succeeds.
*   **Options**: (1) guard `nothing_qualifies` + a final state tagged `walked-away`; (2) the run detects it and ends by itself; (3) treat it as `stalled`.
*   **Decision**: (1). The turn decides where leaving goes; outcome `walked-away`, exit 0, a `walked-away` line and a sentence. Smith Gate 2: an argument that never saw a value (no seat map read because every showing was gated out) does not block leaving; a held-back value always does.
*   **Consequences**: + "nothing tonight" is a testable result. − a sketch without the state stalls instead (with the same explanation).

## ADR-0020: Jev at the edges - a Score per row and the final Choice; never weights

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-23, UND-24
*   **Context**: owner: constraints for what can be measured, Jev for the qualitative (audience reaction) and the final pick coloured by mood. Jev chooses, never writes.
*   **Options**: (1) Score questions as factors + a final Choice with inputs; (2) Jev sets the weights from prose; (3) Jev ranks the whole list.
*   **Decision**: (1). A `type: score` question `looks_at` a row field; asked once per row per run, every waiting row in one request on the next look; its 0..1 answer is a weighted factor. The final Choice gets `pick.instructions` and the inputs in `pick.with`; a shortlist of one is taken without asking. (2) deferred - it would be writing numbers.
*   **Consequences**: + Jev's judgment is one more knob, reused, cheap. − a value waits a look for its Score.

## ADR-0019: Scoring lives in the app, not in the statechart

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-21, UND-22
*   **Context**: owner asked whether the rule logic belongs in xstate or new primitives.
*   **Options**: (1) the generic MCP app filters and ranks the values of one move; (2) per-factor xstate guards.
*   **Decision**: (1). Guards are booleans choosing transitions; ranking values within one move is a different job. The turn sees one outcome, `nothing_qualifies`. The engine (`src/engine.mjs`) is pure over JSON rows.
*   **Consequences**: + reusable beyond MCP (a later `understudy rank`). − the statechart diagram does not show the rules; the step's score table does.

## ADR-0018: Gates, then weighted curves multiplied

*   **Status**: Superseded by ADR-0041 (Sprint 19) · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-21, UND-22
*   **Context**: owner: what is never accepted vs what is liked more; "the option I want the most has the biggest bearing"; a zero should drop a value.
*   **Options**: (1) hard gates, then score = position^weight per factor, multiplied (weighted geometric mean); (2) a weighted sum; (3) everything as hard rules.
*   **Decision**: (1). Gates remove (with why) or hold back (missing fact); while anything is held back the argument offers nothing, unless a value already totals a perfect 1 (owner, 2026-10-16). `range`/`order`/`ask` place a field 0..1; weight 0 turns a factor off; a 0 anywhere removes the value; the shortlist is every total above 0, bounded by `at_most`/`total.at_least`.
*   **Consequences**: + a great tomato cannot hide an end seat. − authors must set range floors deliberately: the bottom of a range removes.

## ADR-0017: Values carry their answer row; facts join by a named key

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-16 · **Related**: UND-21
*   **Context**: rules test facts about a value (a showing's genre lives a level up; a film's score on another server). Sprint 3 offered flat leaf values of the last answer only.
*   **Options**: (1) rows: objects with inherited scalars, values from rows that own the field, across all remembered answers, joined by `join`; (2) look facts up by value equality.
*   **Decision**: (1). Lists of plain values (reviews) count as facts. A decided value used in a call that answered is spent. At most 500 rows kept.
*   **Consequences**: + facts from any server meet; a call already answered with the same arguments is not repeated (owner: an LRU cache, `lru-cache`, 200 calls). − spent values never come back even if the app changes; one join key, exact match.

## ADR-0016: Pause is a gate before each move; no Jev call while paused

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-15
*   **Context**: owner: pause and step a live run from the watch page. A pause must not let Jev be asked anything, must not trip the 10 s first-move/stall limits, and Ctrl-C must still stop the run.
*   **Options**: (1) a gate in the run loop before `takeStep` (the Jev request is inside the step); (2) pause the seat's looking too; (3) pause by suspending the app.
*   **Decision**: (1). `gate.beforeMove()` waits while paused; Step lets one move through, Resume opens it. Idle limits subtract paused time. Ctrl-C releases a *paused* run straight to stop (`interrupted`, no move - QUIT alone would wait for a safe state, which a move state is not); a running watched run stops as any run does, so `--watch` alone changes nothing.
*   **Consequences**: + a paused run is fully still and cheap. − pause takes effect at the next move: until the app offers one, the understudy keeps looking.

## ADR-0015: The watch page is served by understudy and draws its own statechart

*   **Status**: Accepted · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-14, UND-16
*   **Context**: owner: a browser page showing the statechart, state changes and Jev decisions live, plus replay. Must work offline and on the Pi.
*   **Options**: (1) node:http + Server-Sent Events + a small layered SVG layout of our own; (2) Mermaid for the diagram (122 MB unpacked, re-render to highlight); (3) a WebSocket library; (4) a terminal UI.
*   **Decision**: (1). The server binds 127.0.0.1 with a per-run token path, serves only the page's own files, streams history then live lines then `end`; `/control` in live mode only. Live and replay are the same page fed the same events; replay frames are one per log line, so stepping walks the statechart (Phase 5 finding: per-step frames hid the move state).
*   **Amendment (owner, 2026-10-16)**: `--host ADDR` binds the page to another address (e.g. `0.0.0.0`) to watch from another device; 127.0.0.1 stays the default, and the per-run token is then the only guard (documented).
*   **Consequences**: + no new dependency, nothing fetched from the internet. − the layout is ours to maintain (columns by distance from the start, gaps sized to labels, back edges arced above - a visual check in Phase 2 drove both).

## ADR-0014: The run log is an event stream

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-15 · **Related**: UND-13
*   **Context**: replay (owner) needs everything the page shows to be in the log; tools reading step and final lines must keep working.
*   **Options**: (1) add `event` lines - `start` (sketch, plays, turn), `state` (from XState's inspection API), `ended` (why a failed run ended) - to stdout and the log; (2) a second file for events; (3) live-only events.
*   **Decision**: (1). Idle looks (end where they began, no move) are folded into `idle_looks` on the next listed change. Step and final lines keep exactly their fields; readers skip lines with `event`.
*   **Consequences**: + one self-contained log per run; stdout stays equal to the log. − the seat reads XState's microstep `_transitions` (an internal of the inspection API), pinned by a test listing the exact transitions.

## ADR-0013: Jev chooses argument values, it never writes them

*   **Status**: Accepted, confirmed by the owner after launch ("constrained automation") · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-10 AC4-5
*   **Context**: owner: a sketch may list fixed calls, and Jev fills the remaining arguments. Jev (TypeSafe) answers only choice, noul and score questions - it cannot produce free text.
*   **Options**: (1) Jev chooses each open argument from a finite list - the sketch's `values`, the schema (enum, boolean, narrow integer range), or the last non-error result's leaves; (2) generate free text with another model; (3) offer only tools with no required arguments.
*   **Decision**: (1), in a second request after the tool is picked, one Choice per argument; an off-list answer is re-asked once, then the run stops (ADR-0004). A tool whose required argument has no list is not offered, and the run says so once per tool. Candidates come from the last result that was **not an error** (Phase 2 finding: a refused call must not erase what the call before it offered).
*   **Consequences**: + every value sent was offered and is in the log; tools chain naturally (ids from one answer feed the next call). − free-text arguments need listed values; noisy results give long lists (capped at 20).

## ADR-0012: MCP target - SDK client, understudy's own stdio transport, the `mcpServers` shape

*   **Status**: Accepted · **Deciders**: owner, Morpheus · **Date**: 2026-10-15 · **Related**: UND-10, UND-11
*   **Context**: owner: understudy plays any MCP server as its client (not an MCP server itself), on the off-the-shelf `@modelcontextprotocol/sdk`, local and remote, configured the way Claude Desktop/Code configure servers.
*   **Options**: (1) SDK `Client`; local servers over a small `ProgramTransport` on `program.mjs` (using the SDK's `ReadBuffer`/`serializeMessage`), remote over the SDK's `StreamableHTTPClientTransport`; (2) the SDK's `StdioClientTransport` for local servers; (3) a hand-written JSON-RPC client.
*   **Decision**: (1). The server is one `mcpServers` entry, inline (`server: {...}`) or by reference (`config: servers.json, server: <name>`); `${VAR}`/`${VAR:-default}` filled at run start only; remote auth is token headers only (no OAuth, no SSE). A look lists tools + the last result; a move is one tool call; tool errors (isError or JSON-RPC) are the server's answer. A remote server that answers the connection with an HTTP error is `refused`, named by URL and status, never by header.
*   **Consequences**: + a local server is started, watched (exit code, stderr tail) and stopped like every other program; check needs no secrets. − `ProgramTransport` leans on two SDK exports (checked in Phase 2); resources, prompts and notifications are not read.

## ADR-0011: One `sketch.yaml` per sketch; code only in `hooks.mjs`

*   **Status**: Superseded by ADR-0040 (Sprint 19); it had replaced the adapter/part layout of sprints 1-2 · **Deciders**: owner, Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-9
*   **Context**: owner: one YAML file per sketch with all configs and params, and it is the only format (no back-compat). Sprints 1-2 split a stand-in over `adapter.mjs`, `part/turn.yaml` and `part/questions.yaml`.
*   **Options**: (1) `sketch.yaml` (name, description, target, app, player, steps, questions, turn, and for MCP calls/values) + `hooks.mjs` only where the target has no generic app; (2) keep the three files and add a YAML adapter beside the JS one.
*   **Decision**: (1). `src/sketch.mjs` replaces `part.mjs`; `parseTurn` takes the parsed `turn:`; every error names `sketch.yaml` and the path in it (`turn.states...`, `questions.answer...`); `--steps` beats `steps:`; a directory with `adapter.mjs` or `part/` and no `sketch.yaml` is refused, saying what replaced them.
*   **Consequences**: + one file to read; pages and MCP servers need no code; logs go to `build/runs/<sketch name>/`. − hooks still need JavaScript for programs and APIs; the old layout must be converted by hand (docs/SKETCHES.md §1 maps it).

## ADR-0010: One stall rule in the run loop, for every target

*   **Status**: Accepted · **Deciders**: Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-6 AC9, UND-7 AC8
*   **Context**: Smith Gate 1: a run could wait forever once the app stopped offering moves - the step cap counts moves, so it never trips. Hookless pages make this the likely failure (a last screen with no controls).
*   **Options**: (1) one rule in `run.mjs`: 10 s with nothing offered after a move → `stalled`; (2) per-target timeouts.
*   **Decision**: (1), sharing the idle check with the first-move rule; the message says to add a `showing` guard.
*   **Consequences**: + no run hangs; the commonest authoring slip explains itself. − an app that legitimately takes over 10 s between moves needs a larger limit (not configurable yet).

## ADR-0009: The part declares where it ends (`showing`), not the generic adapter

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-7
*   **Context**: the generic page app cannot know a page's end; the owner wanted web adapters to be optional.
*   **Options**: (1) a library guard `showing { text }` over the view `look` returns; (2) a `done` field on the adapter; (3) a Jev question on every look.
*   **Decision**: (1). It works for every target and costs no Jev calls; literal text in `turn.yaml` is allowed.
*   **Consequences**: + web adapters are a name and a target. − `showing` matches substrings anywhere in the view and may over-match on large views.

## ADR-0008: HTTP target - GET-state view, request moves, error statuses are the app's answer

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-6
*   **Context**: the third target kind the owner asked for at the start; ADR-0001's interface was meant to fit it.
*   **Options**: (1) view = GET of a state path, move = adapter-defined request, 4xx/5xx returned and logged, play continues; (2) treat 4xx/5xx as a run failure.
*   **Decision**: (1), with start-on-a-free-port or attach-to-a-running-URL; only a lost connection or a dead server ends the run.
*   **Consequences**: + an API refusing a bad move is visible in the log, which is what a test wants. − no auth headers or cookies yet.

## ADR-0007: Pages are read through the accessibility snapshot; the page hook is removed

*   **Status**: Accepted (supersedes ADR-0002) · **Deciders**: owner, Morpheus · **Date**: 2026-10-15 · **Related**: UND-7
*   **Context**: owner: "ditch the special hook" - play pages that were not written for understudy, with no back-compat.
*   **Options**: (1) Playwright's `ariaSnapshot()` + `getByRole` actions; (2) raw DOM walk with CSS selectors; (3) keep the hook.
*   **Decision**: (1). Roles and visible names are what a person (and a screen reader) meets; hidden and disabled controls are handled by the browser. All hook code, fields and docs were deleted.
*   **Consequences**: + unmodified pages; web adapters optional (generic page app). − free-text fields deferred; duplicate control names use the first visible one.


## ADR-0006: `make test` never calls Jev or launches Chromium

*   **Status**: Accepted · **Deciders**: Morpheus, Tank · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, SDLC §5
*   **Context**: Jev calls cost money and need a key; Chromium is slow and machine-dependent. The gate must be cheap and repeatable.
*   **Options**: (1) unit tests with a judge double and fake/real-process targets, live runs in a separate target; (2) live calls in `make test` behind an env flag.
*   **Decision**: (1). `runPart` takes `makeJudge`/`makeTarget`; the page target takes `launch`. Live runs live in `make test-live`.
*   **Consequences**: + fast, offline gate (93 tests). − the real SDK and Chromium are exercised only at UAT; a live regression is caught later.

## ADR-0005: Exit codes 0 / 1 / 2 for every command

*   **Status**: Accepted · **Deciders**: Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-1..4
*   **Context**: Smith Gate 1 asked for consistent exit codes so scripts and people can tell failures apart.
*   **Decision**: 0 done; 1 the run started and could not finish (`RunError`, with an `outcome`); 2 refused before anything started (`UsageError`). Every failure is one `understudy: <message>` line, no stack trace.
*   **Consequences**: + one rule everywhere. − an internal bug also exits 1 (`unexpected error: ...`) — indistinguishable by code from a failed run.

## ADR-0004: An off-list answer is re-asked once, then the run stops

*   **Status**: Accepted · **Deciders**: Morpheus, Cypher · **Date**: 2026-10-15 · **Related**: UND-1 AC3
*   **Context**: recard silently played its fallback move when Jev chose something not offered. For a testing tool that hides a broken question or option list.
*   **Options**: (1) fallback and continue (recard); (2) re-ask once, then stop with exit 1; (3) stop at once.
*   **Decision**: (2). The step records `offList` and the raw answer; nothing off-list is ever sent to the app.
*   **Consequences**: + broken parts surface. − one extra Jev call per miss; recard's own tests that relied on silent fallback had to change (they now model Jev picking only offered options).

## ADR-0003: Generic `look` actor and `phase` guard

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, UND-5
*   **Context**: every recard game wrote its own `<game>_look` actor and `<game>_phase` guard.
*   **Decision**: one `look` (calls `adapter.app.phase(view)`) and one `phase` guard (`is:`). Also renamed: `TABLE`→`OBSERVE`, `table_changed`→`changed`, `quiet_table`→`quiet`, `ask_table`→`ask`, `services.peer/game`→`target/app`, option `card`→`value`.
*   **Consequences**: + both example parts are the same shape; adapters stay small (51 and 24 lines). − recard's turn files must be renamed when recard migrates (no back-compat shims, per recard's rule).

## ADR-0002: The web target drives a page hook, not the DOM

*   **Status**: Superseded by ADR-0007 (sprint 2) · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-2
*   **Context**: a web adapter needs a view and moves. recard used `window.__recardHarness`.
*   **Options**: (1) a hook the page exposes (`window[hook]`, configurable); (2) generic DOM reading (buttons, text).
*   **Decision**: (1), default `__understudy`. The hook should only read the page and press what is on it.
*   **Consequences**: + exact views, tiny adapters. − the app must cooperate; a DOM mode for unmodified pages is backlog.

## ADR-0001: Target interface `view / act / talk / say / describe / exited / close`

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, extraction map
*   **Context**: the moved core already called recard's `peer` (`view/act/talk/say`); targets must be transport-neutral (web + CLI now, HTTP next).
*   **Options**: (1) keep the peer shape, add `describe/exited/close`; (2) an event-stream interface (push observations).
*   **Decision**: (1). The process target makes a terminal-like view (lines, echoed input, `seq`, `sent`, `exited`).
*   **Consequences**: + the core changed by renaming only. − a process target must buffer output and expose `seq`; adapters must guard against answering a question twice (`questions > sent`).
