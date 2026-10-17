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
    Note over User,Cypher: 📅 2026-10-16
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
```
