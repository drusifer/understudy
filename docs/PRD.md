# Product Requirements: understudy

*   **Status**: Active
*   **Owner**: Cypher (*pm), for the owner (a person who runs a business and a household and makes the same kinds of decisions over and over)
*   **Last Updated**: 2026-11-01
*   **Related**: [DOMAIN.md](DOMAIN.md) (vocabulary and invariants) · [SKETCHES.md](SKETCHES.md) (the reference) · [USER_GUIDE.md](USER_GUIDE.md) · [DECISIONS.md](DECISIONS.md) · [SDLC.md](SDLC.md) · [BACKLOG.md](BACKLOG.md) · epic [EPIC_PYTHON_PORT.md](sprints/EPIC_PYTHON_PORT.md) · gaps [UX_GAPS_SPRINT22.md](sprints/UX_GAPS_SPRINT22.md), [OLD_VERSION_PARITY.md](sprints/OLD_VERSION_PARITY.md)

---

## 1. Vision and Problem

People who run a small business or a household decide the same things again and again: how much coffee to order for next week, which showing and seats to book for an evening, what category a purchase belongs to. They know how they decide, but the only ways to automate it are to write a program or to hand the whole decision to a language model that may make something up. understudy lets the owner write down how they decide, in one file, and runs it the same way every time, using a judgement model only for the one thing a rule cannot read.

* **For** an owner who knows how they decide, **who** wants repeatable decisions over their own data without writing a program or trusting free-form AI output, **understudy** is a platform that runs one YAML sketch of sources, rules and weights **that** produces the same answer from the same inputs and keeps the judgement model (Jev) to choosing among options the owner listed. **Unlike** a script, a spreadsheet or a chat with a language model, a sketch is written in the owner's own rules, its judgement is bounded and recorded, and a run can be replayed offline byte for byte.

## 2. Users and Their Jobs

| User | Job they are trying to get done | Today they | Success looks like |
|---|---|---|---|
| **The owner** (shop owner, household manager) | Turn "how I decide" into a repeatable pipeline over their own files, and trust the result | Use spreadsheets and memory, or hand-written scripts; clean exports by hand | "I wrote my rules once; each week I run it, check what it did, and fix only the few cases it was unsure about" |
| **The owner, reviewing a run** | Know whether a run worked, what it produced, and why it decided what it did | Read terminal output and JSON files | "I opened the console and saw it finished, what it wrote, and which judgements were close calls" |
| **A sketch author** (the owner, or a helper) | Add a new decision, a new stage or a new example without breaking the others | Copy and edit | "A mistake is refused before the run with the file, the path and the nearest valid word" |

## 3. Goals and How We Will Know

