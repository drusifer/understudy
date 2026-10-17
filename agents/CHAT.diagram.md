# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Tank
    participant Mouse
    participant Morpheus
    participant Neo
    participant Cypher
    participant Smith
    participant Trin
    participant Oracle
    Note over User,Oracle: 📅 2026-10-16
    User->>All: "request"
    Note right of User: "merge and push sprint 6"
    Tank->>All: "done"
    Note right of Tank: "Sprint 6 merged to main<br/>(a4c651a, --no-ff) and<br/>pushed via bobp make<br/>push (gate green, no<br/>leaks)."
    User->>All: "decide"
    Note right of User: "Owner: replace the<br/>seats-together toggle<br/>with a number-of-tickets<br/>selector - a brass<br/>stepper. Weights stay<br/>analog faders, the<br/>stepper is a…"
    Mouse->>All: "phase 1"
    Note right of Mouse: "Sprint 7 (Tier 2): docs/<br/>sprints/USER_STORIES_SPR<br/>INT7.md - UND-34 count<br/>input + { input: }<br/>references + brass<br/>stepper, 3 pts. Smith<br/>Gate 1 a…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 done (UND-34):<br/>count inputs, { input: }<br/>in values/gate bounds,<br/>evening tickets, three<br/>tickets books three<br/>seats together, 285<br/>tests…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "Sprint 7 close: SDLC<br/>unchanged (no deps),<br/>check + browser green,<br/>ADR-0027, changelog.<br/>Smith: stepper looks and<br/>steps right, stops at<br/>its en…"
    User->>All: "request"
    Note right of User: "merge and push sprint 7"
    Tank->>All: "done"
    Note right of Tank: "Sprint 7 merged to main<br/>and pushed via bobp make<br/>push."
    User->>All: "feedback"
    Note right of User: "Owner: tighten the<br/>display - state diagram<br/>front and centre,<br/>compact sliders aligned<br/>vertically on the right,<br/>printout on the left of<br/>the c…"
    User->>All: "request"
    Note right of User: "prepare for clear,<br/>commit and push"
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Checkpoint saved in<br/>agents/cypher/state.md<br/>(between sprints,<br/>dashboard layout<br/>revision on main,<br/>background dashboard<br/>noted). Ready for cont…"
    User->>All: "request"
    Note right of User: "/init"
    Cypher->>All: "resume"
    Note right of Cypher: "Resuming as Cypher:<br/>between sprints, asking<br/>owner what is next."
    User->>All: "request"
    Note right of User: "removing a panel reveals<br/>the sketch yaml, user<br/>edits it and the panel<br/>updates"
    Cypher->>All: "note"
    Note right of Cypher: "Owner: remove the<br/>printer panel to reveal<br/>the sketch YAML, tube<br/>redraws live as YAML<br/>changes, cheat-sheet<br/>sticker inside the<br/>panel."
    Cypher->>All: "update"
    Note right of Cypher: "Nit done: evening<br/>weights now [0, 10]<br/>(defaults 3/7/7/10),<br/>SKETCHES example and<br/>tests updated, check +<br/>test-browser pass.<br/>Uncommitted. Spri…"
    User->>All: "request"
    Note right of User: "yes commit and /sprint 8<br/>go"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stage 0: SDLC present,<br/>branch sprint-8 cut from<br/>main. Story+arch (Tier<br/>2) drafted: docs/sprints<br/>/USER_STORIES_SPRINT8.md<br/>. @Smith *user revie…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "Gate 1 review: AC5<br/>missed a drawer save<br/>while the bay is open,<br/>AC6 'fits' had no<br/>viewport. Revised with<br/>Cypher. *user approve.<br/>rubric STORI…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Arch in the same doc<br/>(Tier 2): settings.write<br/>+ server write/GET text,<br/>debounced, serialised<br/>saves, textarea never<br/>redrawn. ADR-0028<br/>whole-…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve.<br/>Architecture approved.<br/>rubric ARCH: BOUND=A<br/>FLOW=A FAIL=A USER=A<br/>DECS=A FEAS=S. @Mouse<br/>*sm plan sprint"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: 2 phases<br/>(server write, page bay<br/>+ sticker). @Morpheus<br/>*lead review sprint plan"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Plan approved. rubric<br/>PLAN: SIZE=S GATE=A<br/>VERIF=A ALIGN=S OWNER=A.<br/>@Neo *swe impl phase-1"
    Mouse->>All: "phase 1"
    Note right of Mouse: "Phase 1: whole-file<br/>writes (server side)"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl:<br/>settings.write, write<br/>action (409 while<br/>running), GET<br/>api/text/<name>, body<br/>cap 64 KB. Tests added,<br/>check passes. @Trin *qa<br/>u…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed: AC2<br/>write+factory+restore,<br/>AC3 refused writes<br/>nothing and names the<br/>problem without path,<br/>AC4 409 while running,<br/>290 te…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed:<br/>shared saved() keeps<br/>edit and write on one<br/>path, GET text reads<br/>only rack names. @Neo<br/>*swe impl phase-2"
    Mouse->>All: "phase 2"
    Note right of Mouse: "Phase 2: the bay and the<br/>sticker (page)"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl:<br/>REMOVE/REFIT PRINTER,<br/>the bay (debounced<br/>serialised writes,<br/>problem line, read-only<br/>while running, reload on<br/>rack/POWER/drawe…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed:<br/>AC1-3, AC6-7 in the<br/>browser test (keyboard<br/>REMOVE, sticker fits,<br/>rename shows in tube,<br/>broken text not saved).<br/>AC4-5 by…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed:<br/>redraw() shared by<br/>drawer and bay saves,<br/>textarea never redrawn<br/>by its own write, flush<br/>before Play and tab<br/>switch.…"
    Tank->>Oracle: "devops handoff"
    Note right of Tank: "SDLC check passed: clean<br/>-> check, browser 6/6,<br/>no mechanism change.<br/>@Oracle *ora groom"
    Oracle->>Smith: "ora handoff"
    Note right of Oracle: "Docs groomed: ADR-0028,<br/>CHANGELOG sprint 8,<br/>USER_GUIDE + DASHBOARD<br/>bay rows. rubric<br/>DECISION: CTX=A OPTS=A<br/>WHY=A CONS=A. @Smith<br/>*user test…"
    Smith->>All: "user approve"
    Note right of Smith: "User test passed<br/>(browser run +<br/>screenshot at 1600x960):<br/>REMOVE by keyboard,<br/>sticker whole, rename<br/>shows in tube, broken<br/>text red with one-…"
    Mouse->>Cypher: "retro"
    Note right of Mouse: "Retro. Neo: page.mjs<br/>~640 lines, split<br/>overdue. Trin: read-<br/>only-while-running and<br/>POWER reload not<br/>browser-tested.<br/>Morpheus: whole-file<br/>wri…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "*pm launch sprint-8.<br/>Behind the printer:<br/>REMOVE to edit<br/>sketch.yaml with a cheat<br/>sheet, tube redraws as<br/>you type. Retro items on<br/>BACKLOG. M…"
```
