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
    participant Trin
    Note over Mouse,Trin: 📅 2026-10-29
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
    Note over Mouse,Trin: "Phase 0 summary<br/>Smith: Smith Gate 2 HOLD<br/>Sprint 19 architecture:<br/>stories say 'understudy<br/>run' but the arch says<br/>'understudy sketch run'<br/>(old sketches still use<br/>ru…<br/>Smith: Smith Gate 2<br/>APPROVE Sprint 19<br/>architecture: command is<br/>'understudy run'<br/>(owner), cache at<br/>.understudy/cache chosen<br/>by Morpheus and noted,…<br/>Morpheus: Morpheus plan<br/>review: phases follow<br/>the architecture, Phase<br/>4 was oversized with a<br/>two-owner task, split<br/>into Phase 4 (run the<br/>machine) and…"
    Mouse->>All: "phase 1"
    Note right of Mouse: "Phase 1"
    Neo->>Morpheus: "swe handoff"
    Note right of Neo: "Phase 1 done:<br/>ruamel.yaml and<br/>jsonschema pinned, ruff<br/>covers src/sketch,<br/>.understudy/ ignored,<br/>Jev wrapper now<br/>src/jev.py and path<br/>policy s…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed:<br/>no duplicate left (git<br/>grep one definition of<br/>each), dependencies<br/>ordinary, SDLC row<br/>updated. @Neo *swe impl<br/>phase-2"
    Note over Mouse,Trin: "Phase 1 summary<br/>Neo: Phase 1 done:<br/>ruamel.yaml and<br/>jsonschema pinned, ruff<br/>covers src/sketch,<br/>.understudy/ ignored,<br/>Jev wrapper now<br/>src/jev.py and path<br/>policy s…<br/>Morpheus: Phase 1 review<br/>passed: no duplicate<br/>left (git grep one<br/>definition of each),<br/>dependencies ordinary,<br/>SDLC row updated. @Neo<br/>*swe impl phase-2"
    Mouse->>All: "phase 2"
    Note right of Mouse: "Phase 2"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl done:<br/>src/sketch (model,<br/>vocabulary, conditions,<br/>loader, check), schema/d<br/>ecision_sketch.schema.js<br/>on, coffee fixtures. 21<br/>tests…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed<br/>(UND-61 AC1-5, run-time<br/>option check follows in<br/>phase 7, no-output-on-<br/>missing-file end to end<br/>in phase 4). rubric UAT:<br/>C…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed<br/>against ADR-0042 and<br/>invariants 1, 2, 7:<br/>explicit conditions,<br/>YAML 1.2, JSON Schema<br/>for shape plus Python<br/>for names,…"
    Note over Mouse,Trin: "Phase 2 summary<br/>Neo: Phase 2 impl done:<br/>src/sketch (model,<br/>vocabulary, conditions,<br/>loader, check), schema/d<br/>ecision_sketch.schema.js<br/>on, coffee fixtures. 21<br/>tests…<br/>Trin: UAT phase 2 passed<br/>(UND-61 AC1-5, run-time<br/>option check follows in<br/>phase 7, no-output-on-<br/>missing-file end to end<br/>in phase 4). rubric UAT:<br/>C…<br/>Morpheus: Phase 2 review<br/>passed against ADR-0042<br/>and invariants 1, 2, 7:<br/>explicit conditions,<br/>YAML 1.2, JSON Schema<br/>for shape plus Python<br/>for names,…"
    Mouse->>All: "phase 3"
    Note right of Mouse: "Phase 3"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 3 impl done:<br/>conditions (all<br/>operators, slices,<br/>and/or/not), decide<br/>trees and weights, blend<br/>per dimension, forbid<br/>with fail/skip/fal…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed<br/>(UND-63 AC1-5, 64-case<br/>grid proves no caffeine<br/>for under-18). rubric<br/>UAT: COVER=A STEPS=A<br/>FAIL=S DATA=A EVID=A.<br/>@Morpheu…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 3 review passed<br/>against ADR-0041/0044<br/>and invariants 3-5: one<br/>blend rule, forbid wins,<br/>weights sum checked.<br/>Design note recorded:<br/>ble…"
    Note over Mouse,Trin: "Phase 3 summary<br/>Neo: Phase 3 impl done:<br/>conditions (all<br/>operators, slices,<br/>and/or/not), decide<br/>trees and weights, blend<br/>per dimension, forbid<br/>with fail/skip/fal…<br/>Trin: UAT phase 3 passed<br/>(UND-63 AC1-5, 64-case<br/>grid proves no caffeine<br/>for under-18). rubric<br/>UAT: COVER=A STEPS=A<br/>FAIL=S DATA=A EVID=A.<br/>@Morpheu…<br/>Morpheus: Phase 3 review<br/>passed against<br/>ADR-0041/0044 and<br/>invariants 3-5: one<br/>blend rule, forbid wins,<br/>weights sum checked.<br/>Design note recorded:<br/>ble…"
    Mouse->>All: "phase 4"
    Note right of Mouse: "Phase 4"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 4 impl done:<br/>machine.py, run.py<br/>(folder, run.json,<br/>events.jsonl, outputs<br/>last), cli.py<br/>(run/check, exit 0/1/2),<br/>the ETL and sketches…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 4 passed<br/>(UND-62 AC1-4, UND-60<br/>AC1-4). rubric UAT:<br/>COVER=A STEPS=A FAIL=S<br/>DATA=A EVID=A. @Morpheus<br/>*lead review phase-4"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 4 review passed<br/>against ADR-0040 and<br/>invariants 1, 9, 10: one<br/>shared runner (a<br/>duplicate removed, not<br/>added), outputs<br/>published last,…"
    Note over Mouse,Trin: "Phase 4 summary<br/>Neo: Phase 4 impl done:<br/>machine.py, run.py<br/>(folder, run.json,<br/>events.jsonl, outputs<br/>last), cli.py<br/>(run/check, exit 0/1/2),<br/>the ETL and sketches…<br/>Trin: UAT phase 4 passed<br/>(UND-62 AC1-4, UND-60<br/>AC1-4). rubric UAT:<br/>COVER=A STEPS=A FAIL=S<br/>DATA=A EVID=A. @Morpheus<br/>*lead review phase-4<br/>Morpheus: Phase 4 review<br/>passed against ADR-0040<br/>and invariants 1, 9, 10:<br/>one shared runner (a<br/>duplicate removed, not<br/>added), outputs<br/>published last,…"
    Note over Mouse,Trin: 📅 2026-10-30
    Mouse->>All: "phase 5"
    Note right of Mouse: "Phase 5"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 5 impl done:<br/>src/cli.mjs is a<br/>launcher (run, check,<br/>etl via one Python<br/>spawner), old commands<br/>say they are being<br/>rebuilt, the old Nod…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 5 passed<br/>(UND-60 AC1, AC2, AC8).<br/>rubric UAT: COVER=A<br/>STEPS=A FAIL=A DATA=A<br/>EVID=A. @Morpheus *lead<br/>review phase-5"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 5 review passed<br/>against ADR-0045 and the<br/>purge list: Node<br/>run/check and the whole<br/>old player are gone (not<br/>just run/check: nothing<br/>el…"
    Note over Mouse,Trin: "Phase 5 summary<br/>Trin: UAT phase 5 passed<br/>(UND-60 AC1, AC2, AC8).<br/>rubric UAT: COVER=A<br/>STEPS=A FAIL=A DATA=A<br/>EVID=A. @Morpheus *lead<br/>review phase-5<br/>Morpheus: Phase 5 review<br/>passed against ADR-0045<br/>and the purge list: Node<br/>run/check and the whole<br/>old player are gone (not<br/>just run/check: nothing<br/>el…"
```
