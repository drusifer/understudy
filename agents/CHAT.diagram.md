# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Tank
    Note over User,Tank: 📅 2026-10-16
    User->>All: "decide"
    Note right of User: "Owner decided: a<br/>decision waits until<br/>nothing is held back -<br/>unless a value hits an<br/>11 (a factor turned to<br/>11 scoring 100% wins<br/>outright)."
    User->>All: "decide"
    Note right of User: "Owner clarified: 11 is<br/>how the dashboard shows<br/>a factor at 1.0. Rule: a<br/>decision waits for every<br/>held-back value, unless<br/>a value already sc…"
    User->>All: "decide"
    Note right of User: "Owner: yes - cache<br/>previous results with<br/>the same inputs (a<br/>deciding sketch does not<br/>repeat a call already<br/>answered with the same<br/>arguments…"
    User->>All: "request"
    Note right of User: "merge and push sprint 5"
    Tank->>All: "done"
    Note right of Tank: "Sprint 5 merged to main<br/>(965bade, --no-ff) and<br/>pushed via bobp make<br/>push (gate green, no<br/>leaks). origin/main up<br/>to date."
    User->>All: "request"
    Note right of User: "/sprint 6 go"
```
