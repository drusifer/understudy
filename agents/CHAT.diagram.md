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
    participant Smith
    participant Morpheus
    participant Mouse
    participant Neo
    Note over User,Neo: 📅 2026-10-15
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
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories ready for user<br/>review: docs/sprints/USE<br/>R_STORIES_SPRINT3.md -<br/>UND-9 sketch.yaml only<br/>format (5), UND-10 local<br/>MCP (5), UND-11 remot…"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject. rubric<br/>STORIES: OUT=S TEST=W<br/>FAIL=W SCOPE=S SIZE=A<br/>DESIGN=A. TEST: UND-10<br/>AC4 'values in the last<br/>result' has no pass<br/>conditi…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories revised per<br/>Smith: UND-10 AC4 now<br/>lists the exact value<br/>sets with a<br/>list_films->pick_seats<br/>example, new AC5 covers<br/>not-offered tool…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. Stories<br/>approved. rubric<br/>STORIES: OUT=S TEST=S<br/>FAIL=S SCOPE=S SIZE=A<br/>DESIGN=A. Note for arch:<br/>UND-11 AC5 changes make<br/>test-l…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture complete: d<br/>ocs/sprints/ARCH_SPRINT3<br/>.md - sketch.mjs<br/>replaces part.mjs, mcp<br/>target (SDK Client, own<br/>stdio transport on<br/>program.…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve.<br/>Architecture approved<br/>with notes (folded in):<br/>'not offering ... yet'<br/>since results can supply<br/>values later, showing<br/>also see…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: task.md<br/>- 5 phases (sketch<br/>loader, convert<br/>examples, local MCP +<br/>fill + box office,<br/>remote MCP + Tank test-<br/>live, docs) + cl…"
    Morpheus->>Mouse: "lead reject"
    Note right of Morpheus: "Plan review FAILED.<br/>rubric PLAN: SIZE=A<br/>GATE=W VERIF=A ALIGN=A<br/>OWNER=A. GATE: Phase 1<br/>removes part.mjs while<br/>examples still use<br/>adapter.mjs…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Plan revised: loader +<br/>example conversion in<br/>one phase (Phase 1), 4<br/>phases total. @Morpheus<br/>*lead review sprint plan"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Sprint plan approved.<br/>rubric PLAN: SIZE=A<br/>GATE=A VERIF=A ALIGN=A<br/>OWNER=A. Phase 1 ready.<br/>@Neo *swe impl phase-1"
```
