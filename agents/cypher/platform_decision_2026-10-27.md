# Platform decisions, owner, 2026-10-27

Recorded by Cypher from the conversation. Nothing here is built yet.

## Decisions
1. **Python for all of understudy.** The Node implementation is replaced outright (no back-compat, no dual runtime, existing sketches and examples are rewritten).
2. **Sketch configs stay no-code and custom** (`sketch.yaml`). Understudy's value is that a person describes an app without writing code.
3. **Invent no new ETL language and no new state machine representation.** Use existing standards:
   - ETL: SQL on DuckDB, run by SQLMesh (the Sprint 16 build already does this).
   - Statecharts: `python-statemachine` and its own YAML representation, chosen by the owner.
4. **No XML.** SCXML is out. PySCXML is also abandoned (last release 0.8.3, 2012-01-08, needs PyV8).
5. **Jev from Python** through `typesafe-sdk` (sync `TypeSafeClient`, async `AsyncTypeSafeClient`; Noul, Choice and Score confirmed in the quickstart).

## Not yet verified (Cypher did not confirm)
- How much of the XState-shaped `turn:` (tags `move`/`safe`, guards with params, `invoke` of `look`/`play`, flat states, `final`) maps onto python-statemachine's YAML representation.
- Whether `typesafe-sdk` exposes per-answer probabilities the way the JS SDK does (the confidence and Noul bands depend on it).
- Per-call batching, timeout and error behaviour of the Python SDK.

## Known risks of the port
- `elkjs` (dashboard flow layout, computed on the server) has no mature Python port.
- `xstate` is the core of `src/machine.mjs` and `src/seat.mjs`.
- The dashboard's browser side (`page.mjs`, CSS) stays JavaScript.
- Size to port: about 6,300 lines of server code across 18 core modules, 5,000 lines of tests, 570 lines of examples.

## Consequences for Sprint 16
- The `sprint-16` worktree already holds a built, uncommitted SQLMesh ETL (phases 0-2 done, C.1 done, C.2-C.5 open).
- The new stories (`docs/sprints/USER_STORIES_SPRINT16.md`, written 2026-10-27) overwrote the original approved stories; the original is not recoverable from git.
- The port needs its own epic (Cypher and Morpheus framing), then sprints.
- Open: close Sprint 16 as built and plan the sign-flipped dedupe, transfers, refunds, MCC naming and MCP source servers as the next sprint, or redo reconciliation inside Sprint 16.
