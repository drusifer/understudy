# Sprint 28 Task Board: Plays

*   **Goal**: A sketch becomes a play: a stage that is the play's whole interface (props, pieces read, pieces written), a scene of beats (computed sources and states become one thing, and Jev is a beat), `to:`, `from:`, `write`, and running a play means providing its stage, from the command line or from a call. Every example gives byte-identical outputs, and the code, console and docs use the new words.
*   **Tier**: Tier 2 (story and architecture in one document)
*   **Total Points**: about 23
*   **Branch**: `sprint-28` (cut from `main` 9be83be)
*   **Status**: Complete 2026-11-05 (launched); branch `sprint-28` committed, not merged or pushed
*   **Plan**: `docs/sprints/STORY_ARCH_SPRINT28.md`. Decisions: `OWNER_DECISIONS_SPRINT22.md` 19 to 42.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-04*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. **Run only the tests you changed while building; run the full unit suite once at the end of a phase; the browser suite once in Phase 6 and at closeout.** Edit files with Edit/Write only (owner rule); use `git mv` for renames. No back-compat anywhere (decision 41).

### Phase 1: The baseline and the package rename (no behavior change)
*Phase goal: a saved `main` baseline to compare against, and the code named for plays.*
- [x] **Task 1.1:** Save the baseline before any change: a household run on the fixtures with the Jev double, and a replay of a captured run. Done: `fixtures/` (Jev double, repeatable byte for byte) and `full/` (replay of live run-20261103T215207 on the real Monarch and Amex files, 3m18s; the newest run was a coffee fixture, not the sample) in `build/baseline-sprint28/`. **L1**. (*Owner: Trin | Trace: UND-108 AC2 | Verification: the two folders exist and their file list is posted in `agents/CHAT.md`*)
- [x] **Task 1.2:** `git mv src/sketch src/play`, `Sketch` to `Play` and every import, `schema/decision_sketch.schema.json` to `schema/play.schema.json`. No file-format change yet. **L2**. (*Owner: Neo | Trace: STORY_ARCH_SPRINT28 Architecture, Renames | Verification: `bobp make lint` and `bobp make test`*)
- [x] **Task 1.3:** Security quick pass, then code review (passed; committed bd2b4dd). **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: `security gate (phase 1): ...` and the review result in `agents/CHAT.md`*)

### Phase 2: The play file shape (UND-105, UND-106 AC1, 3, 4)
*Phase goal: plays load and check in the new shape, with every beat in `scene.beats`, and every example and fixture rewritten mechanically to it.*
- [x] **Task 2.1:** Tests first, then the loader, model, `check` and schema: `stage` of files with `access`, `scene`/`beats`, a beat with `to:`/`transitions:`/`final` as a flow beat and any other beat performed when read, `to:` for `then:`, `from:` for `source:`/`sources:`, `do: { write: x }`, `do: { play: x.yaml }`, the `inputs:` declarations moved onto the stage as props; the refusals in UND-105 AC2 and 3 and UND-106 AC3 and 4. Rewrite every example and test fixture to the new shape, names unchanged. **L3** (loader, check, schema and every play at once; the flow/read split is the one design choice). (*Owner: Neo | Trace: UND-105, UND-106 | Verification: `bobp make test ARGS="test_play_*.py"` while building, then `bobp make check`*)
- [x] **Task 2.2:** UAT: each refusal on a scratch play; household fixtures byte-identical to `build/baseline-sprint28/` (excluding `events.jsonl`). Done: fixtures and the real-file replay both byte-identical; old `main` household refused. **L2**. (*Owner: Trin | Trace: UND-105 AC1-3, UND-106 AC1, 3, 4 | Verification: verdicts and the file comparison in `agents/CHAT.md`*)
- [x] **Task 2.3:** Security review, then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: `security gate (phase 2): ...` and the review result in `agents/CHAT.md`*)

### Phase 3: Jev is a beat (UND-106 AC2) — done inside Phase 2
*Phase goal: Jev questions are beats, captured and replayed as before. Folded into Phase 2 (2026-11-05): the rewritten files had nowhere else to put their Jev questions. Verified by the Phase 2 replay (capture keys unchanged).*
- [x] **Task 3.1:** Tests first, then `do: { jev: { question: choice } }` beats in place of `kind: jev` stage entries, reusing `sources/jev.py`; capture keys unchanged (play name and beat name). Rewrite the examples' Jev entries. **L2**. (*Owner: Neo | Trace: UND-106 AC2 | Verification: the Jev and capture tests, then `bobp make check`*)
- [x] **Task 3.2:** UAT: the sample replay of the baseline captures gives byte-identical outputs (excluding `events.jsonl`). **L1**. (*Owner: Trin | Trace: UND-106 AC2, UND-108 AC2 | Verification: the file comparison in `agents/CHAT.md`*)
- [x] **Task 3.3:** Security review, then code review. **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict line and review result in `agents/CHAT.md`*)

