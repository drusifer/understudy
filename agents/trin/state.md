# Trin State — Sprint 17 Phase 5

## Context
- User authorized proceeding with UAT and test-plan review, explicitly reinforcing test pyramid and lints.
- Reviewed UND-54 AC1–5, current UAT plan, controller/CLI tests, Mouse state (stale Sprint 16; task.md remains current), and Oracle lesson about real-data sign conventions.
- Expanded docs/sprints/UAT_PLAN_SPRINT17.md with a layer-by-layer coverage matrix and six Phase 5 cases. Unit/model coverage owns deterministic rules; existing real MCP/SQLMesh/DuckDB integration owns persistence and output; CLI process smoke owns imports/exit codes. Live Jev quality remains owner acceptance, not proven by doubles.
- Added three fast CLI unit tests: option forwarding/success JSON with AsyncMock only at controller boundary, run-failure exit/error formatting, and real chmod 0555 preflight refusal before source validation. Added category-confidence assertion to the existing shared controller run; no new end-to-end success/scale scenarios.
- First QA run passed 81 Python tests, no skips, 84.322s; existing 4,700-pair case ran in 18.40s. The Make target has no supported Python test filter, so existing integration/scale cases were necessarily repeated; future Tank task should add filtering. Prior unchanged 302 JS / 29 SQLMesh evidence was reused.
- Configured `bobp make lint` passed 2026-10-27 22:52:14 (ESLint). Python has no configured linter. No new lint dependency or gate was added.
- Important defect DEF-UND54-01 (Major): UND-54 AC4 forbids private output under data/ or tracked source folders. `_check_writable` in src/etl/controller.py:58 checks only directory and OS permissions. `--out <checkout>/src` is accepted by Python CLI. Both CLI and direct controller call this helper, so fix belongs in the common preflight.
- Added failing UNIT reproduction in tests/python/test_etl_cli.py: test_output_in_a_tracked_source_directory_is_refused_without_starting_the_controller. Controller is an AsyncMock; no files are written into src. Actual exit0 vs expected2.
- Final run: `bobp make test-py`, 82 tests in 84.444s, 81 pass/1 fail, no skips, 2026-10-27 22:54:36. Captured evidence at agents/trin/phase5_destination_regression.log. Scale case 18.29s.
- judge-trace target is absent from Makefile/help (already noted by earlier sprint QA); no trace audit or UAT pass claimed. Further acceptance execution halted on the defect.

## Current Task
- Status: Phase 5 UAT FAILED; QA investigation complete, targeted fix awaiting diagnosis confirmation per fix skill. Implementation remains uncommitted from prior turn.
- No production code edits in this QA increment, no live Jev calls, private-data reads, commits, pushes or merges.
- Modified this increment: tests/python/test_etl_cli.py (new unit coverage + failing regression), tests/python/test_controller.py (confidence assertion), docs/sprints/UAT_PLAN_SPRINT17.md, this state and chat artifacts. New captured log in agents/trin/. Preserve prior Phase 5 source/dependency/CLI/doc changes recorded in agents/neo/state.md.
- QA does not approve task 5.2 or send a product pass to Smith/Morpheus while the regression fails.

## Next Steps
1. Neo obtains diagnosis confirmation as required by agents/skills/fix/SKILL.md before production edits: destination validation is missing, not a file-permission issue.
2. Proposed fix: reject project data/ and tracked/unignored project output folders before source reads; keep build/ and explicit external output folders working; resolve symlinks. Add unit allowed/forbidden/symlink cases; do not multiply full pipeline runs for path rules.
3. Verify the failing regression turns green through the project Makefile, then run the configured lints. Avoid repeating unchanged JS/model suites unless a relevant production change or required gate justifies it.
4. Resume Trin UAT at UAT-UND-54-04. Execute one actual `bobp make run` missing-input refusal smoke (no Jev call) to close the Make front-door gap. Record results and remaining live-owner limitations. Address missing judge-trace tooling without claiming a trace audit occurred.
5. On QA pass, checkpoint and hand off to Smith usability review and Morpheus phase review. Mouse owns task.md updates. No publishing without owner instruction.
