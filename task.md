# Sprint 27 Task Board: the test pyramid

*   **Goal**: The gate is fast because end-to-end tests are rare and fast and everything else is tested lower: Python unit suite at most 30 s (from 94.6 s), browser suite at most 90 s with no flake (from 154.9 s), at most five whole-sketch household runs (from about 53), and a faster product (child sketches load once per file, not twice per row).
*   **Tier**: Tier 2 (tech debt; story and architecture in one document)
*   **Total Points** (optional): 18
*   **Branch**: `sprint-27` (cut from `main` e2a7b6d)
*   **Status**: Planning — awaiting Morpheus Step 3a Review
*   **Plan**: `docs/sprints/STORY_ARCH_SPRINT27.md` (Gates 1 and 2 combined), security design gate: quick pass. Decisions: `OWNER_DECISIONS_SPRINT22.md` 17 and 18. Baseline: `unittest --durations` run of 2026-11-03.

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`; present 2026-11-03*)

---

## Sprint Execution Phases

Complexity levels follow `agents/templates/_template_task.md`. Each phase is one build task followed by its gates. **Run only the tests you changed while building; run the full unit suite once at the end of a phase and the browser suite once in Phase 4 and at closeout. Do not chain the gate.** Edit files with Edit/Write only (owner rule).

### Phase 1: Child sketches load faster (UND-101, 3 pts)
*Phase goal: the row-independent read of a child sketch is done once per file version.*
- [ ] **Task 1.1:** Tests first (the same child loaded many times is read once; an edited file is read again; the loaded sketch is equal to an uncached one; a caller cannot corrupt the cache), then `functools.lru_cache` on the lenient declared-inputs read keyed by path and `st_mtime_ns`. Measure per-row load before and after on the household child. **L2**. (*Owner: Neo | Trace: UND-101 AC1-3 | Verification: `bobp make test ARGS="test_sketch_template*.py"` and the loader tests, `bobp make lint`*)
- [ ] **Task 1.2:** UAT: a household run on the fixtures gives byte-identical outputs before and after (compare the run folders); the micro-measurement of the per-row load. **L1**. (*Owner: Trin | Trace: UND-101 AC2-3 | Verification: UAT verdict and numbers in `agents/CHAT.md`*)
- [ ] **Task 1.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 1): ...`*)
- [ ] **Task 1.4:** Code review. **L1**. (*Owner: Morpheus | Trace: STORY_ARCH_SPRINT27 UND-101 | Verification: result in `agents/CHAT.md`*)

### Phase 2: Compute one stage on its own (UND-102 part 1, 4 pts)
*Phase goal: a fragment harness, proven by moving one household file down.*
- [ ] **Task 2.1:** Tests first, then `src/sketch/fragment.py` (`read_stage` with `stubs`), the `compute` closure in `run_sketch` shared with it (no copy), and `tests/python` helpers; move `test_household_payments.py` to it (rules at the fragment level, one whole-sketch run kept for the happy path). **L3** (refactor of the run's core; the proof the approach works). (*Owner: Neo | Trace: UND-102 AC1-3, ARCH UND-102 | Verification: the moved tests and `bobp make test ARGS="test_sketch_run*.py"`, `bobp make lint`*)
- [ ] **Task 2.2:** UAT: break each payment rule in a scratch copy (allocation order, the card's dates, the 5% flag, the open balance) and see its moved test fail; time the file before and after. **L2**. (*Owner: Trin | Trace: UND-102 AC3 | Verification: UAT verdict, the broken rules and times in `agents/CHAT.md`*)
- [ ] **Task 2.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 2): ...`*)
- [ ] **Task 2.4:** Code review. **L2**. (*Owner: Morpheus | Trace: STORY_ARCH_SPRINT27 UND-102 | Verification: result in `agents/CHAT.md`*)

### Phase 3: The rest of the household rules (UND-102 part 2, 4 pts)
*Phase goal: at most five whole-sketch household runs; the household tests take 15 s or less.*
- [ ] **Task 3.1:** Move the remaining household tests (`test_household.py`, `_categorize`, `_crosswalk`, `_pins`, `_taxonomy`) to the fragment level in groups, keeping a whole-sketch run only where it shows something only a whole run can (happy path with shared outputs, a refusal before Jev, an empty period, a replay, the console's real start); each group is checked by breaking its rule. **L3**. (*Owner: Neo | Trace: UND-102 AC2-4 | Verification: `bobp make test ARGS="test_household*.py"`, `bobp make lint`*)
- [ ] **Task 3.2:** UAT: the list of tests moved with the rule each guards and the break-it result; the count of whole-sketch runs and the household suite time against the budget. **L2**. (*Owner: Trin | Trace: UND-102 AC2-4 | Verification: UAT verdict and table in `agents/CHAT.md`*)
- [ ] **Task 3.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 3): ...`*)
- [ ] **Task 3.4:** Code review. **L2**. (*Owner: Morpheus | Trace: STORY_ARCH_SPRINT27 UND-102 | Verification: result in `agents/CHAT.md`*)

