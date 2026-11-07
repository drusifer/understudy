# Changelog

## Sprint 31 — a big play folded to its flow (2026-11-06, branch `sprint-31`, not yet merged)

- **The diagram of a play of more than 40 nodes shows its flow:** the stage's files and the flow beats, with the waiting beats left out and their reads passed through (household: 152 nodes down to 31). `SHOW ALL <n> NODES` / `SHOW ONLY THE FLOW` switches, for a plan, a run and a replay. `fold` in `src/play/plan.py`; `view=auto|flow|all` on `GET /api/plan`, `/api/runs/<id>` and `/replay`.
- **More in the diagram (owner: "hard to understand what it is doing"):** each box shows its action under its name (and a file its path), the first beat is marked START, a completed beat shows the rows it made in a tag above its box, and a legend explains the shapes and arrows. Boxes widen for the second line.
- **A more informative run log (owner: "super uninformative"):** a `done` line now says what the beat did (`done weighed  map.weigh  in: joined 12  made 5 rows`; `wrote booking 1 row`), each move is `next <beat>`, each hold is `paused before <beat>`, and every Jev answer is a `jev` line with the level, its probability, the runner-up and the option count. New events `jev_read` and an `action` on `beat_completed` (`docs/PLAYS.md`).
- **Tests:** 642 unit tests in about 31 s; browser 52/52 in about 116 s. The contrast test's cleanup no longer fails when the page redraws a diagram between the picture and the cleanup.

## Sprint 30 — a console that uses the desktop (2026-11-06, branch `sprint-30`, not yet merged)

- **No login** (owner decision 44, already on `main`): the access secret, its files and the hiding of Jev level names are gone; each file box says whether it may be left empty; Replay lists only the picked play's captured runs, named; the start panel is two columns on a wide screen.
- **One diagram, following the last choice:** a run tab shows that run's diagram; picking a play (or SHOW PLAN) shows its plan in the same place, where clicking a flow beat holds the next run before it. The start panel has no diagram of its own.
- **A short run rack:** each play's newest 8 runs and the chosen one; `N older` / `fewer`; the runs the console cannot read are one folded group.
- **The run view uses the width:** three columns from 1400 px (printer, readouts, diagram with step view), two from 1101 px, one below; the printer's paper is as tall as its lines. Browser tests at 390, 1280, 1600, 1920, 2560 and 3840 px (1920 at 50 percent zoom) check the columns and that the page never scrolls sideways.
- **Tests:** 630 unit tests in about 31 s; browser 49/49 in about 109 s. No server or event change.

## Sprint 29 — see the whole play, and step through it (2026-11-05, branch `sprint-29`, not yet merged)

- **The whole play is drawn:** the console's diagram shows the stage's files (read and written), the beats (a dashed border for a beat that waits until it is read) and who reads what, from one plan built from the play file (`src/play/plan.py`). A run lights it up as before; a replay does too. The same picture shows the picked play before any run (`GET /api/plan?play=<file>`).
- **Start held, or held before a beat:** START HELD next to PLAY; click a beat of the flow on the plan (or Enter on it) and the next run holds before it. `understudy run --watch --stop-at <beat>` does the same from the command line. `control.json` gains `stop_at`; the runner still never writes the file. A beat never reached ends the run saying so.
- **A step view:** under the diagram, a beat's action, `with`, what the plan says it reads and, once completed, what it read, made and wrote (names, row counts, column names; no values). `beat_completed` carries `read`, `wrote` and `made`.
- **The run's first line carries the plan** (`run_started.plan`) in place of `beats` and `transitions`; runs recorded before this sprint show "no plan" (no back-compat). The real household replay's outputs are byte-identical to the baseline; its `events.jsonl` grew from 594 KB to 1.06 MB.
- **Docs and tests:** ADR-0062, `STORY_ARCH_SPRINT29.md`, `UAT_PLAN_SPRINT29.md`, `RETRO_SPRINT29.md`, two lessons, owner decision 43. 636 unit tests in about 31 s; browser 44/44 in about 112 s.

## Sprint 28 — plays (2026-11-05, branch `sprint-28`, not yet merged)

