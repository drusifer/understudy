# UAT Plan: Sprint 24, what the money goes on, typed inputs, and the statechart you can see

- **Stories / criteria:** UND-93, UND-94, UND-95, UND-87 and UND-82 in `docs/sprints/USER_STORIES_SPRINT24.md`
- **Environment and build:** branch `sprint-24`, local CLI and console (`bobp make run`, `bobp make dashboard`), live Jev; real household data in `data/` (git-ignored)
- **Date / tester:** 2026-11-02, Trin
- **Entry conditions:** `bobp make check` green; baseline `data/Transactions_2026-11-02T19-14-07.csv` and `data/amex-2026-ytd.csv` present
- **Exit conditions:** every acceptance criterion of the sprint passes; unresolved issues listed

## Scenarios

Phases are added as they pass UAT.

### UAT-24-1: Card payments and moves between accounts are not spending (Phase 1)

- **Linked criterion:** UND-93 AC1 to AC6
- **Preconditions and data:** the baseline files, `since=2026-01-01`; live run `run-20261103T031222-20544bb5`; unit tests for each label form and for a link-only transfer
- **Steps:** `bobp make run ARGS="run examples/household/household.yaml --with monarch=data/Transactions_2026-11-02T19-14-07.csv --with amex=data/amex-2026-ytd.csv --with amex_account=Platinum --with since=2026-01-01"`; read `records.jsonl` and `summary.json`
- **Expected observable outcome:** every labeled or linked record is a transfer; none other is; positive non-transfer records outside Ridgewood under $30,000; Ridgewood income $363,348.62 and expenses $205,042.27; `transfer_basis` counts
- **Actual outcome:** labeled or linked records that are not transfers: 0; `transfer_basis` both 35, label 103, link 5, none 5,010; positives outside Ridgewood 143 records, $20,038.35 (was 169, $240,596); Ridgewood income $363,348.62 and expenses $205,042.27; the all-account figures are now income $383,386.97, expenses $454,415.02, net -$71,028.05; unit tests: `Transportation: Transfers`, `Food & Dining: Credit Card Payment` and plain `Transfer` are transfers, `Shopping: Transferware` is not, and a card payment labeled as income is a transfer by its link
- **Verdict:** PASS
- **Evidence / issue:** run folder above; 368 tests green. A condition `ends` was added so `: Transfer` cannot match `Transferware`. The mislabeled purchases the owner knows of (Depop, Soho Deli, Levy Restaurants) are now transfers until relabeled in Monarch.

### UAT-24-2: Where the money goes (Phase 2)

- **Linked criterion:** UND-94 AC1 to AC6
- **Preconditions and data:** the baseline files; live run `run-20261103T031634-2a0afad6`; unit tests against the fixture, worked out independently from the records, and for a run with no records (`since` after the data)
- **Steps:** run the household sketch; read `spending.jsonl` and `summary.json`; add up the lines
- **Expected observable outcome:** one line per category with `category`, `count`, `amount`, `share`; biggest first; the export's Category first, then Jev's, then `uncategorized`; shares add to 1 within 0.001; amounts and counts equal `spending_total`; income, credits and transfers absent; an empty file when no spending
- **Actual outcome:** 90 lines for 4,951 records; $403,977.13 in total, equal to `spending_total` in `summary.json`; shares add to 1.0 and counts to 4,951; biggest are Housing & Real Estate: Rent $60,807.08 (15.05%, 14 records), Taxes $40,674.00 (10.07%), Mortgage $31,348.60 (7.76%), Bills & Utilities: Medical & Healthcare $24,156.74 (164 records), Food & Dining: Insurance $20,408.00; none `uncategorized` on this file; the empty case writes an empty file
- **Verdict:** PASS
- **Evidence / issue:** run folder above; 377 tests green. Findings for the owner: the category `Refund` shows as a negative amount (money back with no original category); some of the owner's own groups read oddly ("Shopping & Retail: Restaurants & Dining" 469 records, $18,332; "Food & Dining: Insurance"), inherited from the earlier categorization.

