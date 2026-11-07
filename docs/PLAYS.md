# Plays: the reference

understudy performs a **play**: one YAML file in which you write down how you decide something. The play has a **stage**, everything it takes and gives (its props, the files it reads, the files it writes), and a **scene** of **beats**, each a character doing one action with its props. The understudy is the one actor who performs every beat, standing in for you. Counting and converting are SQL on DuckDB; your judgement is `decide` trees with weights; Jev is asked only for a qualitative reading of text you supply, against a rubric you write.

TLDR:
    A play is `name`, `description`, `stage` (props, files read, files written), `outcomes`, `data` and a `scene` of `beats`.
    A beat is `<character>: { do: <action>, with: <props>, to: <character> }`; with `to:`/`transitions:` (or `final`) it is in the scene's flow, without them it is performed when another beat first reads it.
    `from:` names the piece an action works on; a piece is a stage file or another beat's result.
    Jev is a beat: `do: { jev: { question: choice } }` with a rubric (`instructions` + `criteria`) and the `state` it reads.
    `do: { play: other.yaml }` performs another play; its `with:` binds that play's props and files; what it writes is the beat's result.
    Every Jev read is captured; `--replay` runs offline. `understudy check` finds mistakes before anything runs.
    Worked examples: `examples/household/household.yaml`, `examples/evening/evening.yaml`, `tests/fixtures/coffee/coffee_week.yaml`.

## The words

| word | what it is |
|---|---|
| **play** | one YAML file; the outermost configuration of an automation, and a reusable piece when another play calls it |
| **stage** | the play's interface: its props, the files it reads and the files it writes |
| **prop** | a value the play takes: declared on the stage with a kind and a default, given with `--with` or a call's `with:` |
| **piece** | anything a beat reads by name: a file on the stage, or another beat's result |
| **scene** | the play's body: `initial` and its `beats` |
| **beat** | one step: a character doing one action with its props |
| **character** | a beat's name; flow beats are named as roles (`pin_checker`, `record_writer`) |
| **action** | what a beat does: `map.*`, `reduce.*`, `write`, `play`, `jev` |
| **run** | one performance of a play, in its own folder under `.understudy/runs` |

## The file

```yaml
name: household                    # required
description: ...                   # optional

stage:                             # the play's interface
  since: { kind: choice, ... }     # a prop (see Props)
  monarch: { kind: file }          # a file read: --with monarch=<csv>
  additions: { kind: file, path: additions.jsonl }            # a file read, with a default path beside the play
  pinned: { kind: file, path: .understudy/pinned.jsonl, optional: true }   # may be missing
  records_file: { kind: file, path: records.jsonl, access: write }          # a file written into the run folder
outcomes:                          # what can be decided: dimension -> its options
  temp: [hot, iced]
data:                              # your facts: anything the actions read by name
  segments: [ { name: students, share: 0.30, age_max: 24 }, ... ]
scene:
  initial: addition_checker
  beats: { ... }
```

A name means one thing in a play: a stage entry and a beat cannot share it. A play file in the old sketch shape (`sources`, `sinks`, `inputs`, `machine`, `states`, `then`) is refused as unknown keys.

## The scene

```yaml
scene:
  initial: addition_checker
  beats:
    addition_checker:                       # in the flow: it says where to go next
      do: { map: { action: complete } }
      with: { from: additions, fields: [ group, name ] }
      to: pin_checker
    group_judge:
      do: { reduce: { action: any } }
      with: { from: group_fit }
      transitions:                          # or: the first matching transition wins
        - if: { any: { eq: true } }         # a condition over the beat's result
          to: placer
        - to: review_sender                 # no `if` means always
    done:
      final: true

    merged:                                 # performed when read: no `to:`
      do: { map: { action: pair } }
      with: { from: monarch_rows, other: amex_rows, date: date }
```

* **A beat with `to:` or `transitions:` (or `final: true`) is in the scene's flow.** The understudy performs these in order, starting at `initial`, and the flow picks the next one. A failed beat ends the run and publishes nothing. Every flow beat must be able to reach a final one.
* **A beat without them is performed when another beat first reads it**, once, and its rows are remembered. Most of a play's work is written this way: say what each piece is made from, and understudy works out the order. Write `to:` only where order matters or there is a choice.
* A beat reads stage files and beats without `to:`. It cannot read a file the play writes, or a flow beat (which may not have been performed yet); `check` refuses both, naming the beat.

### Actions

A beat's `do:` names an action **type** as a key and which one as its value. `with:` passes its props.

