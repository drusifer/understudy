# Sprint 13 Story + Architecture (Tier 2): Questions that know the inputs

*   **Total Points**: 3 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-13` (cut from `sprint-12`; sprints 10-12 await merge)
*   **Source**: owner, 2026-10-17: "we should be using the parameters to fill in template values
    in the yaml rules ... maybe we just need to update the jev questions?"; every question sees all
    the inputs ("yes see all"). Recorded in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gates 1 and 2 (2026-10-17)

## STORY-UND-40: Jev's questions use the person's settings
**Points:** 3

**As the** owner,
**I want** every Jev question to see the run's inputs and name them in its wording
(`` `inputs.tickets` ``, `` `inputs.mood` ``),
**so that** what Jev is asked follows the controls - three tickets means "hold three seats",
evenings off means "any time today" - instead of fixed wording that can contradict them.

### Acceptance Criteria
1. In a sketch with `inputs:`, every Jev request - the move choice, its argument choices, a noul
   judge, the score questions and the final pick - carries the run's inputs as `inputs` in its
   state. A sketch with no inputs sends no `inputs`.
2. `pick.with` is gone: the pick sees all the inputs like every other question. `check` refuses
   `with:` under `pick:` (not a pick field) - no old form is kept.
3. `check` refuses a question (or `pick.instructions`) whose prose names `` `inputs.<name>` `` for
   an input the sketch does not declare, naming the question and the nearest declared input.
4. The evening's questions follow its controls: `next` says how many seats to hold from
   `inputs.tickets`, its time of day from `inputs.evenings`, and its mood from `inputs.mood`; the
   pick no longer says "a friend" or "tonight" as fixed words. A run with `--input tickets=3`
   asks Jev with `inputs.tickets` 3 in the state.
5. Docs (SKETCHES, MCP_GUIDE, WALKTHROUGH) and the schema no longer mention `pick.with`; SKETCHES
   says every question sees `inputs`.

## Architecture (Morpheus)

- **Inputs in the state, in one place** (ADR-0034): the run puts the resolved inputs on
  `services.inputs`; the library adds them to the state of every request it makes (`play`,
  `fillArguments`, the `judge` actor); the MCP app adds them to its score request. The `told`
  plumbing for `pick.with` is removed.
- **check**: backticked `inputs.<name>` paths in question prose and `pick.instructions` must name a
  declared input (the existing no-literals scan already walks the prose).
- Examples: the evening's questions rewritten; other examples have no inputs and are unchanged.
- Tests: library/app requests carry `inputs`; `check` refusals; the evening run with
  `tickets=3` sends it.

## Out of Scope
- Templating outside question prose (gates and values already take `{ input: }`).
- A `genre` input for the evening (its horror gate stays fixed).

rubric STORIES: OUT=S TEST=S FAIL=A SCOPE=A SIZE=A DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=A
