# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Oracle
    Note over User,Oracle: 📅 2026-10-15
    User->>All: "decide"
    Note right of User: "Owner agrees: Jev<br/>chooses argument values,<br/>never writes them -<br/>understudy is<br/>constrained automation<br/>by design. Asks for a<br/>good example doc…"
    Oracle->>All: "done"
    Note right of Oracle: "Added docs/MCP_GUIDE.md<br/>(owner request):<br/>existing .mcp.json -><br/>finished run, via as the<br/>worked example, linked<br/>from README, USER_GUIDE,<br/>SKE…"
    User->>All: "request"
    Note right of User: "push main"
```
