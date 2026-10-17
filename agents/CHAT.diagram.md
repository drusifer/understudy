# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Oracle
    participant All
    Note over Oracle,All: 📅 2026-10-16
    Oracle->>All: "checkpoint"
    Note right of Oracle: "Checkpoint: Cypher +<br/>Oracle state saved<br/>(between sprints, sprint<br/>9 merged). Ready for<br/>context clear. Resume<br/>with /init."
```
