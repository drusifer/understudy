# Sprint 8 Task Board: Behind the printer (Tier 2)

*   **Goal**: take the printer off the console to edit the sketch's YAML in the bay behind it, with a cheat-sheet sticker; saves as you type and the state tube redraws.
*   **Tier**: Tier 2 · **Points**: 3 (UND-35) · **Branch**: `sprint-8`
*   **Story + Arch**: `docs/sprints/USER_STORIES_SPRINT8.md`
*   **Status**: In progress - planned 2026-10-16

## Phase 1: Whole-file writes - UND-35 AC2-4 (server side)
- [x] **Task 1.1:** `*impl` `settings.write({ sketch, text })` (check on a copy, factory copy, 422 with the problem); server `write` POST (409 while a run plays) and GET of a sketch's text. TDD. (*Owner: Neo*)
- [x] **Task 1.2:** `*uat` + review, commit `Phase 1`. (*Owner: Trin → Morpheus*)

## Phase 2: The bay and the sticker - UND-35 AC1-7 (page)
- [ ] **Task 2.1:** `*impl` REMOVE / REFIT PRINTER, the bay textarea (debounced, serialised writes; problem line; read-only while running; reload on rack switch, POWER, drawer save), the sticker; browser test; USER_GUIDE + DASHBOARD note. (*Owner: Neo, Oracle*)
- [ ] **Task 2.2:** `*uat` + review, commit `Phase 2`. (*Owner: Trin → Morpheus*)

## Close
- [ ] Tank sdlc-check · Oracle groom (ADR-0028, changelog) · Smith test · retro · launch.
