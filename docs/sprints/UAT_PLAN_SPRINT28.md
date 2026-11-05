# UAT Plan: Sprint 28, plays

*   **Stories**: UND-105 to UND-110 (`docs/sprints/STORY_ARCH_SPRINT28.md`)
*   **Data**: the household fixtures (`tests/fixtures/household`, Jev double) and the owner's real Monarch and Amex files (`data/`, git-ignored), replayed from live run `run-20261103T215207-620ddcce`; the coffee fixture and its committed replay
*   **Baseline**: `build/baseline-sprint28/` (saved on `main` code before the first change); compare tool: `scratchpad/compare.sh` (ignores `events.jsonl`, `run.json`, `run.duckdb`, which carry ids, times and event names)
*   **Status**: Executed 2026-11-05; all scenarios passed

## Scenarios

| ID | Story / AC | Steps | Expected | Result |
|---|---|---|---|---|
| UAT-28-1 | UND-105 AC1, UND-108 AC1-2 | Run household on the fixtures; compare to `build/baseline-sprint28/fixtures` | all 11 output files byte-identical | Pass (after Phases 2, 4, 5) |
| UAT-28-2 | UND-106 AC2, UND-108 AC2 | Replay the real live run on the new play (`--replay run-20261103T215207-620ddcce`, real files); compare to `build/baseline-sprint28/full` | all 11 outputs byte-identical; no live request | Pass (Phases 2, 4, 5: `build/sprint28-phase{2,4,5}`) |
| UAT-28-3 | UND-105 AC2 | `understudy check` the household file from `main` | refused: `'scene' is a required property`; `'machine', 'sinks', 'sources' were unexpected` | Pass |
| UAT-28-4 | UND-105 AC3, UND-106 AC3-4 | Scratch plays (tests): write to an undeclared file, write to a read file, read a written file, read a flow beat, two writers, a name on stage and scene, a Jev beat with `to:`, a beat reading itself | each refused naming the path as the play writes it | Pass (`test_sketch_check.py`, `test_sketch_stage_source.py`) |
| UAT-28-5 | UND-107 AC1-4 | `test_play_calls.py`: a call binds a file and a prop; a called play in a loop; run on its own with `--with known=<file>`; unbound file; binding a written file; a play that writes nothing; reading an unbound caller piece | rows carry the played row; no child file in the run folder; refusals name the play, call and piece | Pass; real replay folder has no `placement.jsonl`/`original.jsonl` |
| UAT-28-6 | UND-109 AC1-3 | Coffee replay; read `events.jsonl` and the console view; list `.understudy/runs` | `run_started.play`, `beats`; CLI `beat weather`; "done after 5 beats"; gauges BEATS/FAILED/JEV/ELAPSED; old runs `unreadable` | Pass |
| UAT-28-7 | UND-110 AC1-4 | Read `docs/PLAYS.md`, `docs/DOMAIN.md`; search README, USER_GUIDE, ARCH, PRD, TEST_STRATEGY for `sketch` | framing first; glossary present; `sketch` only as history or named debt; ADR-0061 | Pass |
| UAT-28-8 | UND-108 AC3 | `bobp make check` | exit 0; unit suite 29 to 33 s | Pass: 601 tests, 30.4 s |

## Failure handling

A difference in any output file stops the phase (Trin rejects to Neo with the file name). None occurred.

## Evidence

`agents/CHAT.md` posts for each phase's UAT (Trin), the comparison output, and `build/build.out` of the last gate.