- **A sketch is a play.** A play has a **stage**, its whole interface (props, files read, files written with `access: write`), and a **scene** of **beats**. A beat with `to:`/`transitions:` is in the flow; a beat without them is performed when another beat first reads it. Jev is a beat (`do: { jev: ... }`). `from:` names an action's main input; `do: { write: x }` and `do: { play: x.yaml }` replace sinks and sketch calls. Reference: `docs/PLAYS.md`; ADR-0061.
- **Calling a play:** a call's `with:` binds the called play's props and files to the caller's pieces; the called play touches no disk, and what it writes is the call beat's result (under `each`, each written row carries the row it was played for). `outputs:`, `{input, output}` pairs and `map.unpair` are gone.
- **Paths:** `--with <file>=<path>` gives a stage file its path; `--source` is gone; `optional: true`. The household command line is unchanged (`--with monarch=... amex=... pinned=... additions=...`).
- **The run record and the console say play and beat:** events `run_started.play`, `beat_started`/`completed`/`failed`/`entered`; `run.json` `beats`, `failed_beat`; CLI lines `beat <name>`; console labels Play, all beats, BEAT TUBE, the BEATS gauge; `understudy dashboard --plays`. A log from before plays shows as unreadable (no back-compat).
- **Code:** the package is `src/play` (class `Play`, `PlayError`); the schema is `schema/play.schema.json`; the examples' flow beats are named as roles (`addition_checker`, `record_writer`, `group_judge`).
- **Proved:** the household outputs stayed byte-identical to `main` on the fixtures and on a replay of a real run after every phase. Unit suite 601 tests in about 30.5 s; browser 39/39 in about 108 s.
- **Not changed (debt):** the engine's internal names behind the loader's translation, and the console API's `sketch`/`stage` JSON keys.

## Sprint 27 — the test pyramid (2026-11-03, branch `sprint-27`, not yet merged)

- **A faster gate:** `bobp make check` now takes 36 s (was 96 to 101 s) and runs lint and the secrets scan before the tests, so a lint error stops it in 0.16 s. The Python unit suite is 29.4 s for 586 tests (was 94.6 s for 554).
- **Rules are tested on their own stages:** `src/sketch/fragment.py` (`Fragment`, `read_stage`) computes any source of a sketch from written rows, with stand-ins for the stages and Jev reads behind it; the household tests use it. Household tests: 73 tests in about 57 s became 80 in 11.4 s, and the whole-sketch runs fell from about 53 to five. Each moved group was proved by breaking its rule.
- **Console server stops at once:** it looks for a stop request every 20 ms, not every 500 ms (`run --watch` closes promptly too; about 35 s less across the test suites).
- **Child sketches load once per file version:** the row-independent read is cached on the file's text (so an edit is always seen, whatever the modification time says); per-row load 71.5 to 38.6 ms, outputs identical, about 43 s less on a real household run.
- **Browser suite:** 154.9 s to about 100 s, 39 tests, no flake (contrast stays on real pixels because the themes draw on textures; the six looks run in parallel; animation is off page-wide). The 90 s target was missed by about 10 s.
- **Docs:** ADR-0060, `STORY_ARCH_SPRINT27.md`, `UAT_PLAN_SPRINT27.md`, `RETRO_SPRINT27.md`, `docs/TEST_STRATEGY.md` with the pyramid and its budgets, two lessons, owner decisions 17 and 18.
- **No product behavior changed** except `Server.serve_forever`'s poll and the optional `window.understudyPollMs`.

## Sprint 26 — see and drive the machine (2026-11-03, merged into `main`)

- **Hold, step and resume a run:** PAUSE, STEP and RESUME in the console hold a running run before its next stage (a stage already running, Jev included, finishes first), let exactly one stage through, or run on. A held run reads PAUSED with "paused before `<stage>`", never stalled. `understudy run <sketch> --watch [--pause] [--port N]` opens a console for that run on this machine only (secret in `.understudy/watch.secret`) and can start it held. The run folder gains `control.json`; the log gains `paused` and `resumed` lines.
- **Replay a finished run's story:** REPLAY above the log opens a bar with STEP BACK, PLAY, STEP, a scrubber and "event N of M"; the stages, gauges, diagram and printed lines show the run as it was after event N. It reads `events.jsonl` alone; a log with an unreadable line is refused, naming it. `GET /api/runs/<id>/replay[?at=N]`.
- **See the decision:** a DECISIONS panel lists a run's decisions with their options, final weights, what removed or held each, and the pick; the log prints each as `decision <stage>: <row> <dimension> = <pick> (<probability>)`; in a replay a decision moves the cursor to its event. `GET /api/runs/<id>/decisions`. The log records only the blended weight, not each decider's.
- **Generic sketch parts:** none this sprint.
- **Breaking:** `/api/session` gains `holdable`; printed log lines gain an `event` field.
- **Docs:** ADR-0058 and ADR-0059, `ARCH_SPRINT26.md`, `UAT_PLAN_SPRINT26.md`, `RETRO_SPRINT26.md`, two lessons, owner decisions 16 and 17.

## Sprint 25 — the tool fixes the categories, and payments know what they paid for (2026-11-03, merged into `main`)

