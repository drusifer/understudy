# Sprint 28: Plays (Tier 2: story and architecture in one)

* **Branch**: `sprint-28` (cut from `main` 9be83be)
* **Source**: owner, 2026-11-04 and 05, in conversation; decisions 19 to 42 in `OWNER_DECISIONS_SPRINT22.md`. The owner shaped the model one name at a time; this document only collects it. Revised 2026-11-05 for decision 42 (the stage is the play's interface).
* **Owner rules**: no back-compat (old shapes are replaced, not kept beside the new ones), YAGNI, DRY, use libraries, Edit/Write only for edits, American spelling, run only the tests that changed while building.
* **Mechanism approval**: none needed (no new dependency, language, tool or make target).
* **Size**: about 23 points. **Status**: Approved. Smith Gates 1 and 2 (combined) approved 2026-11-04 after one revision, and re-approved 2026-11-05 after the revision for decision 42; security design gate: quick pass.

## Goal

A sketch becomes a **play**, and the file reads like one: a **stage** of files, a **scene** of **beats**, each beat a character doing one action with its props and going `to:` the next. The model gets simpler, not only renamed: the two ways of computing rows (a computed source and a machine state) become one thing, a beat, and Jev is a beat like any other. When the sprint is done every play, test, console label and document uses the new words, and every example gives byte-identical outputs to today. Sprint 29 (diagrams and stepping through a play) is then built on beats and scenes from the start.

## The model (owner decisions 20 to 42)

| today | a play | decision |
|---|---|---|
| sketch, and a sketch another one calls | **play**, the one file type (still `.yaml`; the top key stays `name:`). A play is the outermost configuration of an automation and can call another play to reuse it; "scene" names a play's body, not a second file type | 20, 28, 32, 42 |
| `sources:`, `sinks:` and `inputs:` | **`stage:`, the play's interface**: every prop it takes (the typed declarations `inputs:` held), every piece it reads (`kind: file`) and every piece it writes (`kind: file, access: write`). `path:` is only a default used when the play is run from the command line | 21, 30, 34, 42 |
| how a run is given its inputs | **running a play means providing its stage**: from the command line, props from `--with`, read pieces from files, write pieces as files in the run folder; from a calling play, its `with:` binds every prop, read piece and write piece to the caller's values and pieces | 42 |
| `outputs:` on a final state; `{input, output}` pairs and `unpair` after a call | gone: what a called play writes lands in the caller's piece bound to it (appended per row under `each`), carrying its own keys | 42 |
| `machine:` | **`scene:`** (`initial:` stays) | 27 |
| `states:` and every `kind: stage` source | **`beats:`**. A beat with `to:` or `transitions:` (or `final: true`) is performed in order: the scene's flow. A beat with none of them is performed when another beat first reads it by name, once | 22, 30 |
| a `kind: jev` source | a **Jev beat**: `do: { jev: { question: choice } }` with its instructions, options and state under `with:` | 29, 30 |
| `then:` | **`to:`** (the `to:` inside `transitions:` already matches) | 26 |
| `do: { sketch: { file: x } }` | **`do: { play: x.yaml }`** | 28, 31, 32 |
| `do: { sink: { name: x } }` | **`do: { write: x }`**; `x` must be a stage file with `access: write` | 35 |
| the prop `source:` (and `sources:` for a list) | **`from:`** for one piece or a list | 38 |
| values (`--with`, `with:`) | **props**, still passed with `with` | 22, 23 |
| a call's `with:` | binds **props and pieces alike**; a called play sees only its own stage, never the caller's pieces, and never touches the disk | 37, 42 |
| actions, runs, `outcomes`, `data` | unchanged | 33 |

Words used in the docs: a **piece** is anything a beat reads by name (a stage file or another beat's result); the flow beats are named as **roles** (`pin_checker`, `record_writer`); a beat performed when read keeps its data name (`merged`, `facts`).

## Assumptions made for the owner

* **The code follows the words:** the package `src/sketch/` becomes `src/play/`, `docs/SKETCHES.md` becomes `docs/PLAYS.md`, `schema/decision_sketch.schema.json` becomes `schema/play.schema.json`, and the run's events say `play` and `beat_*` where they say `sketch` and `stage_*` today.
* **An old-format file is simply refused.** No reader, fallback or old-word table (no back-compat): `check`'s existing unknown-key refusal names the key and the nearest valid one, as it does for any typo.
* **Runs recorded before this sprint** (`.understudy/runs`): no back-compat (owner, decision 41). They are not converted and the console gets no code for them; they show as the run list's existing "unreadable" state. A capture key is the play's name and the Jev beat's name (`capture_key` in `reader.py`), and Jev beats keep their names in this sprint, so one `main` run's captures can be replayed once to prove identical outputs (UND-108 AC2). That is a test tactic, not a feature.

---

## UND-105: A play file reads like a play
**Points:** 5 · **Owner:** Neo

**As** the owner writing a play,
**I want** the file to use play, stage, scene, beats, `to:`, `from:`, `write` and `do: { play: ... }`,
**so that** the words tell me what each part is for.

### Acceptance Criteria
1. A play written in the new shape (the table above) loads, passes `understudy check`, and runs.
2. `understudy check` refuses a file that uses any old key (`sources`, `sinks`, `inputs`, `machine`, `states`, `then`, `outputs`, `kind: stage`, `kind: jev`, `do: { sketch }`, `do: { sink }`, the prop `source`) as an unknown key, with the file and the path, like any other unknown key.
3. `check` refuses a `write` beat that names a file without `access: write`, any beat that reads a file with `access: write`, and two beats writing the same file.
4. The schema (`schema/play.schema.json`) describes the new shape, and an editor using it flags an old key.

## UND-106: Every computed thing is a beat
**Points:** 5 · **Owner:** Neo

**As** the owner reading a play,
**I want** one kind of step, a beat, whether it is in the scene's flow or built when it is needed, and Jev asked as a beat,
**so that** there is one place to look and one way to write a step.

### Acceptance Criteria
1. A beat with `to:` or `transitions:` (or `final: true`) is performed in order, as states are today; a beat without them is performed the first time another beat reads it, once, as a computed source is today.
2. A Jev beat (`do: { jev: { question: choice } }`) asks Jev, is captured and replayed exactly as a Jev source is today, and is asked only when something reads it.
3. A beat that reads a flow beat which has not yet been performed is refused by `check` (the read could happen before the result exists), naming both beats.
4. `check` still refuses a beat that reads itself, an unknown action, and a `from:` that names no piece.

## UND-107: The stage is the play's interface
**Points:** 5 · **Owner:** Neo

**As** the owner reusing one play inside another,
**I want** a play's stage to list everything it takes and gives (props, pieces read, pieces written), and running it, from the command line or from a call, to mean providing that stage,
**so that** a play I already trust can be reused, even once per row, without it touching the disk or reaching into its caller.

### Acceptance Criteria
1. Props are declared on the stage with their kind, limits and default (as `inputs:` declared them); the console draws its controls from them, and `--with` fills them.
2. Run from the command line, a read piece comes from the file given with `--with <piece>=<path>` or its `path:` default, and a write piece is written as a file in the run folder, only when the run succeeds (as today).
3. Called from a play, the call's `with:` binds each prop to a value, each read piece to a piece of the caller (`with: { additions: additions_file }`), and each write piece to a piece of the caller (`with: { placement: placed }`); what the called play writes becomes that piece's rows, appended per row under `each`. The called play writes no file.
4. `check` refuses a call that leaves a prop without a value or default, a read piece unbound, or a write piece unbound, naming the play, the call and the piece; and a called play cannot read anything of its caller that is not bound on its stage.

## UND-108: The examples are plays, with the same results
**Points:** 4 · **Owner:** Neo

**As** the owner,
**I want** household, its two called plays and evening rewritten in the new shape, with flow beats named as roles,
**so that** the model is proven on the real plays.

### Acceptance Criteria
1. `household.yaml`, `categorize_merchant.yaml`, `link_refund.yaml` and the evening plays are in the new shape; their flow beats have role names (`addition_checker`, `record_writer`, `group_judge`); every Jev beat and every beat performed when read keeps its current name. The called plays write what they give back (with the keys the caller joins on), and the callers' `unpair` beats are gone.
2. A household run on the fixtures (with the Jev double) and on the small Monarch and Amex sample (replaying the captures of a run made on `main` before the first change) gives byte-identical output files to that `main` run, compared file by file; `events.jsonl` is excluded because its event names change.
3. Every test fixture written as a sketch is a play; the unit suite passes in about its current time (29 to 33 s).

## UND-109: The console and the run record use the new words
**Points:** 2 · **Owner:** Neo

**As** the owner watching a run,
**I want** the console and the run's events to say play, beat and scene,
**so that** what I read on screen matches the file.

### Acceptance Criteria
1. The console's labels, the run list and the run page say play and beat where they say sketch and stage today.
2. `events.jsonl` names `play` in `run_started` and uses `beat_started`, `beat_completed` and `beat_failed`; `docs/PLAYS.md` documents them.
3. A run recorded before this sprint shows in the run list as "unreadable", the existing state for a log the console cannot read; nothing is added for old runs (decision 41).

## UND-110: The docs teach the play
**Points:** 2 · **Owner:** Oracle (with Neo for `PLAYS.md`)

**As** someone new to understudy,
**I want** the docs to explain plays with the theater framing,
**so that** the model is easy to pick up.

### Acceptance Criteria
1. `docs/PLAYS.md` replaces `docs/SKETCHES.md`, opens with the framing (a play has a stage and a scene; the understudy performs the beats) and uses only the new words.
2. `docs/DOMAIN.md` has a glossary of play, stage, piece, scene, beat, character (a role name), action, prop and run.
3. `README.md`, `docs/USER_GUIDE.md` and `docs/ARCH.md` use the new words; a search for `sketch`, `sink` and `machine:` in the current docs finds only history (CHANGELOG, older sprint files, ADRs).
4. An ADR records the model: one kind of step, the stage of files, and why a beat without `to:` waits until it is read.

---

## Architecture

* **The engine keeps its two run paths and changes how they are declared.** The loader reads `scene.beats` and sorts each beat: a beat with `to:`, `transitions:` or `final` becomes a machine state (as `machine.states` today), and every other beat becomes a computed piece (as a `kind: stage` or `kind: jev` source today). `Sources` and `run_machine` keep working unchanged on what the loader gives them. This is the smallest change that delivers UND-106, and it keeps the replay and capture code as it is.
* **The `Sketch` model** becomes `Play` with `stage` (files only, each with `access`), `beats` and `scene` fields. A flow beat's result is already readable by name (`context.results`), so a computed beat that reads one keeps working; UND-106 AC3 adds the check that it has been performed first (the flow order is a graph `check` already walks).
* **Jev beats** reuse `src/play/sources/jev.py` as it is; only its declaration moves from `sources` to `beats`. The capture key stays the play's name and the beat's name, so replays of runs made after the change are byte-identical.
* **Writes:** the `sink` stage becomes the `write` action; the run folder and the publish-on-success rule are unchanged. The stage file's `path` is the file name in the run folder, as a sink's value is today.
* **The stage as interface (UND-107):** the stage has three entry shapes: a prop (a typed declaration, today's `inputs:` entry, read by `src/play/inputs.py`), a read piece and a write piece. One binding step turns "a stage plus what the runner provides" into what a run uses, with two providers: the command line (props from `--with`, read pieces from paths, write pieces to run-folder files through the publish-on-success code that sinks use today) and a call (the call's `with:` names). For a call, read pieces are handed to the child's `Sources` as provided rows (`Sources.provide` exists); a write piece is collected in memory and becomes the caller's bound piece, appended per row under `each`. The child's `Sources` no longer falls back to the caller's pieces; that fallback is deleted. Props still fill `{{ }}` as today.
* **What goes away:** `outputs:` on a final beat, the `{input, output}` pairs an `each` call makes, and the `unpair` action if nothing else uses it. A `blend` that reads a called play's outcome (evening) reads the caller's piece bound to the child's write piece instead. Risk: a called play's written rows must carry the key its caller joins on (household's merchant key); where today's pairs supplied it, the called play writes it. Caught by the identical-output proof (UND-108 AC2).
* **Renames:** `src/sketch/` to `src/play/` and its imports, `schema/decision_sketch.schema.json` to `schema/play.schema.json`, `docs/SKETCHES.md` to `docs/PLAYS.md`, the `--with` help and the console text. Done with `git mv` for history, then the Edit tool for contents (owner rule: no scripted edits).
* **Old keys** get no code at all: the existing unknown-key check refuses them (no back-compat, decision 41).
* **Order of work:** UND-105 and 106 together (the loader), then 107, then 108 (rewrite the examples and prove identical outputs against `main`), then 109, then 110. The identical-output proof in 108 is the safety net for the whole sprint: a run folder from `main` is saved before the first change.
* **Failure modes:** a beat moved into the flow by mistake (given a `to:`) runs at a fixed point and may read a piece too early; UND-106 AC3 catches it. A missed rename in a play is refused as an unknown key (UND-105 AC2); one in the docs is found by the search in UND-110 AC3.
* **Security:** no new input, output or dependency. UND-107 narrows what a called play can read and removes its disk writes; a read piece's path still comes only from the command line or the play's default, as today. The write-once rule (decision 7) is kept by UND-105 AC3. Expected: a quick pass at the design gate.

## Out of Scope

* Showing the diagrams and stepping through a play: Sprint 29 (decision 39).
* Converting, drawing or replaying runs recorded before this sprint (decision 41).
* Acts, a play made of several scenes, and splitting household into acts: the model allows one scene per play.
* Renaming the actions themselves (`map.pair`, `reduce.blend`) or `outcomes` and `data`.
* The YAML editor, Venmo and Zelle, household cleanup.

## Open Questions

None. Answered: old runs get no back-compat (decision 41); props are declared on the stage, so there is no `inputs:` or `props:` section (decision 42).
