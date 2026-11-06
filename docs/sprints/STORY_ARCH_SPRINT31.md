# Sprint 31: A big play, folded to its flow (Tier 2: story and architecture in one)

* **Branch**: `sprint-31` (cut from `main` 49f5408). **Source**: owner, 2026-11-06 ("yes" to the household diagram next; backlog "Big plays"). **Size**: about 4 points. One story, one phase.
* **Mechanism approval**: none (no new dependency, route or make target; one new query parameter).
* **Owner rules**: no back-compat, Edit/Write only, American spelling.

## Goal

The household play is 152 nodes and a very tall picture. A play of more than 40 nodes is drawn as its **flow**: the stage's files and the flow beats, with the beats that wait to be read left out and their reads passed through. A button shows everything and back.

## Assumptions made for the owner

* **"Flow" means the files plus the beats that have `to:`, `transitions:` or `final`** (what the scene does in order). The waiting beats (about 120 in household) are the computed pieces; they are what makes it tall.
* **A flow beat is shown reading the files and flow beats its waiting beats read** (one arrow each), so "what feeds what" still reads.
* **The server decides the default** (`auto`: flow above 40 nodes, everything below); the person's button choice is kept for the page's life and sent as `view=flow|all`.

## UND-117: A big play folded to its flow
**Points:** 4 · **Owner:** Neo

**As** the owner reading a big play,
**I want** the diagram to show its flow by default and everything on request,
**so that** I can read it without scrolling through 150 boxes.

### Acceptance Criteria
1. `fold(plan, view)` (`src/play/plan.py`) gives `all` (the plan), `flow` (files and flow beats, reads passed through waiting beats, no arrow to a missing node) or `auto` (flow above 40 nodes); it says `view`, `hidden` (waiting beats) and `total` (nodes); an unknown view is refused.
2. `GET /api/plan?play=&view=`, `GET /api/runs/<id>?view=` and `/replay?at=&view=` take the view (`auto` when absent; anything else is 400); the run and plan drawings carry `view`, `hidden`, `total`.
3. Household's default drawing has 31 nodes (not 152) and is clean (no arrow through a box); a play of 40 nodes or fewer is drawn whole as before.
4. A button in the diagram panel reads `SHOW ALL <total> NODES` or `SHOW ONLY THE FLOW`, is hidden when nothing is folded, and works for a plan, a live or finished run and a replay.

## Architecture

`fold` is pure and shared: `plan_layout(found, view)` and `overlay(..., view)` lay out what it returns, so the run's lit beat, step view and hold choice work in both views (the lit and held beats are flow beats). The page keeps `state.diagramView` (unset = the server's choice), adds it through one helper (`runUrl`) to every run request and to the plan request, and the button re-fetches. No change to the run log or the plan carried in `run_started`. **Security:** one new query value, checked against a fixed list; quick pass.

## Out of Scope

Folding by beat neighbors, a search box, saving the choice between page loads.