### Phase 4: The stage is the play's interface (UND-107)
*Phase goal: running a play means providing its stage; a called play sees only its stage and never touches the disk.*
- [x] **Task 4.1:** Tests first, then one binding step with two providers: the command line (props from `--with`, read pieces from paths or `path:` defaults, write pieces to run-folder files on success) and a call (`with:` binds props, read pieces and write pieces to the caller's; written rows collected in memory and appended per row under `each`). Delete the fallback to the caller's pieces, `outputs:` and the `{input, output}` pairs; `check` refuses an unbound prop or piece. Update household's two calls (the called plays write their merchant/refund keys; the `unpair` beats go) and evening's (its `blend` reads the bound piece). **L3** (the run, `check` and three plays change together; one trade-off: what the called play must now write). (*Owner: Neo | Trace: UND-107, UND-108 AC1 | Verification: the call and binding tests, then `bobp make check`*)
- [x] **Task 4.2:** UAT: UND-107 AC1-4 on scratch plays (including a called play in a loop writing nothing to disk); household fixtures and the sample replay still byte-identical to the baseline. **L2**. (*Owner: Trin | Trace: UND-107, UND-108 AC2 | Verification: verdicts and the file comparison in `agents/CHAT.md`*)
- [x] **Task 4.3:** Security review (this phase changes what a called play can read), then code review (passed; committed 403038a). **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict line and review result in `agents/CHAT.md`*)

### Phase 5: The examples read as plays (UND-108)
*Phase goal: flow beats have role names, and the outputs are proven identical.*
- [x] **Task 5.1:** Rename the flow beats in household, categorize_merchant, link_refund and the evening plays to roles (`addition_checker`, `record_writer`, `group_judge`, ...); Jev beats and read-when-needed beats keep their names. Update the tests that name them. **L2**. (*Owner: Neo | Trace: UND-108 AC1, 3 | Verification: `bobp make check`; unit suite time posted (29 to 33 s)*)
- [x] **Task 5.2:** UAT: fixtures and sample replay byte-identical to the baseline (excluding `events.jsonl`). **L1**. (*Owner: Trin | Trace: UND-108 AC2 | Verification: the file comparison in `agents/CHAT.md`*)
- [x] **Task 5.3:** Security quick pass, then code review (passed; committed 1785623). **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict line and review result in `agents/CHAT.md`*)

### Phase 6: The console and the run record (UND-109)
*Phase goal: what the owner reads on screen matches the file.*
- [x] **Task 6.1:** Tests first, then `run_started` names `play`, `beat_started`/`beat_completed`/`beat_failed` replace the `stage_*` events, and the console's labels say play and beat. An old run shows as the existing "unreadable" state, with no code added for it. **L2**. (*Owner: Neo | Trace: UND-109 | Verification: the view and event tests, then `bobp make check` and `bobp make test-browser` once*)
- [x] **Task 6.2:** UAT: a household run on the console reads play and beat everywhere; an old run shows as unreadable. **L1**. (*Owner: Trin | Trace: UND-109 AC1-3 | Verification: verdicts in `agents/CHAT.md`*)
- [x] **Task 6.3:** Security quick pass, then code review (passed; committed). **L1**. (*Owner: Switch, then Morpheus | Trace: design gate | Verification: verdict line and review result in `agents/CHAT.md`*)

### Phase 7: The docs teach the play (UND-110)
*Phase goal: a newcomer learns the play from the docs.*
- [x] **Task 7.1:** `git mv docs/SKETCHES.md docs/PLAYS.md` and rewrite it with the framing; a glossary in `docs/DOMAIN.md`; `README.md`, `docs/USER_GUIDE.md` and `docs/ARCH.md` in the new words. **L2**. (*Owner: Oracle, with Neo for `PLAYS.md` | Trace: UND-110 AC1-3 | Verification: a search for `sketch`, `sink` and `machine:` in the current docs finds only history, posted in `agents/CHAT.md`*)
- [x] **Task 7.2:** The ADR for the model (ADR-0061) (one kind of step, the stage of files, why a beat without `to:` waits until it is read). **L1**. (*Owner: Morpheus | Trace: UND-110 AC4 | Verification: the ADR file and the DECISION rubric line*)
- [x] **Task 7.3:** Review of the docs (approved; committed a2139f3). **L1**. (*Owner: Smith | Trace: UND-110 | Verification: review result in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [x] **Task C.1:** SDLC conformance check (`*devops sdlc-check`): the renamed package and schema are what the Makefile and SDLC name. Done without `distclean` (no manifest change since `main`; a full `bobp make check` exit 0, 601 tests), as in Sprints 23 to 27. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make distclean && bobp make install && bobp make check`*)
- [x] **Task C.2:** Document grooming, lessons, and chat report (CHAT archive left for the owner, as in Sprint 27). (*Owner: Oracle | Trace: N/A — closeout | Verification: `bobp chat-report --moniker SPRINT_28 --summary "..."`*)
- [x] **Task C.3:** End-to-end user testing and lesson review against `docs/sprints/UAT_PLAN_SPRINT28.md`. (*Owner: Smith | Trace: UND-105..110 | Verification: Smith's verdict in `agents/CHAT.md`*)
- [x] **Task C.4:** Sprint retrospective and backlog grooming (`docs/sprints/RETRO_SPRINT28.md`). (*Owner: Mouse | Trace: N/A — closeout | Verification: retros posted in `agents/CHAT.md`*)
- [x] **Task C.5:** Sprint launch (posted 2026-11-05). Merge and push only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch post in `agents/CHAT.md`*)