- **One clean list of categories:** ISO 18245 (13 groups, 280 names) plus your own additions under "Household" (Rent, Mortgage, Tuition, Income, Transfer, Loan repayment); `--with additions=<path>` swaps in your file. A bad additions line or a pin naming a category outside the list stops the run before any Jev request.
- **Jev puts every merchant in a category:** two choices (a group, then a name), placed when sure enough; otherwise the merchant is in `review.jsonl`. The export's own `Category` is never shown to Jev and decides nothing.
- **Kinds follow links and the tool's categories:** a transfer is a payment the run linked from its own text, a merchant in "Household: Transfer", or a card's own "payment received" line. New `crosswalk.jsonl` lists every merchant with the tool's category beside the export's and flags where they differ about money moving.
- **Payments know what they paid for:** `payments.jsonl` (one line per card payment: charges settled, amount settled, remainder, whether it is partly unexplained, and its five largest categories), `settled_by` on each card charge, and `open_balance` in `summary.json`. On the baseline, 11 of 12 payments settle within 5%, and settled plus open equal all the card's charges ($299,942.17) to the cent; open balance $28,443.67.
- **Spending by the tool's category:** `spending.jsonl` and the console's list use the tool's categories, with `unplaced` for a merchant in review (38.6% of spending on the baseline until you pin more).
- **Generic sketch parts:** `map.unique`, `map.smallest`, `map.allocate`, `map.top`, `map.nest`, a `by` option on `map.share`, `places` on `map.weigh`, `commonest` on `map.group`.
- **Breaking:** the export-first category rule and the label rules for transfers are gone; `uncategorized` is now `unplaced`; `place_merchant.yaml` and `name_merchant.yaml` are gone.
- **Docs:** ADR-0055 to ADR-0057, `ARCH_SPRINT25.md`, `UAT_PLAN_SPRINT25.md`, `RETRO_SPRINT25.md`, two lessons.

## Sprint 24 — what the money goes on, typed inputs, and the statechart you can see (2026-11-02, branch `sprint-24`, not yet merged)

- **Card payments are not spending:** a household record is a transfer when its Category is `Transfer` or `Credit Card Payment`, or ends in `: Credit Card Payment`, `: Transfer` or `: Transfers`, or when the run links it to a record in another account. Positive records outside Ridgewood that are not transfers fell from 169 records ($240,596) to 143 ($20,038); Ridgewood is unchanged. `summary.json` counts `transfer_basis` (`label`, `link`, `both`, `none`). New sketch condition `ends`.
- **Where the money goes:** `spending.jsonl`, one line per category (`category`, `count`, `amount`, `share`), biggest first, from your export's own category, else Jev's, else `uncategorized`; `spending_total` in `summary.json`. On the baseline: 90 categories, $403,977 in total, Rent $60,807 first. The console's summary lists the ten largest and "and N more".
- **Typed inputs:** a sketch declares `inputs:` (`choice`, `range`, `count`, `switch`, each with limits and a default). The console shows a dial, a slider, a stepper or a switch for each, reachable by keyboard; a value outside its limits is refused on the command line and in the console, naming the input; `evening` declares its seven values and no longer repeats their defaults.
- **The statechart:** the console draws the sketch's machine (double-bordered finals, guard labels, dashed loops), lights the state the run is in within a second, marks the move just taken and says how the run ended; a log without a story says so. The layout is computed in Python (`src/dashboard/chart.py`) and tested to forty states.
- **Generic sketch parts:** `map.share`, the `ends` condition and `inputs:`; `run_started` now also carries `initial`.
- **Breaking:** `summary.json` has `transfer_basis` instead of `kind_changed_by_category`; a sketch's `--with` value for a declared input is checked against its limits.
- **Security:** SEC-010 (a typed number was checked as a float but passed on as text) found and fixed in Phase 4.
- **Docs:** ADR-0052 to ADR-0054, `ARCH_SPRINT24.md`, `UAT_PLAN_SPRINT24.md`, two lessons.

## Sprint 23 — household numbers you can trust, and a run that tells its story (2026-11-02, branch `sprint-23`, not yet merged)

- **Transfers come from your categories:** a household record is a transfer exactly when its Monarch `Category` is `Transfer` or `Credit Card Payment`, otherwise never; savings moved from Schwab into checking are no longer income or refunds. `summary.json` counts the records the category changed (`kind_changed_by_category`). A Monarch file without a `Category` column stops the run before any Jev request. On the baseline file Ridgewood income is $363,348.62 and expenses $205,042.27, equal to the owner's file to the cent.
- **Income, expenses and net per account:** `totals.jsonl` (one line per account, then an `all` row, also `net_spending` in `summary.json`), transfers left out.
- **Merchants for review, as a list:** `review.jsonl`, one line per merchant Jev was unsure of (`payee`, `count`, `amount`, `top` and `runner_up` with probabilities, `reason`), most records first.
- **Pinned categories:** `{payee, category}` lines in `.understudy/pinned.jsonl` (or `--with pinned=<path>`) place a merchant in your category, mark it `category_source: pin`, skip Jev and leave it out of `review.jsonl`; bad pins stop the run before any request.
- **The run tells its story:** the first `events.jsonl` line lists the sketch's states and moves; `state_entered` lines; `decision` lines for each `reduce.blend` dimension (options, what removed each, pick and probability). The console's description of a run says `story: true` or `false`.
- **Generic sketch parts:** `map.require`, `map.keep`, `map.without`, `map.complete`, `map.known`, `map.set`, `reduce.tally`, `reduce.note`, `reduce.top_two`, a `sums` option on `map.group`, and optional file sources.
- **Breaking:** `external_transfer`, `judge_payee.yaml` and `judgments.jsonl` are gone from the household sketch (Jev is no longer asked about payees).
- **Docs:** ADR-0050 and ADR-0051, `ARCH_SPRINT23.md`, `UAT_PLAN_SPRINT23.md`, two lessons.

