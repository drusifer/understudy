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
    participant Tank
    Note over Mouse,Tank: 📅 2026-10-29
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
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Sprint 19 stories<br/>drafted: docs/sprints/US<br/>ER_STORIES_SPRINT19.md<br/>(UND-60..67, 28 pts,<br/>coffee PoC, file<br/>sources, CLI only, one<br/>live Jev judg…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "Domain model written:<br/>docs/DOMAIN.md (Sketch<br/>context: glossary with<br/>anti-patterns, ER, 10<br/>sketch invariants + run<br/>invariants, run<br/>lifecycle…"
    Tank->>Smith: "devops handoff"
    Note right of Tank: "Tank feasibility: the<br/>PoC needs no new<br/>language, package<br/>manager or dependency<br/>(python-statemachine,<br/>duckdb, typesafe-sdk,<br/>mcp already lock…"
    Smith->>Cypher: "user approve"
    Note right of Smith: "Smith Gate 2: epic and<br/>domain model approved.<br/>rubric DOMAIN: LANG=S<br/>BOUND=A INVAR=S STATE=A<br/>EVENT=A. rubric<br/>LOOP_EPIC: FRAME=A<br/>APPET=A BOUN…"
```
