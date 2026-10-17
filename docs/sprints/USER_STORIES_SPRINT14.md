# Sprint 14 Story + Architecture (Tier 2): The statechart as a flow

*   **Total Points**: 3 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-14` (from `main`)
*   **Source**: owner, 2026-10-17: "is there a better way to display the state machine? its hard to
    tell what it's doing. is there a more standard visualization for our directed graph?"; "the
    other themes can use a rectangle screen". Recorded in `agents/CHAT.md`.
*   **Status**: Done (launched 2026-10-17)

## STORY-UND-41: See what the understudy is doing at a glance
**Points:** 3

**As the** owner, **I want** the statechart drawn the standard way - a layered flow -
**so that** I can follow where the run is and where it can go next.

### Acceptance Criteria
1. States are rounded boxes in layers from the initial state (marked by a dot) downwards; final
   states have a double border; no two boxes overlap.
2. Every transition is an arrow labelled with its event and guard; labels do not sit on boxes.
3. The current state is lit, the transition just taken flows, the decision edge carries the
   weights' blend - as before.
4. Steampunk keeps its round tube (a thin power ring on the rim); professional and starship draw
   on a rectangular screen. The weights' shares show as a bar under the screen.
5. All themes and modes still fit 1600x960 and a phone.

## Architecture (Morpheus)
- `src/dashboard/flow.mjs`: `flowLayout(graph, decision)` with `elkjs` (layered, DOWN, orthogonal,
  model order) on the server; `describeSketch` sends `flow`. The page draws SVG only. ADR-0035.
- `tube.mjs` keeps the ring; the circle layout is removed.
- Tests: `tests/tube.test.js` (flow placement, labels, decision edge, ring); browser tests updated.

rubric STORIES: OUT=S TEST=A FAIL=A SCOPE=A SIZE=A DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=A