## Sprint 22 — the console you can trust, see into, and start runs from (2026-11-01, branch `sprint-22`, not yet merged)

- **A run says how it went:** the header reads RUNNING, DONE, FAILED, STOPPED or STALLED; a failed run shows a banner naming the stage and the reason (it jumps to that line); a summary shows the outcome, mode, stale, duration, the `--with` values and each output with its row count; the page says "disconnected, retrying" when the server is gone and recovers by itself; phones show the status first.
- **See inside a run:** nested stages are grouped with progress (`readings.judge_payee` 25 of 25 done); rack tabs are grouped by sketch and badged; gauges draw a needle only for a fraction the run knows (Jev requests and elapsed time are figures); the printer filters by text, stage and failures, and jumps to the start, the first failure and the end, also for lines that arrive live.
- **See Jev's judgements:** a list of each captured read with its levels, probabilities and top level, flagged when it is below 0.7 or `none_of_these`; gauges for confidence and for answers asked against reused. On the real household run 481 of 932 reads were unsure. Level names that come from your own data (refund candidates named by date and amount) show as "option N" unless you hold the access secret.
- **Start, replay and stop from the console:** `understudy dashboard [RUNS] [--port] [--sketches DIR]` lists the sketches in DIR, checks one with the values you give, starts it live or from a captured run, and stops runs it started. It needs the access secret, saved at each start in `.understudy/dashboard.secret` (never printed); ADR-0049.
- **The command line keeps its promises:** a busy port or a bad folder is one `understudy:` line and exit 2; `--help` describes each command with examples; `run` prints its run id and how to watch it; `understudy runs` lists runs. **New:** `bobp make security-scan` (gitleaks and pip-audit over every dependency group), `bobp make install-browser` and `test-browser` (the console in a real Chromium: rack, banner, live follow, start and stop, keyboard, and text contrast in all six looks). Text that failed 4.5:1 was fixed in every theme.
- **Security (Switch):** reviews and findings SEC-001 to SEC-009 in `agents/switch/`: event streams capped and idled out, browser security headers, the sketch path stored relative, the secret kept out of captured output, a Content-Length check; accepted by the owner with expiry: reads open to the network (to 2026-12-01) and the secret over plain HTTP (to 2027-01-30).
- **Docs:** `docs/PRD.md`, `docs/ARCH.md`, `docs/TEST_STRATEGY.md` and the PRD template are new; ADR-0049.
- **Breaking:** runs now default to `.understudy/runs` (git-ignored and private, beside the Jev captures) instead of `build/runs`, so `bobp make clean` cannot delete them. Move old runs with `mv build/runs .understudy/runs`; `--out` still chooses another folder.

## Sprint 21 — the console in Python, and the last Node deleted (2026-11-01, branch `sprint-21`, not yet merged)

- **`understudy dashboard [runs-folder] [--port 4180]`** serves a read-only operations console over the runs under `build/runs`: a rack of runs, a printer that follows a running run live (server-sent events), one lamp per stage, and four gauges (STAGES, FAILED, JEV, ELAPSED) read from the run's own files. Three themes, light, dark or auto. Standard-library server, listening on 0.0.0.0 with no login (use a trusted network); what the page shows is decided in Python (`src/dashboard/server.py`) and tested there.
- **Removed:** all Node: `package.json`, `package-lock.json`, eslint, `.nvmrc`, every `.mjs`, the `node:test` suites, the play controls, faders, YAML bay and cheat sheet of the old console. **Breaking:** `bin/understudy.mjs` is now the shell script `bin/understudy`; `bobp make install`, `test` and `lint` are Python only (ADR-0048). Fonts are committed under `src/dashboard/fonts/`.
- The Python-port epic is complete; its purge list is empty.

## Sprint 20 — stages, children and the household as a sketch (2026-10-30, branch `sprint-20`, not yet merged)