| # | Goal | Measure | Target | Source of the number |
|---|---|---|---|---|
| G1 | The owner's real pipelines run as sketches | Number of the owner's real pipelines that run end to end with `understudy run` | 2 of 2 (the evening, the household) | `examples/`, Sprint 20 retro |
| G2 | Same inputs and same Jev answers give the same output | Two replays of one run differ by bytes | 0 bytes | `--replay` tests (`test_sketch_*`) |
| G3 | Judgement stays bounded | Values Jev wrote itself (not chosen from the owner's list) | 0 | DOMAIN invariant 6, tests |
| G4 | Few decisions need the owner's attention | Share of household records landing in category review | owner to set (1,706 of 5,074 in the 2026-10-31 real run) | `build/runs/<run>/` counts |
| G5 | The net-spending figure is trustworthy | Net spending on the real household data against a figure the owner accepts | owner to set ($433,762 on 2026-10-31 is considered suspect) | household run summary |
| G6 | A run's state is visible without a terminal | Questions the console answers without a terminal: did it finish, what it wrote, what Jev decided | all three | Sprint 22 stories |
| G7 | One toolchain keeps change cheap | Runtimes and package managers in the repo | 1 (Python and uv) | `docs/SDLC.md` |

## 4. Non-Goals

- **Playing apps like a person** (clicking pages, driving command lines, calling MCP servers). That was the first product; the owner replaced it with decisions over files (epic, 2026-10-29). The play-an-app targets are deleted.
- **Migrating or staying compatible with the old sketch format or with recard.** One kind of sketch; no shims or flags (owner rule).
- **Letting Jev write free text or numbers.** It only chooses among listed options.
- **Live sources other than files** (MCP, HTTP) in this phase; sources are read-only files.
- **Multi-user accounts, hosted service, a marketplace of sketches.** One owner on their own machine.
- **A general data-science toolkit.** Stages are small, typed and general; new ones are added only when a sketch needs them (YAGNI).

## 5. Principles and Constraints

| # | Principle or constraint | Recorded in |
|---|---|---|
| P1 | Jev chooses; it never writes. Constrained automation by design. | Owner 2026-10-15; DOMAIN invariant 6 |
| P2 | One kind of sketch, one runtime, one of everything: no back-compat, no fallbacks, flags or shims. | Owner 2026-10-15, 2026-10-29; ADR-0045, ADR-0048 |
| P3 | Define the names of things before using them; reuse existing words; one consistent way to declare and pass values. | OWNER_DECISIONS_SPRINT20 rules |
| P4 | Standard YAML 1.2 only (plus tags); sketches are Jinja2 templates; values come in with `--with`. | OWNER_DECISIONS_SPRINT20 1-3 |
| P5 | YAGNI and DRY; use established libraries rather than hand-rolled utilities. | Owner; ADR-0047 |
| P6 | Private output never goes into tracked folders or `data/`; real values are never printed in chat or logs. | UND-54 AC4; DOMAIN invariant 10 |
| P7 | Gauges and meters show real data from the run; decoration stays decoration. | Owner, Sprint 15 |
| P8 | Ask the owner only about consequential, hard-to-back-out decisions; decide the rest and note it. | Owner |
| P9 | Every build goes through `bobp make`; the owner decides when to push. | AGENTS.md; SDLC |
| P10 | American spelling in all text. | Owner |

## 6. Requirements

Status: **Delivered** (sprint), **Planned** (sprint), **Open** (not scheduled).

### 6.1 Writing and checking a sketch

| ID | Requirement | Priority | Status | Detail |
|---|---|---|---|---|
| R1 | A sketch is one YAML file with sources, sinks, outcomes, data and a machine the owner writes. | Must | Delivered S19 | SKETCHES.md "The file" |
| R2 | A sketch is a Jinja2 template; values are given with `--with name=value`, and a sketch may call another with `with:`. | Must | Delivered S20 | OWNER_DECISIONS_SPRINT20 |
| R3 | `understudy check` refuses a wrong sketch before any run, naming the file, the path, the bad value and the nearest valid one. | Must | Delivered S19 | DOMAIN invariant 1 |
| R4 | A JSON Schema lets editors complete and check a sketch. | Should | Delivered S19 | `schema/decision_sketch.schema.json` (the loader validates against it; the earlier schema for the old format was deleted) |
| R5 | A sketch may be composed of subsketches, repeated per row (`each`), with results folded (`reduce`). | Must | Delivered S20 | ADR-0047 |

### 6.2 Deciding

| ID | Requirement | Priority | Status | Detail |
|---|---|---|---|---|
| R6 | Rules are `if`/`then`/`else` trees over explicit conditions, with weights that are numbers or conditional. | Must | Delivered S19 | SKETCHES.md "Deciding" |
| R7 | A stage's deciders are blended into one weighted answer per option; a `forbid` always wins and an emptied choice fails the run unless the stage says what to do. | Must | Delivered S19 | DOMAIN invariants 3-5 |
| R8 | General stages count, convert, join, pair, link, group, classify, and find adjacent runs over rows; new stages are added in Python with a typed signature. | Must | Delivered S20 | CHANGELOG Sprint 20 |
| R9 | Options can come from the data itself (rows of a file). | Should | Delivered S20 | UND-73 |

### 6.3 Jev

| ID | Requirement | Priority | Status | Detail |
|---|---|---|---|---|
| R10 | Jev is a source: a rubric and the data it reads go in; a probability per listed level comes out; an answer outside the list is refused and asked once more. | Must | Delivered S19 | DOMAIN invariant 6 |
| R11 | Every live Jev read is captured; `--replay` runs offline from the capture and never goes live. | Must | Delivered S19 | SKETCHES.md "Capture and replay" |
| R12 | Low-confidence Jev answers can be listed so the owner can tune them. | Should | Planned S22 | UND-78 |

### 6.4 Running and outputs

| ID | Requirement | Priority | Status | Detail |
|---|---|---|---|---|
| R13 | `understudy run` writes sinks only after every stage completed, plus `run.json`, `summary.json` (counts only) and `events.jsonl`; a failed run publishes no sink. | Must | Delivered S19 | DOMAIN `Run` invariants |
| R14 | Every failure is one `understudy: <message>` line with exit code 1 (failed after start) or 2 (refused before start), never a traceback. | Must | Delivered S19 for `run` and `check`; Planned S22 for `dashboard` (a busy port prints a traceback today) | UND-80 AC1 |
| R15 | The evening (showings, ratings, seats) runs as a sketch. | Must | Delivered S20 | `examples/evening/` |
| R16 | The household (Monarch and Amex CSVs into one record per transaction with transfers, refunds and categories) runs as a sketch. | Must | Delivered S20 | `examples/household/` |
| R17 | The owner can tune the household: fewer records in review and a trustworthy net-spending figure. | Should | Open | BACKLOG; G4, G5 |

### 6.5 The console

| ID | Requirement | Priority | Status | Detail |
|---|---|---|---|---|
| R18 | A read-only console lists runs, prints their events live, shows stages and four real gauges, in three themes and light, dark or auto. | Must | Delivered S21 | UND-74 |
| R19 | The console says whether a run is going, done or failed and what it produced, and survives losing its server. | Must | Planned S22 | UND-76 |
| R20 | The owner can navigate a large run: nested stages, a filtered printer, badges on runs. | Should | Planned S22 | UND-77 |
| R21 | The owner can start, replay and stop a run from the console; only someone with the access secret may. | Should | Planned S22 | UND-79 |
| R22 | The console draws the sketch's statechart, lit with the current state and last transition. | Should | Planned S23 | OLD_VERSION_PARITY, UND-82 |
| R23 | The owner can pause, step, resume and stop a run, and watch it from `understudy run --watch`. | Should | Planned S23 | UND-83 |
| R24 | The owner can replay a finished run's story from its log with play, pause, step and step back. | Should | Planned S23 | UND-84 |
| R25 | The console shows each decision: options, rules that removed or held them, weights, blend and pick. | Should | Planned S23 | UND-85 |
| R26 | The owner can edit a sketch in the console, checked before it is saved. | Could | Planned S24 | UND-86 |
| R27 | Typed inputs (choice, weight, count, switch) with controls. | Could | Open (owner to confirm) | UND-87 |

### 6.6 Quality attributes

| ID | Attribute | Requirement | Status | Detail |
|---|---|---|---|---|
| Q1 | Reproducibility | Same files and same Jev answers give byte-identical output. | Delivered S19 | G2; DOMAIN invariant 9 |
| Q2 | Privacy | Private output is refused under `data/` and any non-ignored path; real values are not printed. | Delivered S17 | UND-54 AC4; P6 |
| Q3 | Offline | `check`, `--replay` and `bobp make test` need no key and no network. | Delivered S19 | SDLC section 5 |
| Q4 | Usability | Every error says what is wrong and how to fix it; every control is reachable by keyboard; text meets a 4.5:1 contrast ratio. | Partly delivered; Planned S22 | UND-80 |
| Q5 | Security | The console, reachable from the whole network, cannot start a process without the access secret. | Planned S22 | UND-79 AC 8, 11; Switch gate |
| Q6 | Maintainability | One toolchain, one gate (`bobp make check`) that includes tests, lint and the secret scan. | Delivered S21 | SDLC |
| Q7 | Performance | A real household run of about 5,000 records with about 900 Jev reads completes in under 5 minutes, and the whole test suite in under 30 seconds. | Delivered S20 | real run 2026-10-31: 5,074 records, 932 Jev reads, 126 s; suite 233 tests in 13 s |

## 7. Release Path

| Release or sprint | Outcome for the user | Requirements |
|---|---|---|
| Sprint 19 to 21 (done) | One Python runtime; the coffee, evening and household sketches run; a read-only console | R1-R11, R13-R16, R18 |
| Sprint 22, "trust and start" | The console says how a run went, shows inside a run and Jev's judgements, and starts runs | R12, R14, R19-R21 |
| Sprint 23, "see and drive the machine" | Diagram, pause and step, replay of a log, decision detail | R22-R25 |
| Sprint 24, "edit and tune" | Edit a sketch in the console; typed inputs if wanted | R26, R27 |
| Unscheduled | Household tuning | R17 |
| Release tag | Only when the owner asks (v0.1.0 exists on the first sprint's commit) | n/a |

## 8. Risks and Open Questions

| # | Risk or question | Who can answer | Assumed until then |
|---|---|---|---|
| 1 | Do you want typed inputs back (dial, faders, stepper, switches), or are `--with name=value` boxes enough? | Owner | Not wanted; R27 stays Open |
| 2 | What is an acceptable share of records in category review, and which net-spending figure is right? (G4, G5) | Owner | No target; R17 unscheduled |
| 3 | The console is reachable by the whole network with no login while starting runs is added. | Switch (design gate), owner | Access secret for start, stop and replay; watching stays open |
| 4 | `page.js` has no automated test. | Trin | A written browser check in the UAT plan (UND-80) |
| 5 | Jev is a paid, networked service; a missing key blocks every live run. | Owner | Replay and check work offline; the capture is committed for the coffee example |
| 6 | There is no system-level architecture document, test strategy or security baseline; each sprint has its own. | Morpheus, Trin, Switch | Written next (see the foundation gap list) |
