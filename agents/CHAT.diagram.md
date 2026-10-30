# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `bobp chat-diagram` (or it regenerates automatically on every `bobp chat`).

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
    participant All
    Note over Mouse,All: 📅 2026-10-29
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
    Smith->>Cypher: "user reject"
    Note right of Smith: "Smith Gate 1 REJECT<br/>Sprint 19 stories: stale<br/>goal, UND-62 guard<br/>untestable (coffee<br/>machine has no branch),<br/>UND-65 expose has no<br/>subject, UN…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories revised (status<br/>line in<br/>USER_STORIES_SPRINT19.md<br/>lists each fix), only<br/>the choice style of Jev<br/>is in scope. One owner<br/>decision pend…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "Smith Gate 1 re-review<br/>Sprint 19 stories: all<br/>six findings fixed,<br/>capture/replay (UND-60<br/>AC5-7) is testable,<br/>owner confirmed stale<br/>replay w…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture drafted: do<br/>cs/sprints/ARCH_SPRINT19<br/>.md (src/sketch package,<br/>12 components,<br/>capture/replay,<br/>ADR-0040..0045, no new<br/>mechanism, r…"
    Smith->>Cypher: "user hold"
    Note right of Smith: "Smith Gate 2 HOLD Sprint<br/>19 architecture: stories<br/>say 'understudy run' but<br/>the arch says<br/>'understudy sketch run'<br/>(old sketches still use<br/>ru…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "Smith Gate 2 APPROVE<br/>Sprint 19 architecture:<br/>command is 'understudy<br/>run' (owner), cache at<br/>.understudy/cache chosen<br/>by Morpheus and noted,…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint 19 planned:<br/>task.md, 6 phases<br/>(setup/shared,<br/>load+check,<br/>decide/blend,<br/>run+command,<br/>sources+replay, coffee<br/>end to end), each<br/>Neo/Tri…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Morpheus plan review:<br/>phases follow the<br/>architecture, Phase 4<br/>was oversized with a<br/>two-owner task, split<br/>into Phase 4 (run the<br/>machine) and…"
    Note over Mouse,All: "Phase 0 summary<br/>Smith: Smith Gate 2 HOLD<br/>Sprint 19 architecture:<br/>stories say 'understudy<br/>run' but the arch says<br/>'understudy sketch run'<br/>(old sketches still use<br/>ru…<br/>Smith: Smith Gate 2<br/>APPROVE Sprint 19<br/>architecture: command is<br/>'understudy run'<br/>(owner), cache at<br/>.understudy/cache chosen<br/>by Morpheus and noted,…<br/>Morpheus: Morpheus plan<br/>review: phases follow<br/>the architecture, Phase<br/>4 was oversized with a<br/>two-owner task, split<br/>into Phase 4 (run the<br/>machine) and…"
    Mouse->>All: "phase 1"
    Note right of Mouse: "Phase 1"
    Neo->>Morpheus: "swe handoff"
    Note right of Neo: "Phase 1 done:<br/>ruamel.yaml and<br/>jsonschema pinned, ruff<br/>covers src/sketch,<br/>.understudy/ ignored,<br/>Jev wrapper now<br/>src/jev.py and path<br/>policy s…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed:<br/>no duplicate left (git<br/>grep one definition of<br/>each), dependencies<br/>ordinary, SDLC row<br/>updated. @Neo *swe impl<br/>phase-2"
    Note over Mouse,All: "Phase 1 summary<br/>Neo: Phase 1 done:<br/>ruamel.yaml and<br/>jsonschema pinned, ruff<br/>covers src/sketch,<br/>.understudy/ ignored,<br/>Jev wrapper now<br/>src/jev.py and path<br/>policy s…<br/>Morpheus: Phase 1 review<br/>passed: no duplicate<br/>left (git grep one<br/>definition of each),<br/>dependencies ordinary,<br/>SDLC row updated. @Neo<br/>*swe impl phase-2"
```
