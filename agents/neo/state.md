# Neo State — Sprint 17

## Context
- Resumed Phase 5 after the previous provider stopped mid-controller implementation. The old state was Sprint 16; current scope is in task.md and docs/sprints/ARCH_SPRINT17.md.
- Owner requested Python ETL replacement, deletion of the Node ETL, no compatibility layer, and Bob Protocol.
- SQLMesh plans must skip their implicit fixture tests: run-scoped account/period environment variables alter fixture expectations. `bobp make test-etl` runs those 29 fixtures independently.
- Resolve run output paths before invoking SQLMesh from its copied project directory; relative paths otherwise resolve twice.
- Python controller follows src/etl/stages.yaml, persists decision tables, runs final_records, and publishes result.jsonl plus summary.json. Output-stage failures remove partial/public output. Identical files and Jev doubles produce identical bytes.
- JSONL carries source_rows, category/refund confidence and links. Summary includes source/pair/review/category counts, net spending, transfer leg amounts, and decisions reused.
- src/cli.mjs launches Python with streamed progress and preserved exit codes. Options: --out, --since, --amex-account. Python import path points to the checkout while file paths remain relative to the caller.
- Deleted src/etl/{run,categories,csv}.mjs and their three obsolete JS test files; package.json test:js no longer references their directory. Old standalone Python CSV converter and older SQL models remain; no compatibility path invokes them.
- Working tree is uncommitted: prior Phase 5 pyproject.toml/uv.lock, pairing.py, decisions.py, external_models, final_records model+fixture, jev_double changes; new controller/stages/CLI/tests; Node deletions; src/cli.mjs, tests/cli.test.js, package.json; README, USER_GUIDE, CHANGELOG; chat artifacts and this state. Do not sweep unrelated changes into a commit.

## Current Task
- Phase 5 implementation complete (100% implementation); task 5.1 is ready for Trin verification. No live Jev calls, private-data run, commit, push or merge.
- Verified: full test gate passed 301 JS + 76 Python + 29 SQLMesh tests before final contract additions. Updated Python suite passed 77 tests, including 4,700 synthetic pairs in 19.05 seconds with one Jev request and 4,699 reused decisions. JS bridge suite passed 302 tests.
- Final gates passed: 78 Python tests (including output-stage cleanup and 4,700 pairs in 18.54 seconds), 302 JS tests including the actual Python CLI bridge, 29 SQLMesh model tests, and lint. Product/source diff whitespace check passed. Lint findings were style-only and corrected; the second lint run found new import/environment naming issues introduced after the first run, rather than recurring failures of the first fixes.
- A filter containing an unquoted pipe expanded in the Make recipe and failed; the subsequent JS run passed all 302 tests. ARGS appended after script files does not narrow this Node test suite; do not report it as focused.

## Next Steps
1. `@Trin *qa uat phase-5`: verify UND-54 output, confidences, spending/transfer amounts, identical reruns, failed-stage cleanup, CLI options and 4,700-pair scale. Record evidence in docs/sprints/UAT_PLAN_SPRINT17.md and ask Mouse to mark task 5.1 after acceptance. Do not repeat unchanged suites without a specific verification gap.
2. Check the final run logs in CHAT.md; build/build.out currently contains the passing 302-test JS run. Prior Python and SQLMesh results are recorded above and in chat.
3. Morpheus reviews Phase 5 before any phase commit. No publishing without owner instruction. Tank must update SDLC for Python dependencies and the removed Node ETL boundary at sprint close.
4. Real-file live Jev acceptance remains held for owner direction; use doubles for automated verification.
