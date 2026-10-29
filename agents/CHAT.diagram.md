# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Mouse
    participant Cypher
    participant Smith
    participant Neo
    participant Morpheus
    Note over Mouse,Morpheus: 📅 2026-10-29
    Mouse->>Cypher: "phase 0"
    Note right of Mouse: "Sprint 19 planning<br/>started on branch<br/>sprint-19 (from main<br/>357c85b, no worktree).<br/>SDLC present. Scope<br/>pending the owner.<br/>@Cypher *pm plan sp…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Epic drafted: docs/sprin<br/>ts/EPIC_PYTHON_PORT.md<br/>(problem, appetite<br/>proposal of 4 slices,<br/>no-gos, domain, 4<br/>spikes, feasibility,<br/>parity princ…"
    Smith->>Neo: "user approve"
    Note right of Smith: "Smith Gate 1: problem<br/>validated (one runtime,<br/>same behaviour, parity<br/>measured against the<br/>Node run). rubric<br/>LOOP_EPIC: FRAME=A<br/>APPET=A BOUN…"
    Neo->>Morpheus: "spike handoff"
    Note right of Neo: "Spike 1 done (partial):<br/>the turn machine ports<br/>to python-statemachine<br/>YAML (states, events,<br/>named guards), tags,<br/>description and<br/>invoke/onD…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Epic revised to the new<br/>sketch model (docs/sprin<br/>ts/EPIC_PYTHON_PORT.md,<br/>DESIGN_SKETCH_MODEL.md),<br/>slice A = coffee proof<br/>of concept = Sprint…"
```
