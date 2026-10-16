# Sprint 5 Task Board: A decision engine - gates, scores, Jev

*   **Goal**: an MCP sketch can play several servers and decide like a person: gates on answer rows, weighted curves multiplied into a shortlist, a Jev Score as a factor, a final Jev Choice coloured by `--input` values, and a walk-away end that succeeds. The owner's evening is the example.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 29 (UND-18 3, UND-19 2, UND-20 5, UND-21 3, UND-22 5, UND-23 3, UND-24 3, UND-25 2, UND-26 3) - kept whole by the owner ("go big or go home")
*   **Branch**: `sprint-5`
*   **Stories / Arch**: `docs/sprints/USER_STORIES_SPRINT5.md`, `docs/sprints/ARCH_SPRINT5.md` (sprint 4 board: `docs/sprints/TASKS_SPRINT4.md`)
*   **Status**: In progress - Phases 1-3 done; Phase 4 next. Note: `test-live` skips nothing - `examples/evening` has no sketch until Phase 7, so do not run test-live before then
*   **Commits**: one local commit per phase after Morpheus's review (`Phase <N>: ...`); publishing only via `bobp make push` when the owner asks (SDLC §6). No back-compat (owner rule).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` present; `sprint-5` cut from `main` (51fa684). No Tank Phase 0: ARCH §7 adds no dependency, language or runtime. The `test-live` change is Tank's, in Phase 7. (*Owner: Mouse*)

---

## Sprint Execution Phases

### Phase 1: Several servers in one sketch - UND-20
*Phase goal: `target.servers` (inline or `servers.json`) starts/connects every server; moves, step lines and the watch feed name the server; one-server sketches unchanged.*
- [x] **Task 1.1:** `mcpConfig.mjs` resolves `server:` or `servers:`; `targets/mcp.mjs` one client per server, look merges tools tagged `server`, move calls the named server, all stopped on end/failure/Ctrl-C, a failed start stops the started ones and names the server; `apps/mcp.mjs` ids `tool:<server>/<name>` only with >1 server; step line `server`; watch feed shows it; `check` validates each entry. Tests with two in-repo stdio servers (one failing to start). TDD. (*Owner: Neo | Verification: `bobp make test`; `bobp make lint`*)
- [x] **Task 1.2:** UAT UND-20 AC1-6 (existing MCP examples' runs unchanged; two-server run; failing server message; Ctrl-C stops both) then Morpheus review vs ADR-0022. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 1`*)

### Phase 2: The evening's servers - UND-18, UND-19
*Phase goal: `examples/evening/boxoffice.mjs` and `ratings.mjs` answer everything the stories need, including the `BOX_STATE=full` case.*
- [x] **Task 2.0 (Phase 1 review note):** `run.mjs` "exited before the end state" uses `target.describe()`, which lists every server - name only the one that exited. (*Owner: Neo*)
- [x] **Task 2.1:** `boxoffice.mjs` (≥5 films with genres, nested showings with `starts`/`screen`, two screen widths, `seat_map` with `seat`/`row`/`number`/`together`/`centre` per ARCH §5 formula, `pick_seats(seat,count)` side-by-side hold or refusal naming the run, `pay`, `BOX_STATE=full`); `ratings.mjs` (`rating(title)` → tomato + 3-5 reviews, the four score cases, unknown title error). Tests drive both through the MCP client. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 2.2:** UAT UND-18 AC1-6, UND-19 AC1-4 (centre 0.33 at 3 off in width 10, 0.79 in width 30; the three seat-map cases; refusals) then Morpheus review. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 2`*)

### Phase 3: Answer rows and gates - UND-21
*Phase goal: decided arguments take candidates from remembered rows with joined facts; gates remove (with why) or hold back (with the missing fact); spent values are not re-offered.*
- [x] **Task 3.1:** `src/rows.mjs` (remember non-error answers, rows with inherited scalars, `rowsFor(field)`, join by key, 500-row bound); `src/engine.mjs` gates (`is`/bare, `in`, `at_least`, `at_most` numbers and `HH:MM`, `any`) → passing/removed/held; `apps/mcp.mjs` decided path + spent values; `sketch.mjs` loads/checks `decide.*.gates`, `join`, `field`; step line `decided.removed/held`; `held` event once. Unit tests for rows and gates; app tests over a fake view. TDD. (*Owner: Neo | Verification: `bobp make test`; `bobp make lint`*)
- [x] **Task 3.2:** UAT UND-21 AC1-5 (owner's film gate over the evening servers via a double Jev; held-back message; check refusals name file, gate, word) then Morpheus review vs ADR-0017. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 3`*)