| `do:` | meaning |
|---|---|
| `map: { action: <name> }` | rows in, rows out: a library operation written in Python with `@stage` (below) |
| `reduce: { action: <name> }` | many rows to fewer (`blend`, `max`, `min`, `any`), written the same way |
| `write: <file>` | write rows to a stage file with `access: write` (its `from:`, or the rows of the beat before it) |
| `play: <file>.yaml` | perform another play beside this one (see Calling a play) |
| `jev: { question: choice }` | ask Jev (see Jev); performed when read, so it has no `to:` |

| `do:` | `with` | What it does |
|---|---|---|
| `map: { action: split_by_share }` | `from`, `field`, `segments` | splits a total (the sum of `field` over the rows) across `data.<segments>` by each segment's `share`: rows `{segment, share, age_min, age_max, drinks}` |
| `map: { action: join_weights }` | `probabilities`, `weights`, `into` | joins a Jev reading's probability per level with `data.<weights>` (level to option weights) into weighted rows `{<into>: option, weight}` |
| `map: { action: recipes }` | `recipes`, `packs` | turns drink counts into ingredient amounts from `data.<recipes>`, rounded up to whole packs from `data.<packs>` |
| `map: { action: where }` | `from`, `keep` | the rows that satisfy the condition `keep` |
| `map: { action: join }` | `from`, `other`, `on`, `other_on`, `keep_unmatched`, `prefix` | each row plus the fields of the row of `other` whose `other_on` (default `on`) equals its `on`, named with `prefix` before them; a row with no match is dropped, or kept as it is when `keep_unmatched` |
| `map: { action: convert }` | `from`, `dates`, `amounts`, `negate` | adds fields read from text: `dates` maps a field to the field that gets its ISO date, `amounts` to the field that gets its dollars (`(4.50)` is negative); `negate` flips the sign |
| `map: { action: number }` | `from`, `into`, `prefix` | adds `into`: the row's position from 1 after `prefix` |
| `map: { action: pair }` | `from`, `other`, `date`, `amount`, `within`, `only`, `text`, `other_text`, `rounds` | every row of two lists once, paired one to one when `date` and `amount` are equal, then within `within` business days, nearest first: flat rows `{match, method, <fields>, other_<other fields>}` |
| `map: { action: link }` | `from`, `date`, `amount`, `apart`, `id`, `within`, `rounds` | links rows of one list to each other (opposite amounts, different `apart` values, dates within `within` business days): adds `partner` and `gap` |
| `map: { action: earlier }` | `from`, `other`, `on`, `date`, `amount`, `tie`, `prefix`, `take` | for each row, one row per `other` row with the same `on`, a `date` no later and an opposite `amount` at least as large, with a `candidates` count |
| `map: { action: group }` | `from`, `by`, `collect`, `take`, `sums`, `commonest` | one row per distinct `by` value: `{key, <by>, count}`, collected values, sums (optionally `where:` a condition) and the commonest value of a field |
| `map: { action: without }` / `matching` | `from`, `among`, `on`, `among_on` | the rows whose `on` value is not / is the `among_on` value of some row of `among` |
| `map: { action: complete }` | `from`, `fields` | the rows unchanged, after checking every row has every field; the first that does not stops the run |
| `map: { action: unique }` | `from`, `field`, `among`, `among_field` | the rows unchanged, after checking no row repeats a `field` (or one in `among`) |
| `map: { action: known }` | `from`, `field`, `among`, `among_field` | the rows unchanged, after checking every `field` is some row's `among_field` in `among` |
| `map: { action: require }` | `from`, `columns` | the rows unchanged, after checking they have every named column |
| `map: { action: smallest }` | `from`, `fields`, `into` | each row plus `into`: the smallest of its named fields |
| `map: { action: share }` | `from`, `field`, `into`, `by` | each row plus `into`: its `field` as a share of the total (per `by` group) |
| `map: { action: nest }` | `from`, `other`, `on`, `other_on`, `fields`, `into` | each row plus `into`: the matching rows of `other`, each with only the named `fields` |
| `map: { action: allocate }` | `from`, `payments`, `amount`, `day`, `id`, `into` | each charge plus `into`: the `id` of the payment that settled it (oldest first, never past the payment), or null while open |
| `map: { action: top }` | `from`, `by`, `field`, `take` | the `take` rows with the highest `field` in each `by` group |
| `map: { action: set }` / `keep` | `from`, `fields` | each row plus the named fields / with only the named fields |
| `map: { action: attach }` | `from`, `other`, `field`, `into` | adds `into` to every row: the `field` values of all rows of `other` |
| `map: { action: concat }` | `from` (a list) | the rows of every piece named, one after the other |
| `map: { action: classify }` | `from`, `into`, `cases`, `otherwise` | adds `into`: the `then` of the first case the row satisfies, else `otherwise` |
| `map: { action: coalesce }` | `from`, `fields` | adds each `into: [field, ...]`: the first field the row has with a value |
| `map: { action: replace }` / `normalize` / `format` | `from` and the text props | text: replace a regular expression, lower-case and collapse spaces, fill a `{field}` template |
| `map: { action: rows }` / `mcc` | `rows` / none | a literal list of rows / the ISO 18245 merchant categories as `{group, name}` |
| `map: { action: expect }` | `probabilities`, `values`, `into` | one row `{<into>: number}`: your numbers per level averaged by a Jev reading's probabilities |
| `map: { action: adjacent_runs }`, `prefer_order`, `prefer_middle` | see `stages_rows.py` | seat blocks and the owner's row and center preferences |
| `map: { action: weigh }` | `from`, `by`, `into`, `places` | adds `into`: the sum of the `by` fields, each times its weight |
| `reduce: { action: max }`, `min` | `from`, `field`, `take` | the `take` rows with the highest (lowest) `field` |
| `reduce: { action: top_two }` | `from`, `label`, `value` | one row naming the best two rows by `value` |
| `reduce: { action: any }` | `from` | one row, `{any: true}` if the piece has any row (for a guard) |
| `reduce: { action: tally }` / `note` | `from`, `by`/`into` | the rows unchanged; `summary.json` gets a count per value / the first row |
| `reduce: { action: blend }` | `entries`, `forbid`, `on_empty`, `shortlist` | see Deciding |

