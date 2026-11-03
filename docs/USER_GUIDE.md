# understudy User Guide

How to install understudy, run a sketch, replay a run offline, write a sketch of your own, and fix what goes wrong. The cleanup of Monarch and Amex exports has its own section at the end of this part.

TLDR:
    Setup: `bobp make install`; for a run that asks Jev, `export TYPESAFE_API_KEY=...` (or put it in `.env`).
    Run: `bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"`; check without running: `ARGS="check <sketch>"`.
    Offline: add `--replay` to run from the last captured Jev answer, with no key and no network.
    Output: ingredient rows and a counts-only summary under `.understudy/runs/run-<stamp>-<id>/`; exit 0 / 1 / 2.
    Your own: copy `tests/fixtures/coffee/coffee_week.yaml`, change the data and the rules, `check` until it says ok.
    Reference: docs/SKETCHES.md. Design: docs/sprints/DESIGN_SKETCH_MODEL.md.

## Contents

1. [Concepts](#1-concepts)
2. [Install](#2-install)
3. [Run the coffee example](#3-run-the-coffee-example)
4. [Read the output](#4-read-the-output)
5. [Replay a run offline](#5-replay-a-run-offline)
6. [Write a sketch of your own](#6-write-a-sketch-of-your-own)
7. [Troubleshooting](#7-troubleshooting)
8. [Command reference](#8-command-reference)
9. [Local transaction cleanup](#9-local-transaction-cleanup)

---

## 1. Concepts

| Word | Meaning |
|---|---|
| **sketch** | one YAML file in which you write down how you decide something: its sources, sinks, outcomes, data and a machine |
| **source / sink** | a named input (JSONL file, or Jev) and a named output (a file in the run folder) |
| **machine** | your pipeline: states that each name a stage and say what comes next |
| **decision row** | one combination of outcome values with a weight; your `decide` tree, a lookup, a subsketch or a Jev reading can each produce them |
| **blend** | the weighted average of the decision rows its entries produce, per dimension; `forbid` rules then drop options and always win |
| **subsketch** | a sketch another sketch calls (`do: { sketch: { file: ... } }`); it declares the `outputs` it gives back, and the caller passes it values with `with:` |
| **Jev** | TypeSafe's judgement model. It reads text you supply against a rubric you write and gives a probability per level; it never writes a value |
| **capture / replay** | a live Jev read is saved; `--replay` reuses it offline |

The idea: **you** know how to decide. Write your rules down (if/else trees with weights), let SQL do the counting, and keep Jev for the one thing a rule cannot read, such as what a weather forecast means.

## 2. Install

Needs CPython 3.12.15 (installed for you by `uv`), `uv`, `make` and the `bobp` CLI.

```sh
bobp make install        # the locked Python environment, inside the project
```

A live run that asks Jev needs a TypeSafe key in `TYPESAFE_API_KEY` (shell, or `export TYPESAFE_API_KEY=...` in a git-ignored `.env`). Replay, `check` and sketches without a Jev source need none.

## 3. Run the coffee example

`tests/fixtures/coffee/` holds an invented shop: last week's total sales (1,600 drinks), five customer segments, a weather subsketch that has Jev compare two Almanac descriptions, and recipes for coffee beans.

```sh
bobp make run ARGS="check tests/fixtures/coffee/coffee_week.yaml"     # ok: coffee_week
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"       # live: one Jev request
```

```text
stage weather
stage weather_change.judge
stage split_trade
stage match_orders
stage to_ingredients
stage write
wrote .understudy/runs/run-20261030T041744-28ee3978/ingredients.jsonl
```

## 4. Read the output

The run folder, `.understudy/runs/run-<stamp>-<id>/` (git-ignored and private, so `bobp make clean` cannot delete your runs):

* `ingredients.jsonl`: one row per ingredient, `{"amount": 32000, "ingredient": "coffee_beans", "unit": "g"}`, rounded up to whole packs. Written last; a failed run writes none.
* `summary.json`: counts only: total drinks, drinks per segment, the shares per segment, the weather weights, `jev_requests`, `mode` (`live` or `replay`) and `stale`.
* `run.json`: each stage complete or failed, so a failed run says where it stopped. `events.jsonl`: one JSON line per run event.

Exit codes: 0 done, 1 a stage failed after starting, 2 refused before starting (a wrong sketch, a missing file, no key, nothing to replay). Every failure ends with one line starting `understudy:`.

## 5. Replay a run offline

Every live Jev read is captured under `.understudy/cache/` (git-ignored; the last 5 runs). Replay never calls Jev:

```sh
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay"
bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay"   # the committed real answer
```

A replay uses one run, the latest that captured every source, so everything comes from the same moment. If you changed the sketch or the rubric since, the run prints one line and records `stale: true`. Two replays of the same capture give byte-identical files.

## 6. Write a sketch of your own

1. Copy `tests/fixtures/coffee/coffee_week.yaml` (and `weather_change.yaml` if you want the weather).
2. Change `sources` to your files (JSONL, one record per line), `outcomes` to the things you decide, and `data` to your facts.
3. Write your `decide` tree: `if` / `then` / `else` over conditions such as `segment: { eq: students }`, with leaves of weighted rows that add up to 1. Add `forbid` rules for what must never happen.
4. `understudy check` until it says `ok`. It names the file, the path, the mistake and the nearest valid name.

The reference is [SKETCHES.md](SKETCHES.md).

## 7. Troubleshooting

| Message | Exit | What to do |
|---|---|---|
| `...: sources.sales: file ... does not exist` | 2 | the path is relative to the sketch file; fix it, or `--source sales.path=<file>` |
| `...: unknown stage 'map.split_by_shar' (did you mean 'map.split_by_share'?)` | 2 | fix the name at that path |
| `...: 'larg' is not an option of size (did you mean 'large'?)` | 2 | use an option declared under `outcomes` |
| `...: data.segments: shares add up to 1.1, not 1` | 2 | make the shares add up to 1 |
| `...: weights add up to 1.4, not 1` | 2 | a leaf's weights must add up to 1 |
| `Jev needs a TypeSafe key: set TYPESAFE_API_KEY` | 2 | export the key, or run with `--replay` |
| `no saved run captured <source>; do a live run first` | 2 | there is nothing to replay yet: run once without `--replay` |
| `forbid rule 0 left teens with no option for 'caffeine'` | 1 | a rule dropped every option for that segment; relax the rule, or give the stage `on_empty: skip` or `fallback` |
| `stage match_orders: 'weather' returned temp='ice', not a declared option` | 1 | a source returned an option that `outcomes` does not declare |
| `cannot write to ...: it is inside the project and not git-ignored` | 2 | use `.understudy/runs` (the default) or another git-ignored path or a path outside the project |
| `understudy: no .venv - run 'bobp make install' first` | 2 | the Python environment is missing |

## 8. Command reference

```text
understudy run <sketch.yaml> [--with name=value]... [--source name.path=file]... [--out folder] [--replay[=run-id|folder]]
understudy check <sketch.yaml> [--with name=value]... [--source name.path=file]...
understudy dashboard [runs-folder] [--port 4180] [--sketches examples]
understudy runs [runs-folder]
```

Run them as `bobp make run ARGS="<command> ..."`, or `bin/understudy <command> ...`.

A run records the `--with` values it was given in its `run.json`, and the console shows them to anyone who can open it. Pass file names, dates and weights; never a password or key.

`understudy runs` lists the runs in a folder, newest first, with how each ended. A finished `understudy run` prints its run id and how to watch it.

### The console

`understudy dashboard` serves the console on port 4180 of every network interface (`http://<this machine>:4180/`), over the runs under `.understudy/runs` (or the folder you give). There is no login for watching, so use it on a network you trust. A busy port, or a folder that is not a folder, is one plain line and exit 2.

* **The rack** lists the runs grouped by sketch, newest first; a run that is going, failed, stalled or stopped carries a badge in words. The header says RUNNING, DONE, FAILED, STOPPED or STALLED.
* **A failed run** shows a banner with the stage and the reason; press it to see that line in the printer. The summary under the gauges gives the outcome, mode, duration, the `--with` values and each output with its row count.
* **The printer** shows the run's events (new lines appear while it runs). Filter by text, by stage, or failures only; jump to the start, the first failure or the end.
* **The stage tube** shows one lamp per top-level stage; the child sketches that ran inside it are groups you can open (`25 of 25 done`). Four gauges read the run's own files; a needle appears only where the run knows the full scale.
* **JEV READS** lists what Jev answered in the run (from the captured answers; the last five runs keep them): each read's levels and probabilities, flagged UNSURE when the top level is below 0.7 or is `none_of_these`. Level names that come from your own data (a refund candidate named by its date and amount) show as "option N" unless you have unlocked the console.
* **START A RUN** (open the panel at the top): unlock with the access secret, choose a sketch, fill in its values, and press PLAY, live or from a captured run. The console checks the sketch with your values first and tells you what is wrong. STOP THIS RUN ends a run the console started. A sketch that is only called by another is not listed, and a file that cannot be read is listed greyed out with the reason.
* **Typed controls:** a sketch that declares its `inputs` (see `docs/SKETCHES.md`) shows a control for each, set to its default: a choice is a row of options (arrow keys move, stopping at the ends), a range a slider with its value beside it, a count a number with a button either side, a switch ON or OFF. A control cannot be set outside its limits, and PLAY sends every value (the defaults for the ones you left alone). A name the sketch takes without declaring it stays a plain text box.
* **Where the money went:** a run that wrote `spending.jsonl` lists its ten largest spending categories under the summary, with amount and share, and "and N more".
* **The access secret** is new at every start of the console and saved in `.understudy/dashboard.secret` (readable by you alone, git-ignored). Read it there (`cat .understudy/dashboard.secret`) and paste it into the panel; it is kept for that tab only. It is never printed, because command output is copied into the team chat. Without it you can watch but not start, replay or stop. It travels over plain HTTP, which you accepted for a home network (until 2027-01-30).
* **Three themes and light, dark or auto** are remembered by the browser; on a phone the theme controls sit behind LOOK.

To check the console after a change: `bobp make install-browser`, then `bobp make test-browser` (needs Chromium; it drives the real page and measures text contrast in all six looks).

| Make target (`bobp make <target>`) | Does |
|---|---|
| `install` | install dependencies (network) |
| `run` | `ARGS="run <sketch> [--with name=value]..."` or `"check <sketch>"` |
| `dashboard` | the console over `.understudy/runs` (`ARGS="--port 4180 --sketches examples"`) |
| `test` / `lint` / `check` | unit tests / ruff / the full gate with the secret scan |
| `security-scan` | gitleaks and pip-audit over every dependency group (network); clean before a release |
| `install-browser` / `test-browser` | the optional browser tools / the console in a real Chromium |
| `clean` | remove `build/` |

## 9. Local transaction cleanup

The household cleanup is an ordinary sketch, `examples/household/household.yaml`, built from the same parts as
any other: file sources (a file whose name ends in `.csv` is read with its header row as the field names),
general stages, child sketches that ask Jev, and a fold.

```sh
bobp make run ARGS="run examples/household/household.yaml --with monarch=data/monarch.csv --with amex=data/amex.csv --with amex_account=Platinum --with since=2026-01-01"
```

This needs `TYPESAFE_API_KEY` and the locked Python environment (`bobp make install`). A `--with` value that names
an existing file is read relative to where you run the command.
`amex_account` is a part of the card's account name in Monarch (required: only Monarch rows on that account are
paired with the Amex rows). `since` is the first date of the period (default: no limit); earlier rows are left out
and undated rows are kept as `invalid`.

What it does, in order:

1. Reads the two exports; a charge in both (same date and amount, the same text first, then in file order, then
   within three business days) is one record.
2. Links the two halves of a card payment (opposite amounts in different accounts, within three business days).
3. Types each record. It is a transfer (money moving between your own accounts, never income, a refund or
   spending) when its Monarch `Category` is `Transfer` or `Credit Card Payment`, or ends in `: Credit Card Payment`,
   `: Transfer` or `: Transfers` (the forms with a group in front), or when step 2 linked it to a record in another
   account, whatever its category. Any other record is not a transfer. The links stay in `legs.jsonl`, and
   `summary.json` counts the transfers `transfer_basis`: by `label`, by `link`, `both`, and `none` for every other
   record. The Monarch file must have a `Category` column; without one the run stops before it asks Jev anything.
4. Links each refund to the earlier charge it reversed: by rule when there is one, by Jev (`link_refund`) when
   there are several.
5. Places each merchant in a category already in use (`place_merchant`) or, when none fits, names one: a category
   named earlier in the run first, then a kind of business and a name from the ISO 18245 list (`name_merchant`,
   run `each` merchant with `reduce` so each one sees the names given before it). A merchant you have pinned
   (below) is placed in your category and never asked about.

**Pinned categories.** `review.jsonl` is your work list. To settle a merchant, add a line to your pin file, one JSON
object per line: `{"payee": "Amazon", "category": "Business & Professional: Online Shopping"}`. The category must be
one your Monarch export already uses (a Transfer or Credit Card Payment category is not offered); the merchant's
spelling may differ in case and spacing. The next run places that merchant's records in the category, marks them
`category_source: pin`, makes no Jev request for it and leaves it out of `review.jsonl`. The pin file is
`.understudy/pinned.jsonl` (read from where you run, git-ignored) unless you pass `--with pinned=<path>`. If the
default file is not there the run says so and has no pins; a path you pass that does not exist, a line without a
`payee` or `category`, or a category the export does not use stops the run before any request to Jev and names the
line.

Each run creates a new folder under `.understudy/runs/` (or `--out`): `records.jsonl` (one record per transaction with its
`kind`: purchase, refund, credit, transfer or invalid; its link and its category), `legs.jsonl`,
`kinds.jsonl` and `statuses.jsonl` (counts), `review.jsonl` (one line per merchant Jev was not sure of, most records first: `payee`, `count`, `amount`, Jev's `top` and `runner_up` categories with their probabilities, and the `reason`, `below_0.7` or `none_of_these`; empty when nothing needs review), `spending.jsonl` (what the money goes on: one line per category, biggest first, with `count`, `amount` spent and `share` of all spending; a record's category is your export's own `Category`, else the one Jev placed it in, else `uncategorized`; purchases and refunds only, so a refund lowers its category, and income, credits and transfers are not in it; the total is `spending_total` in `summary.json`), `totals.jsonl` (for each account, the money in, money out and net of its purchases, refunds and credits, transfers left out, then one `all` row; the `all` row is also `net_spending` in `summary.json`), `summary.json` (run facts) and `run.json`. Amounts
are signed as Monarch writes them: purchases negative, refunds positive. A failed stage publishes no output.
Keep household inputs and outputs in ignored `data/` and `build/` folders.