### UAT-24-3: The console shows what the money goes on (Phase 3)

- **Linked criterion:** UND-95 AC1 to AC4
- **Preconditions and data:** the real run `run-20261103T031634-2a0afad6` opened in a real Chromium (Professional light at 1300 px, Steampunk light at 390 px); browser tests with built runs for the other cases
- **Steps:** open the console on `.understudy/runs`, choose the run, read the summary panel; the browser tests open a run with 13 categories, a run without the file, a run with an unreadable file, a run at 390 px; the readability test measures the heading and rows in all six theme and mode looks
- **Expected observable outcome:** ten largest categories with amount and share and "and N more"; no heading or list when the file is absent; the unreadable file named and the page working; no sideways scrolling at 390 px; readable text everywhere
- **Actual outcome:** the real run lists Rent $60,807.08 15.0%, Taxes $40,674.00 10.1%, Mortgage $31,348.60 7.8% and seven more, then "and 80 more"; the browser tests: ten rows with the first one's amount and share and "3 more"; a run without the file has the heading hidden; `spending.jsonl line 2 is not readable` shown with the status still DONE; no horizontal overflow at 390 px; the readability check first found the heading unreadable in two light looks (1.06:1 and 1.77:1) and passes after the heading took the theme's heading color; 10 of 10 browser tests pass (69 seconds)
- **Verdict:** PASS
- **Evidence / issue:** screenshots checked by eye (desktop and phone); 386 unit tests green.

### UAT-24-4: Inputs are declared and checked (Phase 4)

- **Linked criterion:** UND-87 AC1, AC4, AC5, AC6, AC7 (the controls are Phase 5)
- **Preconditions and data:** `examples/evening/evening.yaml` and a small typed sketch; unit tests for every kind and every wrong declaration; the console's launcher with a fake process
- **Steps:** `understudy check examples/evening/evening.yaml` with no value, `--with tickets=40`, `--with mood=silly`, `--with tomato=0.33`, and a valid pair; list the sketch through the launcher; post out-of-limit and valid values to start
- **Expected observable outcome:** `ok` with defaults; one plain line naming the input and the limit for each bad value; the console list gives each input's kind, limits, default and label with undeclared names left in `with`; a bad posted value refused with 400 before anything starts; a valid one reaches the run as `--with`
- **Actual outcome:** `ok: evening` with no value and with `evenings=off mood=romantic`; `input 'tickets': 40 is outside 1 to 10`; `input 'mood': silly is not one of fun, serious, dramatic, romantic`; `input 'tomato': 0.33 is not a multiple of 0.05 from 0`; each wrong declaration (unknown kind, no options, default not an option, max not above min, step 0, default outside limits, not whole, switch default, no default) names its input; the launcher lists `evening`'s seven inputs in order and refuses bad values with 400; valid values arrive as `--with evenings=off`, `mood=serious` and so on; 402 tests green
- **Verdict:** PASS
- **Evidence / issue:** `build/build.out`; `tests/python/test_sketch_inputs.py`. The `evening` sketch no longer repeats its defaults.

### UAT-24-5: The right control for each value (Phase 5)

