# understudy User Guide

How to install understudy, run a sketch, replay a run offline, write a sketch of your own, and fix what goes wrong. The cleanup of Monarch and Amex exports has its own section at the end of this part.

TLDR:
    Setup: `bobp make install`; for a run that asks Jev, `export TYPESAFE_API_KEY=...` (or put it in `.env`).
    Run: `bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml"`; check without running: `ARGS="check <sketch>"`.
    Offline: add `--replay` to run from the last captured Jev answer, with no key and no network.
    Output: ingredient rows and a counts-only summary under `build/runs/run-<stamp>-<id>/`; exit 0 / 1 / 2.
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

Needs CPython 3.12.15 (installed for you by `uv`), `uv`, Node 24 (only the launcher), `make` and the `bobp` CLI.

```sh
bobp make install        # locked Python and Node environments, inside the project
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
wrote build/runs/run-20261030T041744-28ee3978/ingredients.jsonl
```

## 4. Read the output

The run folder, `build/runs/run-<stamp>-<id>/`:

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
| `cannot write to ...: it is inside the project and not git-ignored` | 2 | use `build/runs` (the default) or a path outside the project |
| `library is being rebuilt for the new sketch model` (also `watch`, `dashboard`) | 2 | those commands arrive again when the examples and dashboard are rebuilt |
| `could not start Python: ...; run bobp make install` | 2 | the Python environment is missing |

## 8. Command reference

```text
understudy run <sketch.yaml> [--source name.path=file]... [--out folder] [--replay[=run-id|folder]]
understudy check <sketch.yaml> [--source name.path=file]...
understudy etl run --monarch <csv> --amex <csv> [--out <folder>] [--since YYYY-MM-DD] [--amex-account <name>]
understudy --help
```

Run them as `bobp make run ARGS="<command> ..."`.

| Make target (`bobp make <target>`) | Does |
|---|---|
| `install` | install dependencies (network) |
| `run` | `ARGS="run <sketch>"`, `"check <sketch>"` or `"etl run ..."` |
| `test` / `lint` / `check` | unit tests (JavaScript launcher, Python, SQLMesh) / eslint and ruff / the full gate with the secret scan |
| `clean` | remove `build/` |

## 9. Local transaction cleanup

```sh
bobp make run ARGS="etl run --monarch data/monarch.csv --amex data/amex.csv --since 2026-01-01 --out build/runs"
```

This needs `TYPESAFE_API_KEY` and the locked Python environment (`bobp make install`).
The two CSVs must be the complete Monarch and Amex exports with their original column names.
Each is served through its own local MCP source server; input snapshots retain every source column.

The default period starts at the Amex export's first date; `--since YYYY-MM-DD` overrides it.
Earlier rows are counted and excluded; undated rows are retained as invalid. The Monarch Amex
account is detected from opposite-sign matches. If detection ties or finds none, pass
`--amex-account <distinctive account text>`.

Each run creates a new folder under `build/runs/`, or the folder supplied with `--out`:

- `result.jsonl`: one transaction per line, including original `source_rows`, date, signed amount,
  merchant, account, category and confidence, transfer partner and refund link and confidence.
- `summary.json`: source and result counts, merged purchases, transfer counts and amounts,
  net spending (purchases less refunds, transfers excluded), category counts, and review counts.
- `run.json`, input snapshots, `run.duckdb`, and `sqlmesh.log`: local run diagnostics.

`result.jsonl` replaces Sprint 16's `review.csv`; consumers must use the new JSONL fields.
Purchases are negative, refunds positive. Transfer amounts in the summary sum absolute leg
amounts, so a paired transfer contributes both legs. External transfers are listed by payee.
Categories are chosen from the offered Monarch labels or the MCC list; uncertain answers remain
for review. The same inputs and Jev answers produce byte-identical result and summary files.
A failed stage stops the run and publishes no result. Keep household inputs and outputs in
ignored `data/` and `build/` folders.
