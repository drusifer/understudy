# Sprint 28 Retro: plays

Delivered: UND-105 (a play file reads like a play), UND-106 (every computed thing is a beat; Jev is a beat), UND-107 (the stage is the play's interface; calling a play), UND-108 (the examples are plays, outputs byte-identical), UND-109 (the run record and console say play and beat), UND-110 (the docs teach the play). Seven phases plus closeout; Phase 3 folded into Phase 2.

## What went well

* **The model came from the owner in conversation, one name at a time** (decisions 19 to 42), and each answer was recorded at once. Two of the owner's pushes made it simpler, not just renamed: "a distinction without a difference" (computed sources and states are one thing, a beat) and "the set becomes the API" (the stage is the whole interface; running a play is providing its stage).
* **One translation point:** `engine_view` turned the new file into the engine's old structures, so run, capture and replay never changed, and every phase was proved by comparing the real outputs byte for byte with a baseline saved before the first change.
* **The household command line did not change** (`--with monarch=... amex=...`), because the file pieces took the names the owner already passes.

## What went wrong

* **The plan grew once in planning** (decision 42 rewrote UND-107 after the first approval) and twice while building (Jev beats had to come with the file shape; a called play's writes became the beat's result instead of a separate binding). Each change was recorded as an amendment, but the plan was first written before the model had settled.
* **Old event logs:** the first draft promised both "old runs do not replay" and a replay-based proof; Smith caught it. Then the owner said no back-compat, which removed the question.
* **Process slips:** at planning I appended decisions with shell `printf >>` and ticked a status with `sed` (Edit-only rule); once I ran a single browser test with `python -m unittest` instead of `bobp make`. The Edit tool drops trailing spaces from a replacement, which broke some test strings (caught by the tests; lesson recorded).

## By persona

* **Neo:** about 120 file edits with the Edit tool; the translation kept the risk in one place. **Trin:** the byte-identical comparison was the gate for every phase. **Morpheus:** debt recorded: internal names behind `engine_view`; the console API's `sketch`/`stage` keys. **Smith:** caught the replay contradiction at Gate 1. **Oracle:** ADR-0061, two lessons, PLAYS.md and the glossary. **Tank:** SDLC paths, `--plays`. **Mouse:** phases held at 1 to 3 tasks; two L3 tasks were the right size.

## Backlog (feeds `docs/BACKLOG.md`)

* **Sprint 29 (owner, decision 39): show the scene diagram and step through a play**, built on beats and scenes.
* Rename the engine's internals to the play words (`Play.sources` to pieces, `machine` to scene, `then` to `to`, the action parameter `source` to `from` via the registry) and remove `engine_view`'s translation; the console API keys `sketch`/`stage` to `play`/`beat`. (Neo, Morpheus)
* Rename the test files `test_sketch_*.py` to `test_play_*.py`, and the coffee fixture's flow beats to roles. (Neo)
* A test that the household's stand-ins still match what `categorize_merchant` really writes (carried from Sprint 27). (Trin)
* Earlier: YAML editor (now a play editor), Venmo and Zelle, pins for own-account merchants, browser suite to 90 s.