- **Sketches are Jinja2 templates** with `--with name=value` (and `with:` when a sketch calls another), a final state's `outcome`, and a sketch's `outputs`. **Breaking:** the `decider` keyword is gone.
- **Stages are `map`, `reduce`, `sink` and `sketch`**, registered in Python with `@stage` whose signature is the contract of the YAML. **`kind: stage` sources** compute a list once, by name. **`each`** repeats a sketch per row, and **`each` with `reduce`** folds, giving each iteration what the earlier ones output.
- **New general stages:** `where`, `join`, `unpair`, `expect`, `adjacent_runs`, `prefer_order`, `prefer_middle`, `weigh`, `max`, `min`, `any`, `convert`, `number`, `pair`, `link`, `earlier`, `group`, `attach`, `concat`, `matching`, `classify`, `coalesce`, `replace`, `normalize`, `format`, `rows`, `mcc`. Conditions read dates and times with `dateparser`; business days use `holidays`.
- **A file source ending in `.csv`** is read with its header row as field names.
- **The evening** (`examples/evening/`): showings ranked by Jev's reading of the reviews, Jev picks among the best five, seats found by adjacent runs. **The household** (`examples/household/household.yaml`, `understudy run ... --with monarch=... --with amex=... --with amex_account=...`) is the old transaction cleanup rebuilt as a sketch with three Jev child sketches and a fold (ADR-0047).
- **Removed:** `understudy etl run`, SQLMesh and its models, the MCP source servers and the `mcp` dependency, the old Node examples, the recard `seed/` and the old sketch schema. `understudy run` and `check` take `--with`.

## Sprint 19 — the coffee proof of concept: a new sketch model (2026-10-30, branch `sprint-19`, not yet merged)

- **A new kind of sketch, and the only one.** One YAML file with `sources`, `sinks`, `outcomes`, `data` and a `machine` the owner writes (python-statemachine). Rules are `decide` trees with explicit YAML conditions (`segment: { eq: students }`, `temp: { in: [80:90] }`, `and`/`or`/`not`, `has`), weights are numbers or `if`/`then`/`else`, a stage's deciders are blended per dimension, and `forbid` rules drop options and always win. Counting and converting run as SQL on DuckDB. A subsketch (`do: sketch.<file>`) gives back a decider. See `docs/SKETCHES.md`.
- **Jev is a source** (`kind: jev`): a rubric (`instructions` plus `criteria`) and the data it reads go in, a probability per level comes out. Every live read of a non-file source is captured, and `--replay [run-id|folder]` runs offline from one complete capture, never going live. `summary.json` records `mode` and `stale`.
- **`understudy run <sketch.yaml>` and `understudy check <sketch.yaml>`** now start the Python package (`src/sketch`). **Breaking:** the old Node `run`, `check`, targets (process, http, page, mcp), apps, watch page server, dashboard server and XState machine are deleted, with their 41 test files, the browser tests, the `test-browser`, `test-live` and `install-browser` targets and nine npm dependencies. `library`, `watch` and `dashboard` say they are being rebuilt; the six old examples and the dashboard return in later slices of the Python-port epic.
- **One of everything shared:** `src/machine_runner.py` is the state-machine loop for both the ETL and sketches; the Jev wrapper moved to `src/jev.py` and the output-path policy and project root to `src/paths.py`.
- The coffee example (`tests/fixtures/coffee/`) runs end to end on invented fixtures: 1,600 drinks across five segments become 32,000 g of coffee beans. One real Jev judgement (a cold forecast after a mild week: `much_colder 0.95`) is committed as `tests/fixtures/coffee/replay/` and replays with no key.
- `bobp make test-py ARGS="<file pattern>"` runs a subset of the Python tests.

## Sprint 18 — tech-debt cleanup (2026-10-29, branch `sprint-18`, not yet merged)

- Removed the dead Sprint 16 ETL code (`csv_to_jsonl.py`, the `reconciled_transactions` and `categorized_transactions` models and their tests), the unused `@duckdb/node-api` dependency and the `probe-etl` target. No compatibility layer.
- `bobp make lint` now also runs ruff over `src/etl` and `tests/python` (bugbear, simplify, complexity, Pylint, dead-code and more); findings fixed. `run()` in the ETL controller was split (`_run_stages`, `_publish`, `_copy_result`).
- Merged local `sprint-1` to `sprint-15` branches deleted.

## Sprint 17 — transaction cleanup (2026-10-29, branch `sprint-17`, not yet merged)

- **Breaking ETL output change:** `result.jsonl` replaces `review.csv`. Each transaction carries
  its source rows, category and confidence, transfer partner, and refund link and confidence.
  The Node ETL has been replaced by a Python controller using a YAML state machine.
