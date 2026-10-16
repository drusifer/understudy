# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Tank
    participant Cypher
    Note over User,Cypher: 📅 2026-10-15
    User->>All: "request"
    Note right of User: "merge and push"
    Tank->>All: "done"
    Note right of Tank: "Sprint 2 merged to main<br/>(3bd6bf3) and pushed via<br/>bobp make push (b020fc5,<br/>gate green, no leaks).<br/>origin/main up to date."
    User->>All: "decide"
    Note right of User: "Owner, sprint 3<br/>direction: not an MCP<br/>server - an MCP<br/>*target*: understudy as<br/>MCP client playing any<br/>MCP server ('sketches').<br/>Off-the-shelf…"
    User->>All: "decide"
    Note right of User: "Owner agreed: MCP config<br/>uses the de facto<br/>mcpServers shape (Claude<br/>Desktop/Code .mcp.json).<br/>Supported two ways:<br/>reference a config file<br/>+…"
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Checkpoint saved in<br/>agents/cypher/state.md<br/>(sprint 3 shaping: MCP<br/>target, SDK client,<br/>mcpServers config, one<br/>sketch.yaml, 3 open<br/>owner ques…"
    User->>All: "request"
    Note right of User: "/init"
    Cypher->>All: "resume"
    Note right of Cypher: "Resuming sprint 3<br/>shaping from last<br/>session: re-asking the<br/>owner, one at a time,<br/>whether sketch.yaml<br/>becomes the only format."
    User->>All: "decide"
    Note right of User: "Owner decided:<br/>sketch.yaml is the ONLY<br/>sketch format. Sprint 3<br/>converts examples/cli,<br/>web, http and removes<br/>the old part +<br/>adapter.mjs layo…"
    User->>All: "decide"
    Note right of User: "Owner decided: MCP tool<br/>arguments - a sketch may<br/>list fixed calls (tool +<br/>args) as moves, tools<br/>not listed, or with open<br/>args, get argument…"
    User->>All: "decide"
    Note right of User: "Owner decided: remote<br/>MCP auth is token<br/>headers only (headers<br/>with ${VAR} from env).<br/>OAuth goes to Later. All<br/>sprint 3 shaping<br/>questions an…"
    Cypher->>All: "done"
    Note right of Cypher: "Sprint 3 shaping<br/>complete: MCP target,<br/>SDK client, mcpServers<br/>config (file ref or<br/>inline), sketch.yaml as<br/>the only format, sketch<br/>calls + J…"
    User->>All: "request"
    Note right of User: "/sprint 3 go"
```