### Phase 4: The browser suite shows only what a browser can (UND-103, 5 pts)
*Phase goal: contrast from the declared color pairs in Python; the browser keeps two looks; no flake; 90 s or less.*
- [ ] **Task 4.1:** Tests first (`tests/python/test_theme_contrast.py`: every declared text and background pair of the three themes, light and dark, meets WCAG AA; a deliberately bad pair is caught), then cut `ContrastTest`, `DecisionPanelTest`, `ReplayBarTest` and the other "readable in every look" tests to one light and one dark look, measure the stage lamp with animation and transition off, and write in each remaining browser test's docstring the thing only a browser shows. **L3**. (*Owner: Neo | Trace: UND-103 AC1-3 | Verification: `bobp make test ARGS="test_theme_contrast.py"`, `bobp make test-browser`, `bobp make lint`*)
- [ ] **Task 4.2:** UAT: the browser suite run five times: time and failures each; the old flake case (`steampunk/dark .stage-lamp`) passes every time; a bad declared pair is caught in Python. **L2**. (*Owner: Trin | Trace: UND-103 AC2, AC4 | Verification: UAT verdict and the five times in `agents/CHAT.md`*)
- [ ] **Task 4.3:** Security quick pass. **L1**. (*Owner: Switch | Trace: design gate | Verification: `security gate (phase 4): ...`*)
- [ ] **Task 4.4:** Code review. **L2**. (*Owner: Morpheus | Trace: STORY_ARCH_SPRINT27 UND-103 | Verification: result in `agents/CHAT.md`*)

### Phase 5: The gate fails fast and says what each level is for (UND-104, 2 pts)
*Phase goal: cheap checks first; the strategy and the measured times recorded.*
- [ ] **Task 5.1:** `check: lint secrets test` in the Makefile (Tank), `docs/TEST_STRATEGY.md` with the pyramid, its budgets and the rule "each end-to-end test says why it cannot be lower", `docs/SDLC.md` with the order and measured times. One timing run of both suites with the baseline's command. **L1**. (*Owner: Tank | Trace: UND-104 AC1-3 | Verification: a deliberate lint error fails `bobp make check` in seconds (then removed); the timing run's totals against the targets*)
- [ ] **Task 5.2:** Code review of the whole sprint against the targets. **L1**. (*Owner: Morpheus | Trace: STORY_ARCH_SPRINT27 | Verification: result in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make check` once, and `docs/SDLC.md` "Last verified" updated*)
- [ ] **Task C.2:** Document grooming, ADR-0060 (the fragment harness and the pyramid budgets), lessons. (*Owner: Oracle | Trace: N/A — closeout | Verification: ADR in `docs/DECISIONS.md`; groom noted in `agents/CHAT.md`*)
- [ ] **Task C.3:** End-to-end user testing: the household on the fixtures and the console still behave as before; the time targets met or the miss reported. (*Owner: Smith | Trace: UND-101..104 | Verification: Smith acceptance verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task C.4:** Sprint retrospective and backlog grooming. (*Owner: Mouse | Trace: N/A — closeout | Verification: retros in `docs/sprints/RETRO_SPRINT27.md`, posted in `agents/CHAT.md`*)
- [ ] **Task C.5:** Sprint launch; merge `sprint-27` into `main` and push only when the owner asks. (*Owner: Cypher | Trace: N/A — release decision | Verification: launch recorded in `agents/CHAT.md`*)