- Purchases pair one to one with opposite signs, first on the same date and then within three
  business days. Transfers stay in the result but are excluded from net spending. Refunds link
  to earlier charges. Jev judges unpaired transfer payees, including Venmo and Zelle payments.
- Categories come from the period's Monarch labels, with new names chosen from the MCC list.
  `--since`, `--amex-account`, and `--out` control the period, account and destination.
  Default period starts at the Amex export's earliest date. Jev failures stop publication.

## Sprint 16 — staged local ETL with Jev-guided categories (2026-10-27, branch `sprint-16`, not yet merged)

- **`understudy etl run --monarch <csv> --amex <csv>`**: validates both exports, keeps a copy of each
  for the run, converts every row to a JSONL record that keeps its source and row number, and
  reconciles with SQLMesh on DuckDB. A date and amount that occurs once on each side becomes one
  row with both source rows; anything else stays separate, marked ambiguous when it repeats.
  ADR-0037.
- **Jev categorises each distinct merchant once** from a fixed 46-pair taxonomy that always holds
  `Misc / Other or not yet classified`; the choice is reused for every row with that merchant, and an
  off-list or empty answer becomes `Misc` marked for review.
- **A review file and a summary** (counts only, no transaction contents) under ignored
  `build/runs/<run-id>/`. A failed stage, Jev being unreachable included, leaves no summary or review
  file. A synthetic run of 4,700 pairs (9,400 rows) completes locally in about 10 seconds.
- **Python joins the toolchain** (approved by the owner and Tank 2026-10-17): CPython 3.12, uv, SQLMesh
  and DuckDB, pinned and isolated; `test-py`, `test-etl` and `probe-etl` make targets.
- **Known limit**: on the owner's real files it matches only 26 rows, because it pairs same-sign
  amounts and the Amex export and Monarch show the same purchase with opposite signs. The
  sign-flipped match, transfers, refunds and new category names are planned for Sprint 17.
- `make run` and `make test-live` read API keys from a gitignored `.env`; `data/` is gitignored.

## Sprint 15 — flair and real gauges (2026-10-17, branch `sprint-15`, not yet merged)

- **Five gauges** from the run: steps of the limit, Jev's confidence, shortlist left, Jev scores
  asked · reused, idle time of the idle limit. The run's start line now carries its `limits`.
  ADR-0036.
- **Flair**: steampunk stitched leather, brass screws, ornate edges, flickering valve bulbs and
  backlit needle meters; starship power-bar readouts; professional metric cards.

## Sprint 14 — the statechart as a flow (2026-10-17, branch `sprint-14`, not yet merged)

- The state tube draws the statechart as a **layered flow** (as Graphviz and the XState visualiser
  do): rounded state boxes from the initial dot down, double-bordered finals, labelled orthogonal
  arrows, laid out by `elkjs` - no overlaps. Steampunk keeps the round tube; professional and
  starship use a rectangular screen. The weights' shares are a bar under the screen. ADR-0035.
- The printer runs spool to spool behind glass; scroll up to rewind. A page opened mid-run shows
  that run. The printer opens on a release latch.

## Sprint 13 — questions that know the inputs (2026-10-17, branch `sprint-13`, not yet merged)

- **Every Jev question sees the run's inputs** as `inputs` in its state; any question's wording
  can name one (`` `inputs.tickets` ``), and `check` refuses an undeclared name. `pick.with` is
  gone (the pick sees all of them too). ADR-0034.
- The evening's questions follow its controls: the party size, the mood and the evenings switch.

## Sprint 12 — one move at a time (2026-10-17, branch `sprint-12`, not yet merged)

- **STEP** and **PAUSE/RESUME** on the dashboard: STEP starts a run and makes one move, then one
  more each press; PAUSE holds a playing run before its next move; STOP ends either. ADR-0033.
- The printer opens on an **OPEN** release latch (was REMOVE).

## Sprint 11 — light and dark (2026-10-16, branch `sprint-11`, not yet merged)

- A **MODE** switch on the dashboard: **AUTO** follows the device's light/dark setting (live),
  **LIGHT** and **DARK** fix it; remembered per browser, `?mode=` on the link. Every theme has both:
  steampunk light (parchment, maple, brass), professional dark (charcoal), starship light (the
  bars on a pale screen). ADR-0032.
- The fader LEDs, slot glows and readouts shine as brightly as their fader is set (owner).
- Phones: the bay drops down under the tube; the theme switch wraps. The dashboard is served at
  the root - no token in the URL (owner; ADR-0023 amended).

## Sprint 10 — a schema for sketch.yaml (2026-10-16, branch `sprint-10`, not yet merged)

- **`schema/sketch.schema.json`**: editors with the YAML language server complete `sketch.yaml`
  keys, show what each means and underline mistakes as you type. Every example points at it;
  `docs/SKETCHES.md` "Editor help" says how to point yours. `check` is unchanged. ADR-0031.

