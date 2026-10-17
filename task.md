# Sprint 13 Task Board: Questions that know the inputs (Tier 2)

*   **Goal**: every Jev question sees the run's inputs; the evening's questions use them.
*   **Tier**: Tier 2 · **Points**: 3 (UND-40) · **Branch**: `sprint-13` (from `sprint-12`)
*   **Story + Arch**: `docs/sprints/USER_STORIES_SPRINT13.md`
*   **Status**: Complete - launched 2026-10-17; merge to main awaiting owner

## Phase 1: Inputs in every request; pick.with gone; check names - UND-40 AC1-3
- [x] **Task 1.1:** `*impl` `services.inputs` into every request's state; drop `pick.with`/`told`; check `inputs.<name>` in prose. TDD. (*Owner: Neo*)
- [x] **Task 1.2:** `*uat` + review. (*Owner: Trin → Morpheus*)

## Phase 2: The evening's questions; docs and schema - UND-40 AC4-5
- [x] **Task 2.1:** `*impl` rewrite the evening's `next`/`audience`/`pick` wording; schema; SKETCHES. (*Owner: Neo, Oracle*)
- [x] **Task 2.2:** `*uat` + review; committed with phase 1 (the evening used `pick.with`, so the two could not pass apart). (*Owner: Trin → Morpheus*)

## Close
- [x] Tank sdlc-check · Oracle groom (ADR-0034, changelog) · Smith test · retro · launch.
