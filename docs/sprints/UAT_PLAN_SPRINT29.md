# UAT Plan: Sprint 29, see the whole play and step through it

*   **Stories**: UND-111 to UND-113 (`docs/sprints/STORY_ARCH_SPRINT29.md`)
*   **Data**: the evening and household examples; a three-beat scratch play (`flow.yaml`) for the live console check; the owner's real Monarch and Amex files (`data/`, git-ignored) replayed from live run `run-20261103T215207-620ddcce`
*   **Baseline**: `build/baseline-sprint28/full` (outputs byte for byte; `events.jsonl`, `run.json` and `run.duckdb` carry ids and times and are not compared)
*   **Status**: Executed 2026-11-05

## Scenarios

| ID | Story / AC | Steps | Expected | Result |
|---|---|---|---|---|
| UAT-29-1 | UND-111 AC1, AC4 | Build the plan of household, evening, coffee; compare with the YAML | every stage file and beat is a node, every `write` beat has a `writes` edge, every read is a `reads` edge; household: 14 files (4 read, 10 written), 152 nodes, 174 edges; no arrow through a box | Pass |
| UAT-29-2 | UND-111 AC2, AC3 | Open the console, pick evening, read the plan; start a run and watch the beats light | rounded file tags, dashed waiting beats, double-bordered finals, guards labeled; the current beat lit | Pass (screenshot read; browser tests) |
| UAT-29-3 | UND-112 AC1 | Real console and child: `POST /api/start` with `hold: true` on the scratch play | run reads `paused before first`; RESUME ends it done after 3 beats | Pass |
| UAT-29-4 | UND-112 AC2, AC3 | `hold_at: second`; STEP; RESUME. Then `hold_at: done` | `paused before second`, after STEP `paused before third`, RESUME done; a final beat refused 400 naming first, second, third | Pass |
| UAT-29-5 | UND-112 AC2 | Browser: click a beat, click again, Enter and Space on a focused beat, then PLAY | the hold is shown on the diagram and in the note, cleared by a second click, the start sends `--stop-at` and spends it | Pass (browser tests) |
| UAT-29-6 | UND-112 AC5 | Run ends without reaching its beat (unit test) | the ending line says `never reached <beat>` | Pass |
| UAT-29-7 | UND-113 AC1, AC4 | Replay the real live run with the real files on the new code; compare outputs to `build/baseline-sprint28/full` | all 11 outputs byte-identical; 3786 `beat_completed` lines all carry `read` and `wrote`; none of 77 payee values appears in them | Pass |
| UAT-29-8 | UND-113 AC2, AC3 | Browser: step view follows the run, a clicked beat shows what it read and made, a beat logged without the lists shows without error | `sales: 3 rows (keys: drinks, week)`, `result: 1 row (keys: total)`; no error | Pass (browser tests) |
| UAT-29-9 | all | `bobp make check` and `bobp make test-browser` | exit 0, 636 tests in about 31 s; browser 44/44 in about 112 s | Pass |

## Failure handling

A difference in an output file stops the phase (Trin rejects to Neo with the file name). None occurred. A browser failure caused by a deliberate change (diagram nodes became buttons) is fixed in the test only when the new accessible name is right; three expectations and the keyboard test's identifier were updated for that reason.

## Evidence

`agents/CHAT.md` posts for each phase's UAT (Trin), `build/sprint29-phase4/` (the replay), and `build/build.out` of the last gate.