`understudy check` refuses an unknown action and suggests the nearest, and checks each `with` key.

## Deciding

`blend` takes weighted entries and reduces them to one distribution per row the beat before it produced (a segment, say):

```yaml
order_matcher:
  do: { reduce: { action: blend } }
  with:
    entries:
      - decide:                     # your tree; weight defaults to 1
          if: { segment: { eq: students } }
          then:
            drink: [ { temp: iced, size: large, weight: 0.5 }, { temp: hot, size: medium, weight: 0.5 } ]
          else:
            drink: [ { temp: hot, size: medium, weight: 1.0 } ]
      - from: weather               # a beat that performs a play: its written rows are weighted rows
        weight: { if: { segment: { eq: night_workers } }, then: 0, else: 0.3 }
    forbid:                         # hard rules: drop options, always win
      - when: { age_max: { le: 17 } }
        drop: { caffeine: { ne: none } }
    on_empty: fail                  # fail (default), skip, or fallback
  to: ingredient_counter
```

* **The blend** averages each dimension over the entries that name it, weighted by the entry's `weight` (a number, or `if`/`then`/`else`; a missing `else` is 0).
* **`forbid`** drops the options a matching rule forbids and renormalizes; a row left with no option fails the run unless `on_empty` says `skip` or `fallback`.
* Options must be declared under `outcomes`; the checker refuses a typo and suggests the nearest.

### Conditions

```yaml
segment: { eq: students }            # eq ne lt le gt ge
job:     { in: [nurse, driver] }     # in not_in: a list ...
temp:    { in: [80:90] }             # ... or a slice: 80 included, 90 excluded
merchant: { has: coffee }            # has: the field contains the value
Category: { ends: ": Transfers" }    # ends: the text ends with the value
or:                                  # and or not combine; several fields in one mapping mean and
  - { genre: { eq: horror }, tomato: { ge: 70 } }
  - { tomato: { gt: 90 } }
```

`lt le gt ge` order numbers, dates, times and datetimes read from text. A field a row does not have never matches (write `not: { x: { ne: null } }` to find rows without it). Plays are read as YAML 1.2, so `70:30` stays text.

## Jev

Jev only chooses among options you list and gives probabilities; it never writes values. Ask it with a beat:

```yaml
weather_change:
  do: { jev: { question: choice } }
  with:
    instructions: Compare next week's description with last week's. How much warmer or colder is next week?
    criteria:                        # the rubric: each level and what it means
      much_colder: Clearly and markedly colder than last week.
      same: About the same.
      much_warmer: Clearly and markedly warmer.
    state:                           # the pieces Jev reads
      last_week: { from: last_week }
      next_week: { from: next_week }
```

