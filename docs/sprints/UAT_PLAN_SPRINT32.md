# UAT Plan: Sprint 32, the beat box

*   **Stories**: UND-118 to UND-120 (`docs/sprints/STORY_ARCH_SPRINT32.md`)
*   **Data**: the owner's real Monarch and Amex files replayed from live run `run-20261103T215207-620ddcce`; the evening play replayed from `run-20261106T170350-6ca3903d`; seeded runs in the browser tests
*   **Baseline**: `build/baseline-sprint28/full`
*   **Status**: Executed 2026-11-06

## Scenarios

| ID | Story / AC | Steps | Expected | Result |
|---|---|---|---|---|
| UAT-32-1 | UND-118 AC5 | Replay the real household run with the real files; compare to the baseline | all 11 outputs byte-identical; 1282 `iteration` events; `events.jsonl` 1.06 MB to 3.49 MB | Pass |
| UAT-32-2 | UND-118 AC1-4 | `test_play_profile.py`, the evening event tests, the coffee story tests | profiles, the iteration event, Jev levels, nothing larger than 6 columns or 5 top values per piece | Pass |
| UAT-32-3 | UND-119 AC1-2 | Live console, evening replay: choose the run, click `booker` | IN `booked`, OUT `booking` as labeled values (one row each), status done | Pass |
| UAT-32-4 | UND-119 AC3-4 | Click `scored`, then `pick` | `scored`: pass 8 of 8 with its row and what it made; `pick`: Jev bars, `UNSURE` at 0.67 | Pass |
| UAT-32-5 | UND-119 AC2, 5 | Browser tests: gauge, donut and bars with text equivalents; stepper by keyboard; a log without the lists | each chart has an accessible name; no error for an older log | Pass |
| UAT-32-6 | UND-119 AC5 | Contrast test in all six looks with the new classes | readable in every theme and mode | Pass (three clean runs) |
| UAT-32-7 | UND-120 AC1-3 | Search the page for the removed panels; read the run header | no `#decisions`, `#jev`, `#summary`, `#tube`, `#step-view`; one header line | Pass |
| UAT-32-8 | all | `bobp make check`, `bobp make test-browser` | 659 unit tests (about 32 s); browser 51/51 (about 100 s) | Pass |

## Failure handling

A difference in an output file stops the phase (Trin rejects to Neo). None occurred. A measuring test that fails only when the page redraws is made to look again, not loosened.

## Evidence

`agents/CHAT.md` UAT posts, screenshots read during the sprint, `build/sprint32-phase1/`, `build/build.out`.
