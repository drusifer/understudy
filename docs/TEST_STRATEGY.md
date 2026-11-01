# Quality & UAT Strategy: understudy

*   **Lead SDET / QA Guardian**: Trin
*   **Status**: Active
*   **Last Updated**: 2026-11-01
*   **Target Environments**: `Local developer machine (a Raspberry Pi, CPython 3.12.15 in .venv)`; there is no CI

---

## 1. Quality Vision & Testing Principles

understudy makes decisions about the owner's money and time, so its first quality promise is that a run is **reproducible** and that nothing a model says becomes a value without passing the owner's list. Tests exist to keep those promises cheap to check on every change.

* **Shift-Left Quality:** a sketch's mistakes are caught by `check` before a run (DOMAIN invariant 1); stories carry acceptance criteria a tester can answer yes or no (STORIES check) before code is written.
* **Deterministic feedback:** the suite needs no key and no network; Jev is a scripted double (`tests/python/jev_double.py`) or a committed capture replayed with `--replay`. The gate is `bobp make check`.
* **External dependencies:** the real Jev service is called only in one live UAT run with the owner's go-ahead (Sprint 19 rule), never by `bobp make test`. The double's assumptions (typed probabilities over listed options, asked again once on an off-list answer) are checked against one committed real capture (`tests/fixtures/coffee/replay/`, a real cold-forecast judgement) that replays in the suite.
* **Simplicity & Maintainability:** tests exercise stages as functions and sketches as files; no mocking framework is used. Test data are invented fixtures (`tests/fixtures/`); the owner's real exports are never committed or printed.
* **Look at it, not only its tests:** for anything drawn (the console), UAT includes opening it in a real browser; unit tests cannot see layout or overlap (lesson 2026-10-15).

---

## 2. Testing Levels & The Quality Pyramid

| Level | Purpose and risk covered | Where it runs / command | When it is appropriate |
|---|---|---|---|
| Unit | Rules, conditions, blend, dates, stage functions, console routing and gauges: fast isolated cases and edges | `bobp make test-py ARGS="test_<area>*.py"` (24 files, 233 tests, about 13 s) | Every change; pick the narrowest file pattern first |
| Integration | A whole sketch end to end on invented fixtures with a Jev double: coffee, evening, seating, household (naming, fold), CLI exit codes, the console server over real sockets | `bobp make test-py` (same suite: `test_sketch_run`, `test_sketch_coffee`, `test_sketch_evening`, `test_household*`, `test_dashboard`) | When a boundary changes: stages, sources, run folder, CLI |
| Replay acceptance | Byte-identical output from a captured real Jev read | `bobp make run ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay"` | After changes to capture, blend or sinks |
| End-to-end / UAT | The owner's real journey: the household run on real exports (live, once), the console in a real browser (rack, live follow, failed run, themes, 390 px), the CLI's wrong-input messages | written in `docs/sprints/UAT_PLAN_SPRINT<N>.md`; browser steps by hand until UND-80 writes them down | Sprint close; before the owner sees a change |

Browser automation is not part of the suite (ADR-0048). A thin Python-driven browser check is proposed in Sprint 22 UND-80 and needs Tank's approval before any tool is added.

---

## 3. Ownership and Review

Authoring and review roles are defined in `agents/trin/SKILL.md`, `agents/neo/SKILL.md` and `agents/skills/impl/SKILL.md`; usability review in `agents/smith/SKILL.md`; security review in `agents/switch/SKILL.md`. Artifact owners and their checks: `agents/templates/ARTIFACTS.md`.

## 4. Automated Quality Gates

| Gate | Existing target / command | Pass condition | Required at |
|---|---|---|---|
| Tests | `bobp make test` (runs `test-py`) | exit 0, `OK`, no skipped test | every handoff to Trin; before commit; sprint close |
| Lint | `bobp make lint` (ruff over `src` and `tests/python`) | `All checks passed!` | every handoff to Trin; sprint close |
| Secrets | `bobp make secrets` (gitleaks over history and tracked changes) | `no leaks found` | every commit and push; sprint close |
| Full gate | `bobp make check` (tests, lint, secrets) | all three pass | before `bobp make push`; sprint close |
| Dependency audit | none yet | n/a | Tank to add a `security-scan` target (security review, 2026-11-01) |

## 5. Test Environment & Fixture Management

* **Isolation:** tests build their own run folders and sketches in temporary directories (`tempfile`); no test depends on another's leftovers; the console tests start a server on port 0 and stop it in cleanup.
* **Scratch & Cleanup:** temporary directories are removed in `setUp`/cleanup; runs write only under a temp `--out` or `build/`, never under `data/`.
* **Non-Destructive Execution:** tests never read `.env`, never call the network, and never touch the owner's `data/` or `.understudy/` captures; the live Jev run is a manual UAT step with the owner's go-ahead and prints counts only.
* **Private data:** real exports and live capture files are never committed, pasted or printed; fixtures are invented and small.

---

## 6. Defect Handling

Defects follow the fix loop in `agents/skills/fix/SKILL.md` (reproduce with a test first, confirm the diagnosis with the user, surgical fix, no regressions) and its Anti-Loop rule (two failed rounds go to Oracle, then the user). Usability defects (`*user bug`) are routed through Trin for triage; security findings follow `agents/templates/_template_SECURITY_FINDING.md` with Switch.

## 7. Known Gaps (as of 2026-11-01)

| Gap | Risk | Planned |
|---|---|---|
| `page.js` has no automated check | a DOM regression (live follow, tab switch, theme memory) is found only by hand | Sprint 22 UND-80 (a written check; tool approved by Tank) |
| No UAT plans for sprints 7 to 15, 20 and 21 | acceptance evidence for the console and the household is in chat and retros only | Trin writes Sprint 21's after the fact; Sprint 22 gets one up front |
| No dependency audit | a vulnerable pinned package would not be seen | Tank, `security-scan` target |
| Live Jev behavior is verified once per sprint at most | a change in the real service's answers would show only in a live run | owner's go-ahead for a live UAT run at sprint close |
| The household's category quality has no accepted baseline | "better" cannot be measured (1,706 of 5,074 in review) | owner to set a target (PRD G4) |
