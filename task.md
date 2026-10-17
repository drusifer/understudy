# Sprint 9 Task Board: Themes (Tier 2)

*   **Goal**: a THEME switch on the dashboard - steampunk (default), professional, and a starship look like the Enterprise-D's screens.
*   **Tier**: Tier 2 · **Points**: 5 (UND-36) · **Branch**: `sprint-9`
*   **Story + Arch**: `docs/sprints/USER_STORIES_SPRINT9.md`
*   **Status**: Complete - launched 2026-10-16; merge to main awaiting owner

## Phase 1: The switch, and the professional theme - UND-36 AC1-3, AC5-6
- [x] **Task 1.1:** `*impl` script colours to CSS vars; `themeOf` + header switch (URL, localStorage, default); redraw on change. TDD. (*Owner: Neo*)
- [x] **Task 1.2:** `*impl` `theme-professional.css`; browser test (switch, reload, `?theme=`, Play, fits 1600x960). (*Owner: Neo*)
- [x] **Task 1.3:** `*uat` + review, commit `Phase 1`. (*Owner: Trin → Morpheus*)

## Phase 2: The starship theme - UND-36 AC4-6
- [x] **Task 2.1:** `*impl` `@fontsource/antonio`; `theme-starship.css`; browser test covers it. (*Owner: Neo*)
- [x] **Task 2.2:** USER_GUIDE + DASHBOARD sections, screenshots. (*Owner: Oracle*)
- [x] **Task 2.3:** `*uat` + review, commit `Phase 2`. (*Owner: Trin → Morpheus*)

## Close
- [x] Tank sdlc-check · Oracle groom (ADR-0029, changelog) · Smith test · retro · launch.
