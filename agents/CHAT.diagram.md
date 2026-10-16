# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Oracle
    participant Tank
    participant Cypher
    Note over User,Cypher: 📅 2026-10-15
    User->>All: "decide"
    Note right of User: "Owner agrees: Jev<br/>chooses argument values,<br/>never writes them -<br/>understudy is<br/>constrained automation<br/>by design. Asks for a<br/>good example doc…"
    Oracle->>All: "done"
    Note right of Oracle: "Added docs/MCP_GUIDE.md<br/>(owner request):<br/>existing .mcp.json -><br/>finished run, via as the<br/>worked example, linked<br/>from README, USER_GUIDE,<br/>SKE…"
    User->>All: "request"
    Note right of User: "push main"
    Tank->>All: "done"
    Note right of Tank: "Sprint 3 merged to main<br/>(1dc029f, --no-ff) and<br/>pushed via bobp make<br/>push (gate green, no<br/>leaks). origin/main up<br/>to date. Branch sprint-3<br/>fu…"
    User->>All: "request"
    Note right of User: "/sprint 4 UX - see what<br/>the understudy is doing:<br/>a UX that displays the<br/>state machine diagram<br/>and shows state changes<br/>and Jev decisions in…"
    Cypher->>All: "shaping"
    Note right of Cypher: "Shaping sprint 4 with<br/>the owner before writing<br/>stories, asking one<br/>question at a time<br/>(where the UX lives<br/>first)."
    User->>All: "decide"
    Note right of User: "Owner decided: the live<br/>view is a browser page -<br/>run --watch serves a<br/>local page (127.0.0.1)<br/>drawing the statechart,<br/>highlighting the curre…"
    User->>All: "decide"
    Note right of User: "Owner decided: live +<br/>replay - the same page<br/>follows run --watch live<br/>and replays a finished<br/>run from its log<br/>(understudy watch<br/><log.jsonl>…"
    User->>All: "decide"
    Note right of User: "Owner decided: each<br/>decision shows options<br/>offered, the pick,<br/>confidence, chosen<br/>arguments and the app's<br/>answer - no full<br/>probability distr…"
    User->>All: "decide"
    Note right of User: "Owner decided: pause and<br/>step live from the page<br/>(plus play/pause/step in<br/>replay). Shaping<br/>questions done,<br/>assumptions listed in<br/>BACKLOG Sp…"
    User->>All: "request"
    Note right of User: "/sprint 4 go"
```
