# Sprint 7 Story + Architecture (Tier 2): How many tickets

*   **Total Points**: 3 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-7`
*   **Source**: owner, 2026-10-16: "lets change the seats together toggle into a number of tickets
    selector" - a **brass stepper**; weights stay analog faders; the stepper is a control kind other
    sketches can use for whole-number inputs. Recorded in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gate 1 (2026-10-16)

## STORY-UND-34: Choose how many tickets
**Points:** 3

**As the** owner,
**I want** to set how many tickets to buy with a brass stepper,
**so that** the understudy books that many seats, all together, and the "together" rule follows the
party size.

### Acceptance Criteria
1. A new input kind, `tickets: { count: [1, 4], default: 2 }`: a whole number in a range.
   `--input tickets=3` sets it; `--input tickets=9` or `tickets=2.5` refuses the run
   (`understudy: input "tickets" must be a whole number from 1 to 4, got 9`).
2. A sketch can use an input where it lists a value or a gate bound, written `{ input: tickets }`:
   `values: { boxoffice/pick_seats: { count: { input: tickets } } }` offers exactly that count;
   `together: { at_least: { input: tickets } }` needs that many free seats in a row.
   `check` refuses `{ input: x }` naming an input the sketch does not declare, or a choice/switch
   where a number is needed.
3. The evening example has `tickets` (default 2): run with `--input tickets=3`, it holds three
   side-by-side seats; the printed ticket names three seats.
4. On the dashboard a `count` input is a brass stepper: − and + buttons either side of a big Nixie
   number, stopping at the range's ends; reachable by keyboard; Play passes its value.
5. Weights stay continuous faders; nothing else changes for sketches without `count` inputs.

## Architecture (Morpheus)

- `src/inputs.mjs`: kind `count` (two integers, low < high; default and values whole numbers).
- **Input references** `{ input: <name> }` (ADR-0027): resolved at run time from the run's inputs -
  in `values:` (the list becomes `[value]`) by the MCP app, and in a gate's `at_least`/`at_most` by
  `engine.gate` (`given.inputs`). `check` validates names and kinds (`count`/`weight` for numbers).
- `src/dashboard/rack.mjs`: a `count` control `{ kind: 'count', range, default }`;
  `page.mjs`/`page.css`: the stepper.
- Docs: SKETCHES (count inputs, `{ input: }`), USER_GUIDE (the stepper).
- No new dependency or mechanism.

## Out of Scope
- Steps on weight faders; a stepper for anything but `count` inputs.
- Input references anywhere but `values:` lists and gate bounds.

rubric STORIES: OUT=S TEST=S FAIL=A SCOPE=A SIZE=S DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=S