### Phase 4: Scores and the shortlist - UND-22
*Phase goal: weighted curves multiplied rank what passes; zero drops; shortlist bounds; the score table is in the log and on the watch page.*
- [ ] **Task 4.1:** `engine.mjs` factors (`range`, `order`, weight curve, weight 0 off, product, ties by first seen, `shortlist` `at_most`/`total.at_least`); decided candidates = shortlist; step line `decided.table` (shortlist + ≤10 zeroed); watch page renders the table, removed and held; `check` refusals for factors. Tests: the worked numbers (E/F/D at w1, w2; E edge 0.4 vs F centre). (*Owner: Neo | Verification: `bobp make test`; `bobp make test-browser`*)
- [ ] **Task 4.2:** UAT UND-22 AC1-6 then Morpheus review vs ADR-0018/0019. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 4`*)

### Phase 5: Jev's Score, inputs and the final pick - UND-23, UND-24
*Phase goal: a `type: score` question with `looks_at`/`levels` is a factor (asked once per row, batched); inputs from `--input` set weights and colour the final Choice; a shortlist of one skips Jev.*
- [ ] **Task 5.1:** `sketch.mjs` score questions (`looks_at`, ≥2 `levels`), `ask:` factors, `inputs:` and `pick:` checks (unknown input, default out of range); `src/inputs.mjs` + `cli.mjs --input` refusals; start line `inputs`; Score batch per look with run cache (log notes reuse); `fill.mjs` final Choice with pick instructions + `with` inputs; shortlist of one taken without Jev. Tests with a double Jev (Score answers, request count, mood in state only). TDD. (*Owner: Neo | Verification: `bobp make test`; `bobp make lint`*)
- [ ] **Task 5.2:** UAT UND-23 AC1-5, UND-24 AC1-6 then Morpheus review vs ADR-0020. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 5`*)

### Phase 6: Walk away - UND-25
*Phase goal: `nothing_qualifies` + a `walked-away` final state end the run with exit 0 and an explanation; without it, `stalled` says what was removed.*
- [ ] **Task 6.1:** look actor output carries `decisions`; guard `nothing_qualifies` (ARCH §4 as amended at Gate 2); outcome `walked-away` from the tagged final state, `walked-away` event line + stderr sentence; no call after an empty shortlist; `idle()` lists removals; held values never count. Tests: all showings gated out (no seat map read) walks away; held film does not. (*Owner: Neo | Verification: `bobp make test`*)
- [ ] **Task 6.2:** UAT UND-25 AC1-6 then Morpheus review vs ADR-0021. (*Owner: Trin → Morpheus | Verification: `bobp make check`; commit `Phase 6`*)

### Phase 7: The owner's evening - UND-26
*Phase goal: `examples/evening` buys the owner's seats live, walks away when full, and the docs teach decide/inputs/several servers.*
- [ ] **Task 7.1:** `examples/evening/sketch.yaml` (ARCH §5 with the example defaults); `docs/SKETCHES.md`, `docs/MCP_GUIDE.md` "Deciding like a person", `docs/USER_GUIDE.md` (`--input`, `walked-away`). (*Owner: Neo, Oracle for docs | Verification: `bobp make check`; a live run by hand*)
- [ ] **Task 7.2:** `test-live` gains the evening buy run and the `BOX_STATE=full` walk-away run and checks each final `outcome` (Mechanism change, SDLC §6). (*Owner: Tank | Verification: `bobp make test-live`*)
- [ ] **Task 7.3:** UAT UND-26 AC1-5 (`--input centre=0` changes the table) then Morpheus review. (*Owner: Trin → Morpheus | Verification: `bobp make test-live` + `bobp make check`; commit `Phase 7`*)

---

## Sprint Close

- [ ] **Task C.1:** `*devops sdlc-check` - from-clean rebuild, targets as documented, Last verified line. (*Owner: Tank*)
- [ ] **Task C.2:** `*ora groom` - ADR-0017..0022 into `docs/DECISIONS.md`, lessons, `*ora report sprint-5`. (*Owner: Oracle*)
- [ ] **Task C.3:** `*user test` against `docs/sprints/UAT_PLAN_SPRINT5.md` (Trin writes it in Phase 1). (*Owner: Smith*)
- [ ] **Task C.4:** retro, then `*pm launch sprint-5`. (*Owner: All → Cypher*)
