# understudy User Guide

How to install understudy, run a play, replay a run offline, write a play of your own, and fix what goes wrong. The cleanup of Monarch and Amex exports has its own section at the end of this part.

TLDR:
    Setup: `bobp make install`; for a run that asks Jev, `export TYPESAFE_API_KEY=...` (or put it in `.env`).
    Run: `bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"`; check without running: `ARGS="check <play>"`.
    Offline: add `--replay` to run from the last captured Jev answer, with no key and no network.
    Output: ingredient rows and a counts-only summary under `.understudy/runs/run-<stamp>-<id>/`; exit 0 / 1 / 2.
    Your own: copy `tests/fixtures/coffee/coffee_week.yaml`, change the data and the rules, `check` until it says ok.
    Reference: docs/PLAYS.md. Design: docs/sprints/STORY_ARCH_SPRINT28.md (plays) and docs/sprints/DESIGN_SKETCH_MODEL.md (the model before).

## Contents

1. [Concepts](#1-concepts)
2. [Install](#2-install)
3. [Run the coffee example](#3-run-the-coffee-example)
4. [Read the output](#4-read-the-output)
5. [Replay a run offline](#5-replay-a-run-offline)
6. [Write a play of your own](#6-write-a-play-of-your-own)
7. [Troubleshooting](#7-troubleshooting)
8. [Command reference](#8-command-reference)
9. [Local transaction cleanup](#9-local-transaction-cleanup)

---

## 1. Concepts

| Word | Meaning |
|---|---|
| **play** | one YAML file in which you write down how you decide something: its stage, outcomes, data and a scene |
| **stage** | the play's interface: the props it takes and the files it reads and writes (`kind: file`, `access: write` for an output) |
| **prop** | a value the play takes, declared on the stage with a kind and a default, given with `--with` |
| **scene / beat** | the play's body: beats that each do one action; a beat with `to:` is in the flow, one without is performed when read |
| **decision row** | one combination of outcome values with a weight; your `decide` tree, a lookup, a called play or a Jev reading can each produce them |
| **blend** | the weighted average of the decision rows its entries produce, per dimension; `forbid` rules then drop options and always win |
| **calling a play** | a beat that performs another play (`do: { play: other.yaml }`); its `with:` binds that play's props and files, and what that play writes is the beat's result |
| **Jev** | TypeSafe's judgement model. It reads text you supply against a rubric you write and gives a probability per level; it never writes a value |
| **capture / replay** | a live Jev read is saved; `--replay` reuses it offline |

The idea: **you** know how to decide. Write your rules down (if/else trees with weights), let SQL do the counting, and keep Jev for the one thing a rule cannot read, such as what a weather forecast means.

## 2. Install

Needs CPython 3.12.15 (installed for you by `uv`), `uv`, `make` and the `bobp` CLI.

```sh
bobp make install        # the locked Python environment, inside the project
```

A live run that asks Jev needs a TypeSafe key in `TYPESAFE_API_KEY` (shell, or `export TYPESAFE_API_KEY=...` in a git-ignored `.env`). Replay, `check` and plays without a Jev beat need none.

## 3. Run the coffee example

`tests/fixtures/coffee/` holds an invented shop: last week's total sales (1,600 drinks), five customer segments, a weather play it calls that has Jev compare two Almanac descriptions, and recipes for coffee beans.

```sh
bobp make run ARGS="check tests/fixtures/coffee/coffee_week.yaml"     # ok: coffee_week
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"       # live: one Jev request
```

```text
beat weather
beat weather_change.judge
beat weather_change.give
beat split_trade
beat match_orders
beat to_ingredients
beat write
wrote .understudy/runs/run-20261030T041744-28ee3978/ingredients.jsonl
```

## 4. Read the output

The run folder, `.understudy/runs/run-<stamp>-<id>/` (git-ignored and private, so `bobp make clean` cannot delete your runs):

* `ingredients.jsonl`: one row per ingredient, `{"amount": 32000, "ingredient": "coffee_beans", "unit": "g"}`, rounded up to whole packs. Written last; a failed run writes none.
* `summary.json`: counts only: total drinks, drinks per segment, the shares per segment, the weather weights, `jev_requests`, `mode` (`live` or `replay`) and `stale`.
* `run.json`: each beat of the flow complete or failed, so a failed run says where it stopped. `events.jsonl`: one JSON line per run event.

Exit codes: 0 done, 1 a beat failed after starting, 2 refused before starting (a wrong play, a missing file, no key, nothing to replay). Every failure ends with one line starting `understudy:`.

## 5. Replay a run offline

Every live Jev read is captured under `.understudy/cache/` (git-ignored; the last 5 runs). Replay never calls Jev:

```sh
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay"
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay"   # the committed real answer
```

A replay uses one run, the latest that captured every Jev beat, so everything comes from the same moment. If you changed the play or the rubric since, the run prints one line and records `stale: true`. Two replays of the same capture give byte-identical files.

## 6. Write a play of your own

1. Copy `tests/fixtures/coffee/coffee_week.yaml` (and `weather_change.yaml` if you want the weather).
2. Change the `stage` to your files (`kind: file`; JSONL, one record per line, or CSV) and props, `outcomes` to the things you decide, and `data` to your facts.
3. Write your `decide` tree: `if` / `then` / `else` over conditions such as `segment: { eq: students }`, with leaves of weighted rows that add up to 1. Add `forbid` rules for what must never happen.
4. `understudy check` until it says `ok`. It names the file, the path, the mistake and the nearest valid name.

The reference is [PLAYS.md](PLAYS.md).

## 7. Troubleshooting

| Message | Exit | What to do |
|---|---|---|
| `...: stage.sales: file ... does not exist` | 2 | the path is relative to the play file; fix it, or `--with sales=<file>` |
| `...: stage.monarch: no file given: pass --with monarch=<file>, or a call binds it` | 2 | give the file with `--with` |
| `...: unknown action 'map.split_by_shar' (did you mean 'map.split_by_share'?)` | 2 | fix the name at that path |
| `...: Additional properties are not allowed ('machine', 'sources' were unexpected)` | 2 | a sketch from before plays: rewrite it as a play (see PLAYS.md) |
| `...: 'larg' is not an option of size (did you mean 'large'?)` | 2 | use an option declared under `outcomes` |
| `...: data.segments: shares add up to 1.1, not 1` | 2 | make the shares add up to 1 |
| `...: weights add up to 1.4, not 1` | 2 | a leaf's weights must add up to 1 |
| `Jev needs a TypeSafe key: set TYPESAFE_API_KEY` | 2 | export the key, or run with `--replay` |
| `no saved run captured <source>; do a live run first` | 2 | there is nothing to replay yet: run once without `--replay` |
| `forbid rule 0 left teens with no option for 'caffeine'` | 1 | a rule dropped every option for that segment; relax the rule, or give the beat `on_empty: skip` or `fallback` |
| `beat match_orders: 'weather' returned temp='ice', not a declared option` | 1 | a piece returned an option that `outcomes` does not declare |
| `cannot write to ...: it is inside the project and not git-ignored` | 2 | use `.understudy/runs` (the default) or another git-ignored path or a path outside the project |
| `understudy: no .venv - run 'bobp make install' first` | 2 | the Python environment is missing |

## 8. Command reference

```text
understudy run <play.yaml> [--with name=value]... [--out folder] [--replay[=run-id|folder]] [--watch [--pause] [--port N]]
understudy check <play.yaml> [--with name=value]...
understudy dashboard [runs-folder] [--port 4180] [--plays examples]
understudy runs [runs-folder]
```

Run them as `bobp make run ARGS="<command> ..."`, or `bin/understudy <command> ...`.

A run records the `--with` values it was given in its `run.json`, and the console shows them to anyone who can open it. Pass props (dates, weights) and the paths of stage files (`--with monarch=data/monarch.csv`); never a password or key.

`understudy runs` lists the runs in a folder, newest first, with how each ended. A finished `understudy run` prints its run id and how to watch it.

### The console

**Hold and step a run.** `understudy run <play> --watch` also opens a console for that one run, on this machine only (`http://127.0.0.1:<port>`, a free port unless you give `--port`), and prints its address; `--pause` starts the run held before its first beat, and `--stop-at <beat>` runs up to a beat of the flow (not a final one) and holds before it (both need `--watch`, and without it the command stops with `understudy: --pause needs --watch`; a beat that is not in the flow is refused with the beats there are). In the console (unlock with the access secret) PAUSE holds a running run before its next beat, STEP lets exactly one beat run and holds again, RESUME runs on, and STOP ends it. A beat that is already running, Jev requests included, finishes first; nothing starts, and Jev is not asked, while the run is held. A held run reads PAUSED (never stalled), however long it waits, and says `paused before <beat>`. The console started by `understudy dashboard` can do the same for the runs it started. The hold is a small file, `control.json`, in the run's folder (`{"mode", "steps"}`, and `stop_at` for a beat to hold before; the next pause, step or resume rewrites it without `stop_at`); the run's events gain `paused` and `resumed` lines. After a watched run ends the console stays up until Ctrl-C, so you can read how it ended.

**Replay a run's story.** Choose a run that has ended (done, failed or stopped) and press REPLAY above the log. A bar opens with STEP BACK, PLAY (it becomes PAUSE), STEP, a scrubber and "event N of M"; the beat tube, gauges, diagram and printed lines show the run as it was after event N, and the status reads REPLAY. LIVE closes the bar and shows the run as it is. A replay reads only the run's `events.jsonl`: it makes no Jev request and changes nothing. A log with a line that cannot be read is refused with one line naming it (`events.jsonl line 4 is not readable`), and a run with no events says so. The Jev request count shows `-` until the last event, because the log does not record it event by event. The same data is at `GET /api/runs/<id>/replay` (the number of events) and `?at=N` (the run after N events).

**See a decision.** A run whose play decides (a `reduce.blend` beat) logs one `decision` line per input row and dimension. Each is printed in the run log (`decision match: teens temp = hot (0.7)`) and drawn in the beat box (below) as one bar per option with the picked one marked; an option something removed says `(removed)`. While a replay is open, a click on a decision's line in the log moves the replay to that event. The weights are the blended result: the log does not record each decider's own weight. The list is also at `GET /api/runs/<id>/decisions`.

`understudy dashboard` serves the console on port 4180 of every network interface (`http://<this machine>:4180/`), over the runs under `.understudy/runs` (or the folder you give). There is no login for watching, so use it on a network you trust. A busy port, or a folder that is not a folder, is one plain line and exit 2.

* **The rack** lists the runs grouped by play, newest first; a run that is going, failed, stalled or stopped carries a badge in words, and a run from before plays reads unreadable. The header says RUNNING, DONE, FAILED, STOPPED or STALLED.
* **A failed run** shows a banner with the beat and the reason; press it to see that line in the printer. The summary under the gauges gives the outcome, mode, duration, the `--with` values and each output with its row count.
* **The printer** shows the run's events (new lines appear while it runs). Filter by text, by beat, or failures only; jump to the start, the first failure or the end.
* **The beat box** shows one beat: what goes IN, the beat, what comes OUT, as small charts rather than text. It follows the beat the run is on (or, when the run is on its last beat or over, the last beat that did something); click another beat on the diagram to look at it, and click it again to follow the run. Each input and output is a card with its name and row count and up to three charts of its columns: a **gauge** for a number (its range, with the mean marked), a **donut** for a text column with up to four values, **bars** for the commonest five of more. A column with one value is just said. A beat that runs once per row (a play called with `each`) shows **one pass at a time**: that pass's row as labeled values (not the whole list), what the pass made, and a stepper (`<`, `pass 3 of 60`, `>`) over the latest 40 passes; it looks back over passes, it does not hold the run between them. **Jev's answers** are bars from 0 to 1 per level (the top one marked, `UNSURE` below 0.7 or for `none_of_these`), and a blend's decisions are weight bars. A beat not yet run shows what it will read from the plan. Level names and values are shown as they are (there is no login).
* **The run header** under the run's ending line gives the mode, how long it took, whether its Jev captures are stale, what it was given and what it wrote. Four gauges read the run's own files (including how sure Jev was and how many answers were asked against reused); a needle appears only where the run knows the full scale.
* **START A RUN** (open the panel at the top): choose a play, fill in its props and, if you want other files than its own, the paths of the files it reads (each box says whether it may be left empty), and press PLAY, live or from a captured run. "Replay from" lists only the captured runs of the picked play, each with its name. The console checks the play with your values first and tells you what is wrong. STOP THIS RUN ends a run the console started. A play that is only called by another is not listed, and a file that cannot be read is listed greyed out with the reason.
* **Typed controls:** a play that declares props on its stage (see `docs/PLAYS.md`) shows a control for each, set to its default: a choice is a row of options (arrow keys move, stopping at the ends), a range a slider with its value beside it, a count a number with a button either side, a switch ON or OFF. A control cannot be set outside its limits, and PLAY sends every value (the defaults for the ones you left alone). A name the play takes without declaring it stays a plain text box.
* **The run view by width:** from 1400 px wide, three columns (the printer, the readouts, and the diagram with its step view, which stays in view as you scroll); from 1101 px, two columns with the diagram under both; below that, one column (readouts, diagram, printer). The printer's paper is as tall as its lines. The page does not scroll sideways at any width, including a 50 percent zoom.
* **The run rack** shows each play's newest 8 runs (and the run you chose, wherever it is) and a button `N older` for the rest (`fewer` folds them again). Runs the console cannot read (from before Sprint 29) are in one folded group, `N unreadable`.
* **One diagram:** the page has one diagram. It follows what you chose last: a run tab shows that run (`DIAGRAM OF RUN <time>`); picking a play in START A RUN, or pressing SHOW PLAN, shows that play's plan (`PLAN OF <play>`) in the same place. Starting a run, or choosing a tab, brings the run back. It is described below.
* **A big play is drawn as its flow.** A play of more than 40 nodes (household has 152) shows its files and the beats of its flow (31 nodes for household); the beats that wait to be read are left out, and each flow beat shows the files and flow beats those beats read. A button above the diagram, `SHOW ALL <n> NODES`, shows everything, and `SHOW ONLY THE FLOW` goes back. The button is there only when something is hidden, and it works for a plan, a run and a replay. The choice is kept until you reload the page.
* **What the run log says:** each line is one thing that happened. `next weighed` is the scene moving to a beat; `start` and `done` bracket it, and a `done` line says what the beat did: `done weighed  map.weigh  in: joined 12, films 8  made 5 rows` (what it read and how many rows, and what it made or wrote). Each Jev answer is a line: `jev evening.pick: Paddington 2 18:00 0.67 (then Parasite 19:00 0.28; 5 options)`, the level it chose, how sure it was, the runner-up and how many options there were. A blend's decisions, holds (`paused before pick`) and failures have their own lines.
* **What the boxes say:** under each beat's name is what it does (`map.where`, `reduce.max`, `jev.choice`, `play:review_score.yaml`, `write:booking`), and under each file's name its path. The first beat is marked START. Once a beat has run, a small tag above its box gives the rows it made (or wrote). A legend above the diagram explains the shapes and arrows.
* **The play diagram:** the whole play drawn from the first beat downward: the stage's files as rounded tags (a file the play writes in a warmer color), beats as boxes (a double border for a final beat, a dashed border for a beat that waits until another reads it), a solid arrow for each move (labeled with its guard when it has one, dashed red for a loop back), a fine dotted arrow from each file or beat to the beat that reads it, and a green arrow from a `write` beat to its file. The beat the run is on is lit and the move just taken is orange; it follows a live run within a second and keeps the last beat lit with how the run ended. A big play scrolls inside its box. A run recorded before Sprint 29 has no plan, so it says so and draws nothing.
* **The plan of a play, before any run:** the picked play's plan shows what feeds what without reading the YAML. Click a beat of the flow (or tab to it and press Enter) and the next run holds before it; click it again to clear. PLAY then runs at full speed up to that beat and holds there (`paused before <beat>`), and STEP, RESUME and STOP work as for any held run. START HELD holds before the first beat instead. A beat that is never reached ends the run with `never reached <beat>, the beat it was to hold before`.
* **Where the money went:** a run that wrote `spending.jsonl` lists its ten largest spending categories under the summary, with amount and share, and "and N more".
* **There is no login** (owner decision 44): anyone who can reach the console's port can watch, start, replay and stop runs, and sees Jev's level names. Keep it on a network you trust. Another website's page cannot start a run (the console refuses a request from another origin).
* **Three themes and light, dark or auto** are remembered by the browser; on a phone the theme controls sit behind LOOK.

To check the console after a change: `bobp make install-browser`, then `bobp make test-browser` (needs Chromium; it drives the real page and measures text contrast in all six looks).

| Make target (`bobp make <target>`) | Does |
|---|---|
| `install` | install dependencies (network) |
| `run` | `ARGS="run <play> [--with name=value]..."` or `"check <play>"` |
| `dashboard` | the console over `.understudy/runs` (`ARGS="--port 4180 --plays examples"`) |
| `test` / `lint` / `check` | unit tests / ruff / the full gate with the secret scan |
| `security-scan` | gitleaks and pip-audit over every dependency group (network); clean before a release |
| `install-browser` / `test-browser` | the optional browser tools / the console in a real Chromium |
| `clean` | remove `build/` |

## 9. Local transaction cleanup

The household cleanup is an ordinary play, `examples/household/household.yaml`, built from the same parts as
any other: stage files (a file whose name ends in `.csv` is read with its header row as the field names),
general actions, two plays it calls that ask Jev (`categorize_merchant`, `link_refund`), and checks and writes in
its scene's flow.

```sh
bobp make run ARGS="run examples/household/household.yaml --with monarch=data/monarch.csv --with amex=data/amex.csv --with amex_account=Platinum --with since=2026-01-01"
```

This needs `TYPESAFE_API_KEY` and the locked Python environment (`bobp make install`). `monarch` and `amex` are
files on the play's stage, so `--with` gives their paths, read relative to where you run the command.
`amex_account` is a part of the card's account name in Monarch (required: only Monarch rows on that account are
paired with the Amex rows). `since` is the first date of the period (default: no limit); earlier rows are left out
and undated rows are kept as `invalid`.

What it does, in order:

1. Reads the two exports; a charge in both (same date and amount, the same text first, then in file order, then
   within three business days) is one record.
2. Links the two halves of a card payment: opposite amounts in different accounts, within three business days. The
   records it tries are chosen from their own text (payment words in the description, statement or merchant name, and
   the card export's "payment received" lines), never from your export's category, so a payment whose category says
   something else still links. The links are in `legs.jsonl`.
3. Puts each merchant (every payee that is not one half of a linked payment) in a category of the clean list (below), in two choices by Jev (`categorize_merchant`): a
   group first (shown every name in each), then a name in that group, or none of them. Jev only chooses; it never
   writes a category, and it never sees your export's own categories. A choice counts when it is above 0.7, or at
   least 0.4 and at least twice as sure as the runner-up (a long list spreads the probability); when both choices
   count the merchant is placed (`category_source: jev` on its records), otherwise it goes to `review.jsonl`. A merchant you have
   pinned (below) is placed in your category and never asked about. A live run asks about every merchant (about two
   requests each, 2,000 or so and about seven minutes for a year of the household's data), and Jev's answers vary a
   little from run to run near the thresholds; `--replay <run>` reuses a run's captured answers (no requests, the
   same result), which is how to change a pin or a rule and see the effect.
4. Types each record. It is a transfer (money moving between your own accounts, never income, a refund or
   spending) when step 2 linked it, or when its merchant's category is "Household: Transfer" (Jev's choice, or your
   pin), or when a card's own text says it is a payment received (`PAYMENT RECEIVED`, `PAYMENT, THANK YOU`) even if
   its bank side is not in the data; the export's `Category` never decides. `summary.json` counts the transfers
   `transfer_basis`: by `link`, by `category`, `both`, by `payment`, and `none` for every other record. A merchant still for review keeps its records as purchases
   or credits until it is placed or pinned.
5. Links each refund (money in that is not in "Household: Income") to the earlier charge it reversed: by rule when
   there is one, by Jev (`link_refund`) when there are several.
6. Writes `crosswalk.jsonl`: every merchant, biggest first, with the category the tool chose and the export's most
   common category side by side, and `differs_on_money_moving` where the tool and the export's own labels disagree
   about whether the money was a transfer; the summary counts them (`crosswalk_flagged`).
7. Ties each card payment to the charges it settled: for the Amex export, a payment settles that card's charges
   oldest first by the card's own dates (a day's charges smallest first), never past its amount, never a charge dated
   after it, and a charge in at most one payment. `payments.jsonl` has one line per payment (`payment_id`, `day`,
   `card`, `amount`, `charges` settled, `settled` amount, `remainder`, `unexplained` when more than 5% of the payment
   has no earlier charge to explain it, and `top`: its five largest categories with `amount` and `share`). Each card
   charge in `records.jsonl` has `settled_by` (the payment's id, or null while it is open), and `summary.json` has
   `open_balance` (the count and amount of charges after the last payment). A card with no payments has no lines and
   every charge open.

**Pinned categories.** `review.jsonl` is your work list. To settle a merchant, add a line to your pin file, one JSON
object per line: `{"payee": "Amazon", "category": "Retail outlets: Book stores"}`. The category must be in the
clean list (see below and `taxonomy.jsonl` in the run folder): an ISO 18245 category or one of your own additions;
the merchant's spelling may differ in case and spacing. The next run places that merchant's records in the category, marks them
`category_source: pin`, makes no Jev request for it and leaves it out of `review.jsonl`. The pin file is
`.understudy/pinned.jsonl` (read from where you run, git-ignored) unless you pass `--with pinned=<path>`. If the
default file is not there the run says so and has no pins; a path you pass that does not exist, a line without a
`payee` or `category`, or a category that is not in the clean list stops the run before any request to Jev and names
the line.

**The clean list of categories.** Your export's own categories are not used. The list is the ISO 18245 merchant
categories (13 groups, 280 names, each written `Group: Name`) plus your own additions where ISO has no good match.
`examples/household/additions.jsonl` ships with six under the group `Household`: Rent, Mortgage, Tuition, Income,
Transfer and Loan repayment. Copy it, edit it (one `{"group": ..., "name": ...}` per line) and pass
`--with additions=<path>`. A path that does not exist, a line without a group or a name, or a name that repeats an
ISO name or an earlier line stops the run before any request to Jev and names the line. The whole list is written to
`taxonomy.jsonl` in the run folder (`group`, `name`, `category`, and `origin`: `iso` or `owner`).

Each run creates a new folder under `.understudy/runs/` (or `--out`): `records.jsonl` (one record per transaction with its
`kind`: purchase, refund, credit, transfer or invalid; its link and its category), `legs.jsonl`,
`kinds.jsonl` and `statuses.jsonl` (counts), `review.jsonl` (one line per merchant Jev was not sure of, most records first: `payee`, `count`, `amount`, Jev's `top` and `runner_up` categories with their probabilities, and the `reason`, `below_0.7` or `none_of_these`; empty when nothing needs review), `spending.jsonl` (what the money goes on: one line per category, biggest first, with `count`, `amount` spent and `share` of all spending; a record's category is the tool's own (Jev's or your pin), `unplaced` for a merchant still for review, and never the export's `Category`; purchases and refunds only, so a refund lowers its category, and income, credits and transfers are not in it; the total is `spending_total` in `summary.json`), `totals.jsonl` (for each account, the money in, money out and net of its purchases, refunds and credits, transfers left out, then one `all` row; the `all` row is also `net_spending` in `summary.json`), `summary.json` (run facts) and `run.json`. Amounts
are signed as Monarch writes them: purchases negative, refunds positive. A failed beat publishes no output.
Keep household inputs and outputs in ignored `data/` and `build/` folders.
