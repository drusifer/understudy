# Mouse State

## Context
- Sprints 1-15 complete on `main` as of 2026-10-17; see `agents/PROJECT.md`, `docs/BACKLOG.md`, and `docs/SDLC.md` for current project context.
- Owner wants to reproduce their household transaction-cleaning procedure with Understudy. Procedure document covers preserving raw inputs, cross-source reconciliation, merchant/category dictionaries, human review, calendar dedupe/trip grouping, travel tagging, taxonomy mapping, and location-aware merchant consolidation.
- Workbook export is publicly reachable and contains 8 tabs: transaction source/output, Amex transactions, merchant map, two calendar/event tabs, consolidated trips, category ontology, and pivot output. Row counts inspected, but no further row values retained. Temporary CSV/XLSX/doc exports removed.
- Owner notes Understudy may need additional primitives/operations such as joins and maps. This is the key architecture question before sprint scope.

## Current Task
- Status: Product/architecture discovery handed off to Morpheus (0% implementation).
- Proposed direction: identify the smallest composable deterministic transformation primitives needed for the procedure; then let Jev handle bounded ambiguous cases and keep approval/reporting explicit. Do not write sprint artifacts until technical shape is clear.

## Next Steps
1. Morpheus assesses how joins, maps, filters/grouping, and exception decisions fit Understudy's sketch model and what belongs in a small first increment.
2. Resume sprint planning only after architecture and scope are agreed; use a sanitized sample, keep workbook data out of repo artifacts, and start with a read-only production pilot.
