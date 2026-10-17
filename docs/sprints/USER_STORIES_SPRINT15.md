# Sprint 15 Story + Architecture (Tier 2): Flair and real gauges

*   **Total Points**: 3 (Tier 2) · **Branch**: `sprint-15` (from `sprint-14`)
*   **Source**: owner, 2026-10-17: per-theme flair - steampunk leather, brass screws, flickering
    vacuum-tube bulbs, backlit needle meters; starship ship readouts and moving power bars;
    professional familiar metric displays - "yes real metrics in the gauges".
*   **Status**: Done (launched 2026-10-17)

## STORY-UND-42: Instruments that tell me how the run is going
**As the** owner, **I want** each theme's instruments to show real readings of the run,
**so that** a glance tells me how far it has gone, how sure Jev is and whether it is stuck.

### Acceptance Criteria
1. Five gauges: steps taken of the step limit; Jev's confidence in its last choice; values left on
   the shortlist of those considered; Jev scores asked · reused; time since the last move of the
   idle limit (first-move limit before the first move).
2. Steampunk: backlit needle meters, leather panels, brass screws, ornate edges, flickering bulbs
   (still under reduced motion). Starship: power-bar readouts moving only within a small band round
   the reading. Professional: metric cards.
3. Every theme and mode fits 1600x960 and a phone.

## Architecture
- Start line `limits: { steps, first_move_ms, stall_ms }`; `metersAfter`/`gaugesOf` (pure) in
  `page.mjs`; one gauge markup, styled per theme. ADR-0036.
- Tests: unit (readings), browser (2 steps read 2/30, a confidence figure), run start-line keys.
