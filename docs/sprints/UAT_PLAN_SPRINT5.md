# Sprint 5 Acceptance Test Plan (UAT): A decision engine - gates, scores, Jev

*   **Author**: Trin
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT5.md` (UND-18..26) · **Arch**: `docs/sprints/ARCH_SPRINT5.md`
*   **Status**: In progress - Phases 1-6 verified

## 1. Scope of Acceptance Testing

Every acceptance criterion of UND-18..26, verified per phase as it lands, then end to end by
Smith at sprint close. Out of scope: the sprint 6 dashboard; real ratings data.

## 2. Preconditions & Test Environment Setup

- `bobp make install`; Node per `.nvmrc`. Unit gate: `bobp make check`. Browser: `bobp make test-browser`.
- Live cases (UND-23, UND-26) need `TYPESAFE_API_KEY` and run through `bobp make test-live` (paid).
- Throwaway sketches for UAT live under `build/uat/` (git-ignored; inside the repo so example
  servers resolve `node_modules`).

## 3. Scenario-Driven Acceptance Test Cases

| Case | Story / AC | Steps | Expected | Evidence | Result |
|---|---|---|---|---|---|
| UAT-UND-20-01 | UND-20 AC1 | `understudy check examples/mcp`, `examples/mcp-remote`; unit suite | both OK as in sprint 4; one-server ids `tool:<name>`, calls carry no `server` | `tests/mcpServers.test.js` "with one server"; check output | PASS (Phase 1) |
| UAT-UND-20-02 | UND-20 AC2-3 | two box offices `a`, `b` in one target; look; call `b/pick_seats` | 8 tools tagged `a`/`b`; ids `tool:a/...`; call reaches `b` only; `view.last.server` = `b` | `tests/mcpServers.test.js` | PASS (Phase 1) |
| UAT-UND-20-03 | UND-20 AC4 | close a two-server target | every server stopped; a later look fails | `tests/mcpServers.test.js` "closing stops every server" | PASS (Phase 1) |
| UAT-UND-20-04 | UND-20 AC5 | `build/uat/two`: servers `a` (box office) + `ratings` (`process.exit(3)`); `understudy run` | `understudy: server "ratings" did not start: node -e process.exit(3) exited with code 3 before the MCP handshake - it printed nothing on stderr`; no box office left running | CLI output; `ps` | PASS (Phase 1) |
| UAT-UND-20-05 | UND-20 AC6 | check a sketch with `servers.ratings.type: sse`; both `server` and `servers` | refused naming `target.servers.ratings.type`; "give server: (one) or servers: (several), not both" | `tests/sketch.test.js`, `tests/mcpConfig.test.js` | PASS (Phase 1) |
| UAT-UND-18-01..06 | UND-18 AC1-6 | drive `examples/evening/boxoffice.mjs` through the MCP client | genres, showings, two screen widths, centre 0.33 / 0.79, side-by-side hold, refusal naming the run, `BOX_STATE=full` | `tests/evening.test.js` (s4-F4 = together 4, centre 0.67; E2 0.22 of 10; 0.83 vs 0.44 at 2.5 off in 30 vs 10) | PASS (Phase 2) |
| UAT-UND-19-01..04 | UND-19 AC1-4 | drive `ratings.mjs` | tomato + 3-5 reviews; the four score cases; unknown title error | `tests/evening.test.js` | PASS (Phase 2) |
| UAT-UND-21-01..05 | UND-21 AC1-5 | owner's film gate over both servers with a Jev double | no afternoon / low-score film offered; >90 non-horror offered; held-back line; check refusals | `tests/engine.test.js`, `tests/rows.test.js`, `tests/decideApp.test.js` (real evening servers: s2, s13, s8, s4 offered; s1/s6 removed with why; held said once; spent), `tests/sketch.test.js` | PASS (Phase 3) |
| UAT-UND-22-01..06 | UND-22 AC1-6 | engine over seat rows | E/F/D 1, 0.67, 0.33 (w1) and 1, 0.44, 0.11 (w2); E edge 0.4 below F centre; table in log and page | `tests/engine.test.js` (curves, product, zero, bounds, checks), `tests/decideApp.test.js` (s4 seats: F5, F6, F4; edge E removed), `tests/watchPage.test.js`; `make test-browser` 4/4 | PASS (Phase 4) |
| UAT-UND-23-01..05 | UND-23 AC1-5 | score question over reviews | asked once per row; enthusiastic > bored (live) | `tests/jevScore.test.js` with a scoring double (one request per look, nothing re-asked, `jev: { asked, reused }`, screaming reviews rank first), `tests/sketch.test.js`; live in Phase 7 | PASS (Phase 5, live pending) |
| UAT-UND-24-01..06 | UND-24 AC1-6 | `--input mood=romantic --input centre=1` | start line inputs; mood only in state; shortlist of one skips Jev; refusals | `tests/inputs.test.js`, `tests/jevScore.test.js`, `tests/cli.test.js`, `tests/sketch.test.js`; start-line `inputs` checked in Phase 7 | PASS (Phase 5) |
| UAT-UND-25-01..06 | UND-25 AC1-6 | everything gated out; a held film | `walked-away` exit 0 + sentence; no call after; `stalled` without the state; held never walks | `tests/evening.run.test.js` (BOX_STATE=full: 11 steps, no hold, `walked-away` line + sentence), `tests/library.test.js` (guard incl. Gate 2 case and held), `tests/decideApp.test.js` (stall reason) | PASS (Phase 6) |
| UAT-UND-26-01..05 | UND-26 AC1-5 | `examples/evening` live, normal and `BOX_STATE=full` | buys per the rules; `--input centre=0` changes the table; walks away; docs | `bobp make test-live` | pending |

## 4. Negative & Error Handling Test Cases

Covered in the rows above: UAT-UND-20-04/05 (server start, config), UND-21 AC5, UND-22 AC6,
UND-23 AC5, UND-24 AC5-6 (check and input refusals).

## 5. Defect Summary & Gate Outcome

- Phase 1: no defects. 213 unit tests pass, lint clean.
- Phase 2: no defects. 220 unit tests pass, lint clean. Note: a big-screen seat map exceeds the 2000-character step text; the full answer stays in the view (rows read it in Phase 3).
- Phase 3: no defects. 231 unit tests pass, lint clean.
- Phase 4: no defects. 239 unit tests, 4 browser tests pass, lint clean.
- Phase 5: no defects. 248 unit tests pass, lint clean. Rows now keep lists of plain values (a film's reviews) as facts, so `looks_at` can read them.
- Phase 6: no defects. 253 unit tests pass, lint clean. The evening sketch landed here (Phase 7 needs it for the double-played runs); live runs remain for Phase 7.