Reading it returns one row per level, `{level, probability}`. Instead of `criteria`, `options: { from: <piece>, key: <field> }` offers the values found in rows. Your weights per level live in `data`; Jev never sees them. A Jev beat is performed when read (it has no `to:`), and a live read needs `TYPESAFE_API_KEY`.

## Props

A play declares on its stage the props it takes, with a kind, its limits and a default. The console draws a control for each; the command line and the console check a value against the declaration, and a value left alone is its default.

```yaml
stage:
  mood:     { kind: choice, label: Mood, options: [fun, serious, dramatic, romantic], default: fun }
  weight:   { kind: range, min: 0, max: 1, step: 0.05, default: 0.3 }
  tickets:  { kind: count, min: 1, max: 10, default: 2 }
  evenings: { kind: switch, default: "on" }       # on or off (quote them: YAML reads bare on as a word)
```

Every play file is a Jinja2 template over YAML 1.2: a prop reaches the file as text through `{{ }}` (`length: {{ tickets }}`). A name the file uses but does not declare is still given as text, and a template may write its own default (`{{ since | default('1900-01-01') }}`). A wrong declaration or a value outside its limits is refused before anything runs: `prop 'tickets': default 11 is outside 1 to 10`. A `--with` name the play does not use is refused with the nearest name it does use.

## Files

A stage file is `kind: file`. Read (the default) or written (`access: write`):

* **Read:** its path comes from `--with <name>=<file>` (read from where you run), else its `path:` (beside the play; from where you run when `optional`), else a call binds it. A file read with no path and no binding is refused: `stage.monarch: no file given: pass --with monarch=<file>, or a call binds it`. A name ending in `.csv` is read with its header row as field names, every value text; any other file is JSONL. An `optional: true` file that does not exist has no rows (the run says so), unless `--with` named it.
* **Written:** a `write` beat writes it into the run folder, and only when the run succeeds. Each written file has one writer, and no beat reads it (decision 7: runs stay write-once).

## Calling a play

A play can reuse another play, one it already trusts, with `do: { play: <file>.yaml }`:

```yaml
placements:                          # once per merchant: each with its category
  do: { play: categorize_merchant.yaml }
  each: unpinned
  with: { additions: additions }     # binds the called play's stage file `additions` to this play's piece
```

Running a play means providing its stage. From the command line, props come from `--with`, files read from paths, files written go to the run folder. **From a call,** the beat's `with:` provides it: a name that is a stage file of the called play binds it to the caller's piece of that name; any other name is a prop (a value, filled into `{{ }}`). The called play sees only its own stage, never the caller's other pieces, and touches no disk: **what it writes is the beat's result**. A called play that writes nothing is refused (`play x.yaml writes no file, so it gives its caller nothing`). A final beat with `outcome: none` gives its caller no rows.

### Once per row: `each`