- **Linked criterion:** UND-87 AC2, AC3, AC4, AC6, AC7
- **Preconditions and data:** the `evening` example listed by the console in a real Chromium (Professional light at 1000 px, Steampunk dark at 390 px); a typed fixture sketch with a text-only value in the browser tests
- **Steps:** open START A RUN, choose `evening`; use each control by mouse and keyboard; Play against a fake process and read the `--with` arguments; the readability check measures the controls in all six looks
- **Expected observable outcome:** a dial, stepper, switch and four faders at their defaults with a name and a readable value; keyboard use; limits held; Play sends every value; an undeclared name stays a text box; no overflow at 390 px; readable in every look
- **Actual outcome:** `evening` shows Mood (fun, serious, dramatic, romantic with `fun` selected), Party size 2 with - and +, Evenings only ON and four faders (0.3, 0.7, 0.7, 1) beside their values; the browser tests: roles and names found for the radio group, slider, spin button and switch; arrow keys move the dial and stop at the end, a slider arrow moves it one step (0.30 to 0.35), the number takes ArrowUp, Space flips the switch to OFF; + disables at the maximum and - at the minimum, a typed 99 is put back to 3, End on the slider reads 1 and one more arrow stays at 1; Play posted `evenings=off, mood=dramatic, note=hello, tickets=2, weight=0.3` (the defaults for the untouched ones); `#field-note` is a text input; no horizontal overflow at 390 px; the readability check passed in six looks after the controls' class names were renamed (the themes still held styles for the old console's `.dial-option`, `.switch` and `.fader`, and made two of them unreadable in the dark looks); 15 of 15 browser tests pass
- **Verdict:** PASS
- **Evidence / issue:** screenshots checked by eye; 403 unit tests green. One run of the readability check failed once on a pre-existing selector (`.stage-lamp` in Steampunk dark, 1.20:1) and passed in three repeats; recorded as a flake in the instrument for the retro. The switch first stretched across the whole row; it is now compact.

### UAT-24-6: The statechart is laid out (Phase 6)

- **Linked criterion:** UND-82 AC1 to AC5, AC7 (the drawing is Phase 7)
- **Preconditions and data:** the real machines of `household`, `evening` and the coffee fixture, a hand-built machine with skips, loops, a self-loop and guards, and six generated 40-state machines; a throwaway SVG rendering of the layout (not part of the product) looked at in Chromium; unit tests for the lit state, last move, ending and no-story cases
- **Steps:** lay each machine out; check for overlapping boxes, overlapping labels, labels on boxes and arrows through boxes; render the layout and look at it; call `describe` on a run with and without a story
- **Expected observable outcome:** states in layers from the initial state, finals and the initial state flagged, an arrow per move with a label only where there is a guard, loops drawn beside the boxes, nothing overlapping at 40 states, a lit state and last move from `state_entered`, `chart` null without a story
- **Actual outcome:** `household` is a straight chain of 11 states ending in a double-bordered `done`; `coffee` a chain of 6; `evening` shows `anything_qualifies`, `seats_free`, `walk_away`, `book` and `done` with `any = false` labels on the two guarded arrows; the loops machine draws the retry loop and the self-loop as dashed red arrows beside the boxes, the skip arrow around the boxes in a gutter, guards as labels; the six generated 40-state machines have no overlaps of any kind (checked by the tests, and the rendering is busy but readable); a run in `b` after `a` lights `b` and marks `a` to `b` as the move just taken; a finished run keeps its last state lit and carries its ending; a log with no story has `chart` null; a state named `<script>alert(1)</script>` and a guard with markup stay plain text in the JSON; 428 unit tests green
- **Verdict:** PASS
- **Evidence / issue:** rendering checked by eye (the rendering script is a scratch file). The layout is simple layered, as the architecture says; a 40-state machine is dense but not overlapping.

## Results and Handoff

- **Passed / failed / blocked:** Phase 1: 1 passed (UAT-24-1); Phase 2: 1 passed (UAT-24-2); Phase 3: 1 passed (UAT-24-3); Phase 4: 1 passed (UAT-24-4); Phase 5: 1 passed (UAT-24-5); Phase 6: 1 passed (UAT-24-6); 0 failed, 0 blocked
- **Open issues and impact:** Phase 2: the oddly grouped categories and a negative `Refund` line are the owner's data, not a defect; noted for the backlog.
- **Overall verdict:** PASS for Phases 1 to 3
- **Handoff evidence:** message in `agents/CHAT.md`
