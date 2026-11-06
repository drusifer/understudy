# Sprint 29 Task Board: See the whole play, and step through it

*   **Goal**: The console draws the whole play (stage pieces, beats, and who reads what) from the play file, starts a play held (before its first beat or a beat the owner picks on the diagram), and shows what each step read and wrote.
*   **Tier**: Tier 2 (story and architecture in one document)
*   **Total Points**: about 18
*   **Branch**: `sprint-29` (cut from `main` 158edd4)
*   **Status**: In progress (planned 2026-11-05)
*   **Plan**: `docs/sprints/STORY_ARCH_SPRINT29.md`. Decision: `OWNER_DECISIONS_SPRINT22.md` 43.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-05*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. **Run only the tests you changed while building; run the full unit suite once at the end of a phase; the browser suite once in Phase 4 and at closeout.** Edit files with Edit/Write only (owner rule); use `git mv` for renames. No back-compat anywhere. Commit once per reviewed phase: `Phase <N>: <summary>`.

### Phase 1: The plan of a play (UND-111, part 1)
*Phase goal: a loaded play becomes a graph of pieces and beats with reads, writes and moves, and the server returns its layout.*
- [ ] **Task 1.1:** Tests first, then `src/play/plan.py`: nodes (read piece, write piece, flow beat, beat performed when read; flags `write`, `flow`, `final`, `waits`) and edges (`move`, `reads`, `writes`) from a loaded `Play`; the reads come from `with.from`, `with.sources`, `write` beats, Jev state and options, and `do: { play }` bindings. Tested on the coffee and household plays. **L3** (many places name a piece; the read rules are the design risk). (*Owner: Neo | Trace: UND-111 AC1, ARCH "One plan" | Verification: `bobp make test ARGS="test_play_plan.py"`*)
- [ ] **Task 1.2:** Tests first, then `chart.py` lays out the plan's graph (new node kinds, a "reads" edge class, no arrow through a box) and `GET /api/plays/<file>/plan` (listed plays only; 404 otherwise; one-line reason when a play does not load). **L3**. (*Owner: Neo | Trace: UND-111 AC1, AC3, AC4 | Verification: chart and route tests*)
- [ ] **Task 1.3:** UAT: the plan of the household and coffee plays checked by eye against their YAML (every read and write listed, none invented). **L1**. (*Owner: Trin | Trace: UND-111 AC1, AC4 | Verification: verdict in `agents/CHAT.md`*)
- [ ] **Task 1.4:** Security review (plan route name check), then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict lines in `agents/CHAT.md`*)

### Phase 2: The page draws the whole play (UND-111, part 2)
*Phase goal: the new picture replaces the old chart, for a chosen play and for a run.*
- [ ] **Task 2.1:** The page draws the plan in the chart's place (pieces as tags, write pieces differently, beats as boxes, dashed outline for beats performed when read, double border for final), lit from the run's events as today; the old chart drawing and its first-line story use are replaced. A play with no flow says so. **L2**. (*Owner: Neo | Trace: UND-111 AC2, AC3, AC5 | Verification: page tests that can run without a browser; one browser check in Phase 4*)
- [ ] **Task 2.2:** UAT on the live console: pick household, see the picture; start a coffee run, watch it light up. **L1**. (*Owner: Trin | Trace: UND-111 AC2 | Verification: verdict in `agents/CHAT.md`*)
- [ ] **Task 2.3:** Security quick pass, then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict lines*)

### Phase 3: Start held and hold at a beat (UND-112)
*Phase goal: a play starts held, or held before a beat picked on the diagram.*
- [ ] **Task 3.1:** Tests first, then `Hold` with `stop_at` (reaching it switches to `hold` and clears it), `control.json` accepts it, `run_sketch(stop_at=)`, CLI `--stop-at`, and the launcher's hold choice (`hold` / `hold_at` on `POST /api/runs`, checked against the play's flow beats, secret required). **L3** (runner gate, CLI and launcher together). (*Owner: Neo | Trace: UND-112 AC3-5 | Verification: `bobp make test ARGS="test_play_control.py"` and the route tests*)
- [ ] **Task 3.2:** The page: START HELD, click a flow beat to hold before it (shown on the diagram, cleared by clicking again or by starting), "never reached" when the run ends with the hold unspent. **L2**. (*Owner: Neo | Trace: UND-112 AC1, AC2 | Verification: page tests*)
- [ ] **Task 3.3:** UAT: start held on coffee and step to the end; hold at a middle beat and see the stop; a bad `hold_at` refused. **L2**. (*Owner: Trin | Trace: UND-112 AC1-3 | Verification: verdicts*)
- [ ] **Task 3.4:** Security review (the new input), then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict lines*)

### Phase 4: See what each step read and wrote (UND-113)
*Phase goal: the log and the step view say what a beat read and wrote, in names and counts.*
- [ ] **Task 4.1:** Tests first, then the context records what a beat read; `beat_completed` carries `read` and `wrote` (names and row counts); `docs/PLAYS.md` documents them. **L2**. (*Owner: Neo | Trace: UND-113 AC1 | Verification: event tests*)
- [ ] **Task 4.2:** The step view below the diagram, live and in replay; the plan alone before a run; a log without the fields shows the beat with no error. One browser test for hold, start, stop at the beat, step and the step view. **L2**. (*Owner: Neo | Trace: UND-113 AC2, AC3 | Verification: page tests, `bobp make test-browser` once*)
- [ ] **Task 4.3:** UAT: household fixtures byte-identical to `build/baseline-sprint28/` (excluding `events.jsonl`); the step view of a household replay. **L2**. (*Owner: Trin | Trace: UND-113 AC1-4 | Verification: file comparison and verdicts*)
- [ ] **Task 4.4:** Security review (event fields carry no rows), then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict lines*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check (`*devops sdlc-check`). (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make check` exit 0*)
- [ ] **Task C.2:** Document grooming (USER_GUIDE, PLAYS, ARCH, ADR for the plan and hold-at-beat), lessons, chat report. (*Owner: Oracle | Trace: N/A — closeout | Verification: `bobp chat-report --moniker SPRINT_29 --summary "..."`*)
- [ ] **Task C.3:** End-to-end user testing against `docs/sprints/UAT_PLAN_SPRINT29.md`. (*Owner: Smith | Trace: UND-111..113 | Verification: Smith's verdict*)
- [ ] **Task C.4:** Retrospective and backlog grooming (`docs/sprints/RETRO_SPRINT29.md`). (*Owner: Mouse | Trace: N/A — closeout | Verification: retros posted*)
- [ ] **Task C.5:** Sprint launch. Merge and push only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch post*)