## Between sprints (2026-10-16, on `main`)

- **A weight input is a share of the full weighting** (owner): the top of its range weighs a factor
  3, half way 1.5, the bottom turns it off - so the evening's 0-10 faders score as the old 0-3 did.
- `docs/SKETCHES.md`: a table of the four input kinds and their rules, the weight rule, and
  `when:` / `{ input: }` in the table of words.

## Sprint 9 — themes (2026-10-16, branch `sprint-9`, not yet merged)

- A **THEME** switch on the dashboard: **steampunk** (default), **professional** (light, flat, one
  blue accent) and **starship** (black screens framed by rounded orange/lilac/blue bars, pill
  buttons, condensed lettering - in the manner of the Enterprise-D's computers). Remembered per
  browser; `?theme=` on the link. ADR-0029.
- Fixed: with 0-10 weights the tube's centre orb and decision edge grew far too big; sizes now
  follow each weight's share of its range.

## Sprint 8 — behind the printer (2026-10-16, branch `sprint-8`, not yet merged)

- **REMOVE the printer** to edit the sketch's whole `sketch.yaml` in the bay behind it, with a
  cheat-sheet sticker; saved half a second after typing stops (checked first), and the state tube
  redraws as you type. Refused text is not saved and says why; read-only while a run plays.
  **REFIT PRINTER** puts it back. ADR-0028.
- The evening's weights run 0-10 (was 0-3).

## Sprint 7 — how many tickets (2026-10-16, branch `sprint-7`, not yet merged)

- **Count inputs** (`tickets: { count: [1, 4], default: 2 }`, `--input tickets=3`), shown on the
  dashboard as a **brass stepper**; weights stay analog faders.
- **`{ input: <name> }`** in `values:` lists and gate bounds: the evening holds as many seats as
  tickets, all together in one row. ADR-0027.

## Sprint 6 — the dashboard, with atmosphere (2026-10-16, branch `sprint-6`, not yet merged)

- **`understudy dashboard <folder>`**: a steampunk operations console (design approved on a
  clickable mockup, `docs/design/DASHBOARD.md`): a rack of the folder's sketches; each sketch's
  inputs as a pointer dial, coloured analog faders with Nixie readouts (`11` at the top) and
  switches with lamps; a square lit PLAY/STOP with a green READY lamp; POWER.
- **State tube**: any sketch's statechart on a round tube screen, every state and transition
  labelled; the current state glows; a power ring of the weights, and their blended colour on the
  decision edge and the centre orb.
- **Printer**: the run log printed on tractor-feed paper, score tables with 1.0 as `11`.
- **Access panels**: edit a factor's range/order, its Jev question, defaults and the moods - saved
  to `sketch.yaml` in place (comments and layout kept), checked first; POWER off and on restores the
  factory settings.
- **Switch inputs** and `when:` on gates; `examples/evening` has an evenings-only switch.
- Fonts from `@fontsource/*` (local). ADR-0023..0026.

## Sprint 5 — decide like a person (2026-10-16, branch `sprint-5`, not yet merged)

- **Several MCP servers in one sketch**: `target.servers` (inline or names in `servers.json`);
  tools are `<server>/<tool>` when there are several. One-server sketches are unchanged.
- **Deciding** (`decide:`): for a named tool argument, each value keeps its answer row (joined
  across servers by a key). **Gates** (`is`, `in`, `at_least`, `at_most` with numbers or HH:MM,
  `any`) remove or hold back; **scores** (`range`, `order`, `ask`) with weights that bend the
  curve multiply into a total; Jev makes the final Choice from the **shortlist**. Step lines and
  the watch page show the score table, what was removed and why, what is held back. A decision
  waits until nothing is held back, unless a value already scores a perfect 1. A deciding sketch
  does not repeat a call already answered with the same arguments (an LRU cache of 200, `lru-cache`).
- **Jev judges what numbers cannot**: a `type: score` question (`looks_at`, `levels`) is a
  factor - asked once per row, in one request per look.
- **Inputs**: `inputs:` declares choices and weights; `understudy run <sketch> --input
  mood=romantic --input centre=1`; `pick:` tells the final Choice the mood.
- **Walk away**: guard `nothing_qualifies` + a final state tagged `walked-away` - outcome
  `walked-away`, exit 0, and a sentence saying what removed what.
- **`examples/evening`**: the owner's night out against a box office and a ratings server
  (made-up films, scores, reviews); `BOX_STATE=full` walks away. `make test-live` checks every
  run's outcome. Docs: SKETCHES "Several servers" and "Deciding", MCP_GUIDE "Deciding like a
  person"; ADR-0017..0022.

## Sprint 4 — watch the understudy live (2026-10-15, branch `sprint-4`, not yet merged)

- **Live view**: `understudy run <sketch> --watch [--port N]` serves a page on 127.0.0.1 that
  draws the sketch's statechart, highlights the current state and the transition just taken,
  and lists each Jev decision - options, pick and confidence, chosen MCP arguments, the app's
  answer - as it is made. Opening late or reloading shows everything so far. No internet needed,
  no new dependency; watching changes nothing about the run.
- **Pause and step**: Pause stops a watched run before its next move, Step lets one move
  through, Resume lets it run; `--pause` starts paused. No Jev call while paused; the idle
  limits count running time only; Ctrl-C stops a paused run at once.
- **Replay**: `understudy watch <log.jsonl>` replays any finished run from its log alone - play,
  pause, step through each state change, click a decision to jump to it.
- **The log is the whole story**: a `start` line (sketch, what it plays, its statechart), a
  `state` line per transition (idle looks folded into `idle_looks`), and an `ended` line saying
  why a failed run stopped. Step and final lines are unchanged; skip lines with `event`.
- Docs: USER_GUIDE "Watch a run" with a screenshot, SKETCHES §7 event lines; ADR-0014..0016.

## Sprint 3 — one sketch file, and any MCP server as an app (2026-10-15, branch `sprint-3`, not yet merged)

- **`sketch.yaml` is the only format**: one file holds a stand-in's name, target, player
  settings, step cap (`steps:`), questions and turn (statechart). Code only where an app needs
  reading - `hooks.mjs` for programs and JSON APIs. `adapter.mjs` and `part/` are no longer read
  (no back-compat): such a directory is refused, saying what replaced them. The three examples
  were converted; `examples/web` has no code at all. Commands take a sketch directory or the file.
- **MCP target** (`kind: mcp`): understudy is an MCP client (`@modelcontextprotocol/sdk`) and
  plays any MCP server - local over stdio, or remote over streamable HTTP with token headers.
  The server is named in Claude's `mcpServers` shape, inline or by reference to a file
  (`config: servers.json`, or a project's own `.mcp.json`); `${VAR}` / `${VAR:-default}` come
  from the environment. Tool errors are logged as the server's answer.
- **Generic MCP app**: each tool is a move; Jev **chooses** each open argument from the sketch's
  `values:`, the tool's schema, or the last successful answer (it never writes text). `calls:`
  fixes whole calls. Tools that cannot be filled are left out, and the run says why.
- Examples: `examples/mcp` (a cinema box office over stdio) and `examples/mcp-remote` (the same
  box office by URL and token). `make test-live` serves the remote one itself.
- Docs: `docs/SKETCHES.md` replaces `docs/ADAPTERS.md`; ADR-0011..0013.

## Sprint 2 — a JSON API, and web pages without changing them (2026-10-15, branch `sprint-2`, not yet merged)

- **HTTP target** (`kind: 'http'`): plays a JSON API - a look is a GET of its state, a move is a
  request. Starts the server on a free port or attaches to a running one. An error status is
  logged as the step's `response`, not treated as a crash. Example: `examples/http` (vending machine).
- **Web pages need no changes**: the page target reads the accessibility snapshot (what a screen
  reader sees) and presses, ticks or picks controls by role and name. The `window.__understudy`
  hook is gone (no back-compat).
- **Generic page app**: a web adapter can be just a name and a target; the controls on the page
  are the moves (`button:Pro (paid monthly)`). `examples/web` now has a 4-line adapter.
- **`showing` guard**: a part says what its end looks like.
- **Stalled runs end**: 10 s with nothing offered after a move ends the run (`stalled`) with a
  hint, for every target.
- `check` refuses unknown or missing target fields, naming what each field is for.
- Docs and ADR-0007..0010 updated; ADR-0002 superseded.

## Sprint 1 — MVP first run (2026-10-15, merged to `main` at 766a47c, tag `v0.1.0`)

First release of understudy: Jev-driven stand-ins that play real apps.

- `understudy run <dir> [--steps N]` plays an example's part against its app with live Jev:
  one JSON line per step on stdout and in `build/runs/<adapter>/<ts>.jsonl`, a final
  outcome line, a step cap (default 50), Ctrl-C stops at a safe state.
- Two targets: a command-line **process** and a web **page** (headless Chromium, driven
  through the page's `window.__understudy` hook).
- `understudy check <dir>` refuses broken parts before anything starts, naming file, path,
  bad name and the nearest known one; `understudy library [<dir>]` lists every name.
- Examples: `examples/cli` (coffee counter) and `examples/web` (sign-up wizard).
- Exit codes 0 done / 1 failed after starting / 2 refused before starting.
- Core (statechart parts, Jev decisions, seat) moved from recard d817d3c and generalized.
- Docs: `docs/ADAPTERS.md`, `docs/DECISIONS.md`, `docs/SDLC.md`.