`each: <piece>` performs the play once per row; the row's fields are its props, beside the call's `with:`. The result is every row it wrote, **each carrying the fields of the row it was played for** (a merchant's key, say):

```json
[ { "title": "It Follows", "audience": 0.9 }, { "title": "Hereditary", "audience": 0.7 } ]
```

Each row's Jev answers are captured under the called play's name and the row's position, so a replay needs no live call.

### Folding: `each` with `reduce`

```yaml
named:
  do: { play: name_each.yaml }
  each: unnamed
  reduce: { action: concat, into: earlier }
```

The iterations run in order; the rows each writes are appended to a running list, which the next receives as the prop `earlier` (empty for the first). The beat's result is that list. A called play that never uses the `into` name is refused by `check`.

## Adding an action

An action is one Python function, registered with `@stage`. Its signature is the contract of the YAML:

```python
@stage("map.split_by_share")
async def split_by_share(context, source: Source, field: str, segments: Data) -> list[dict]: ...
```

```yaml
do: { map: { action: split_by_share } }
with: { from: sales, field: drinks, segments: segments }
```

* Each parameter after `context` is a `with:` key; one with no default is required. The play writes the main input, the Python parameter `source` (or `sources` for a list), as `from:`.
* `Source` names a piece, `Data` a key under `data`; `str`, `int` or `float` is a plain value. `understudy check` reads the same signature.

## Options that exist only in data

```yaml
outcomes:
  showing: { from: showings, key: title }      # the title of every row of the piece `showings`
```

A weighted row may name any of those values; one the file does not have is refused with the nearest. A `blend` can keep only its best few (`shortlist: 5`), and a Jev beat can then choose among them with `options: { from: ranked, key: title }`.

## How a run ends

A guard (`if:` on a transition) tests the fields of a beat's result when it is a mapping or a single row, which is what `reduce.any` returns:

```yaml
block_finder:
  do: { reduce: { action: any } }
  with: { from: scored }
  transitions:
    - if: { any: { eq: false } }
      to: nothing_fits
    - to: block_picker
```

A final beat may carry an `outcome:`; the run still exits 0, records it in `run.json` and the last event, and prints `outcome: <name>` as its last line.

## Capture and replay

Every live Jev read is captured under `.understudy/cache/<run-id>/` (git-ignored; the last 5 runs are kept). `--replay` runs from the capture and never goes live:

```sh
understudy run coffee_week.yaml --replay              # the latest run that captured every Jev beat
understudy run coffee_week.yaml --replay=<run-id>     # a named run
understudy run coffee_week.yaml --replay=tests/fixtures/coffee/replay   # a folder of captures
```

A capture is keyed by the play's name and the Jev beat's name, so renaming a Jev beat makes old captures miss.

## What a run writes

`.understudy/runs/run-<stamp>-<id>/` (or `--out`, refused under `data/` or any tracked folder):

* the files the play writes, last, so a failed run publishes none;
* `summary.json`: counts only;
* `run.json` (`beats`: each flow beat complete; `failed_beat` and `error` when it failed), `events.jsonl`, `run.duckdb`.

`events.jsonl`, one JSON line per event: `run_started` names the `play`, `mode`, and the play's `plan` as the file was when the run began (and `stop_at` when the run was to hold before a beat). The plan is `{initial, props, nodes, edges}`: a node is a stage file (`kind: piece`, `write` for a file it writes) or a beat (`kind: beat`, with `flow`, `final`, `waits` for a beat performed when read, its `action` such as `map.join` or `jev.choice`, and its `with` as short text cut at 160 characters), and an edge is a `move` (a `to:` or a `transitions:` entry, with its `when` guard), a `reads` (a piece or beat that feeds a beat) or a `writes` (a `write` beat to its file). The console draws it; `understudy` itself never reads it back. Then `beat_started` / `beat_completed` / `beat_failed` (`beat`, with `reason` on failure; a called play's beats are named `caller.play[n].beat`). A `jev_read` line says what Jev answered for a Jev beat (`source`, `top` and its `probability`, the `next` level and its `next_probability`, and how many `options` it chose among; level names are cut at 60 characters), and a `beat_completed` carries the beat's `action` (`map.where`, `write:booking`, `play:seating.yaml`). A `beat_completed` also says what the beat touched, by name and as a summary, never as rows: `read` and `wrote` (each `{piece: {rows, keys, columns}}`, `keys` being the sorted column names of the first row, at most 12) and, when the beat's result is a list of rows, `made` (`{rows, keys, columns}`). `columns` (on a top-level beat only) summarizes up to 6 columns, numbers first: `{name, kind: number, rows, min, max, mean}`, `{name, kind: text, rows, distinct, top: [[value, count] x5]}` (values cut at 40 characters) or `{name, kind: other, rows}` (`src/play/profile.py`). A beat that calls a play once per row (`each`) logs an `iteration` per pass: `beat`, `index`, `of`, `item` (that row's fields, values cut at 60 characters, at most 12 fields) and `made` (`{rows, columns}` of what the pass wrote). A `jev_read` also carries `levels`, up to 8 `[name, probability]` pairs. A log written before Sprint 29 has no plan (the console says so and draws no diagram) and its beats have none of these lists. `beat_entered` (`beat`, `caused_by`: `start`, `ok` or `fail`) each time the scene moves, `paused` / `resumed` around a hold, and for every `reduce.blend` a `decision` per input row and dimension (`beat`, `row`, `dimension`, `options` with each `{name, weight, removed_by}`, `pick`, `probability`). A run ends with `run_finished` and its `outcome`. A log that does not name its play (one written before plays) shows in the console as unreadable.

Exit codes: 0 done, 1 a beat failed after the run started, 2 refused before starting. Every failure ends with one `understudy: <message>` line, never a traceback.

## Checking

`understudy check <play.yaml>` loads and checks the play and every play it calls, and starts nothing. It reports every mistake as the file, the path inside it as the play writes it, what is wrong and the nearest valid value, for example `scene.beats.split_trade.do.map.action: unknown action 'map.split_by_shar' (did you mean 'map.split_by_share'?)`. [schema/play.schema.json](../schema/play.schema.json) describes the shape for editors.
