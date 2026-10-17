# Sprint 10 Task Board: A schema for sketch.yaml (Tier 2)

*   **Goal**: `schema/sketch.schema.json` so editors complete and flag `sketch.yaml` as you type; kept in step with `check` by tests.
*   **Tier**: Tier 2 · **Points**: 3 (UND-37) · **Branch**: `sprint-10`
*   **Story + Arch**: `docs/sprints/USER_STORIES_SPRINT10.md`
*   **Status**: In progress - planned 2026-10-16

## Phase 1: The schema and its tests - UND-37 AC1, AC3-5
- [x] **Task 1.1:** `*impl` tests first (ajv: examples pass, broken ones fail with their path; lists match `check`'s); then `schema/sketch.schema.json`; export the lists. (*Owner: Neo*)
- [x] **Task 1.2:** `*uat` + review, commit `Phase 1`. (*Owner: Trin → Morpheus*)

## Phase 2: Editors find it - UND-37 AC2
- [x] **Task 2.1:** `*impl` `# yaml-language-server: $schema=` line in every example; SKETCHES "Editor help"; README. (*Owner: Neo, Oracle*)
- [x] **Task 2.2:** `*uat` + review, commit `Phase 2`. (*Owner: Trin → Morpheus*)

## Close
- [ ] Tank sdlc-check · Oracle groom (ADR-0031, changelog) · Smith test · retro · launch.
