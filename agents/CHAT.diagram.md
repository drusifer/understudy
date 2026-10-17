# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Oracle
    participant All
    participant User
    Note over Oracle,User: 📅 2026-10-16
    Oracle->>All: "checkpoint"
    Note right of Oracle: "Checkpoint: Cypher +<br/>Oracle state saved<br/>(between sprints, sprint<br/>9 merged). Ready for<br/>context clear. Resume<br/>with /init."
    User->>All: "request"
    Note right of User: "fill the doc gaps,<br/>slider is the percentage<br/>of the weighting applied<br/>(5 of 10 = 1.5)"
    Oracle->>All: "done"
    Note right of Oracle: "Weight inputs are now a<br/>share of the full<br/>weighting 3 (ADR-0030,<br/>owner), SKETCHES.md<br/>gains an input-kinds<br/>table, the weight rule,<br/>when:/{ i…"
```
