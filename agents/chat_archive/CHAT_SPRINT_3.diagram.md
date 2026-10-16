# CHAT_SPRINT_3 — Sprint Archive

## Summary

Sprint 3: owner shaped an MCP target (understudy as MCP client, SDK, mcpServers config inline or by reference, token headers) and one sketch.yaml as the only format; Cypher's stories rejected once by Smith (argument values, nothing-offerable), then approved with the architecture (ProgramTransport on program.mjs, generic MCP app, Jev chooses arguments). Plan revised once (loader + examples in one phase). Phases 1-4 passed UAT and review: sketch loader + converted examples, local MCP + box office (DEF-07: candidates from last non-error result), remote MCP + test-live (Tank), docs (SKETCHES.md, ADR-0011..0013). Close: SDLC check green, 3 lessons, Smith played a real server from .mcp.json and found DEF-09 (absolute config paths) - fixed. Launched; merge awaits owner.

---

## Planning

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

---

## Phase 1

Phase 1: sketch loader and the three examples converted (UND-9)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl complete:<br/>src/sketch.mjs replaces<br/>part.mjs, parseTurn<br/>takes the turn object,<br/>cli/run speak 'sketch',<br/>steps precedence,<br/>cli/web…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed:<br/>refusals exit 2 with<br/>sketch.yaml paths (old<br/>layout, turn typo,<br/>missing hooks, bad<br/>--steps), check line<br/>same for dir and…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed.<br/>rubric-free notes:<br/>matches ARCH §3 sketch<br/>file (keys, per-kind<br/>fields, hooks default<br/>export + library), §5<br/>messages,…"
```

---

## Phase 2

Phase 2: local MCP target, generic MCP app, argument filling, box office (UND-10)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl complete:<br/>mcpConfig (inline/ref,<br/>${VAR}),<br/>ProgramTransport on<br/>program.mjs (+stderr<br/>tail), mcp target<br/>(stdio), fill.mjs,<br/>generi…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed: live<br/>run examples/mcp 3 steps<br/>-> Ticket issued, exit<br/>0, not-offered 'yet'<br/>lines once each, unset<br/>${VAR} exit 2 naming v…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed:<br/>matches ADR-0012 (SDK<br/>Client, ProgramTransport<br/>on program.mjs) and<br/>ADR-0013 (choose-not-<br/>write, 2nd request, off-<br/>list…"
```

---

## Phase 3

Phase 3: remote MCP over HTTP with token headers (UND-11)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Tank
    participant All
    participant Trin
    participant Morpheus
    participant Neo
    Note over Tank,Neo: 📅 2026-10-15
    Tank->>All: "done"
    Note right of Tank: "Task 3.2 done (Tank,<br/>SDLC §6 mechanism -<br/>recipe edit of an<br/>existing target,<br/>approved via sprint<br/>scope): test-live serves<br/>examples/mcp/serve…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed: live<br/>mcp-remote 3 steps<br/>(pay(method=card) fixed<br/>call) exit 0, server<br/>left running, wrong<br/>token -> exit 1 'refused<br/>the c…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 3 review passed:<br/>remote path per ARCH §4<br/>(streamable HTTP +<br/>headers, retry to 10 s,<br/>HTTP error final,<br/>client-only close), URL<br/>shown f…"
```

---

## Phase 4

Phase 4: docs teach sketches and the MCP target (UND-12)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    participant Tank
    participant Oracle
    participant Smith
    participant All
    participant Cypher
    participant Mouse
    Note over Neo,Mouse: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 4 impl complete<br/>(Neo+Oracle):<br/>docs/SKETCHES.md<br/>replaces ADAPTERS.md,<br/>README, USER_GUIDE,<br/>WALKTHROUGH (new §5 MCP<br/>with real runs) on s…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 4 passed:<br/>every documented<br/>check/library/help/no-<br/>key command gives the<br/>documented line, anchors<br/>resolve, AC3 grep only<br/>hits the a…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "Phase 4 review passed:<br/>docs match the code<br/>(keys, messages,<br/>outcomes incl. refused,<br/>test-live), ADRs cite<br/>stories and the Phase 2<br/>finding.…"
    Tank->>Oracle: "devops handoff"
    Note right of Tank: "SDLC check passed:<br/>distclean -> install<br/>(lockfile unchanged) -><br/>check green, 162/162,<br/>deps match imports (+@mo<br/>delcontextprotocol/sdk,<br/>zod v…"
    Oracle->>Smith: "ora handoff"
    Note right of Oracle: "Docs groomed:<br/>UAT_PLAN_SPRINT3 written<br/>(14 negative cases,<br/>DEF-07/08 resolved), 3<br/>lessons (read model<br/>answer types before<br/>promising, error…"
    Smith->>Trin: "user bug"
    Note right of Smith: "*user bug CMD: check<br/><sketch> with<br/>target.config:<br/>/abs/path/.mcp.json |<br/>EXPECTED: reads that<br/>file | ACTUAL: exit 2<br/>'not found next to<br/>sketc…"
    Trin->>Neo: "qa triage"
    Note right of Trin: "DEF-09 triaged Major:<br/>mcpConfig.resolveServer<br/>and sketch.loadApp use<br/>path.join(directory, x),<br/>absolute paths break.<br/>Fix: path.resolve(direc…"
    Smith->>All: "user approve"
    Note right of Smith: "User testing passed<br/>(DEF-09 fixed +<br/>retested: real via<br/>server from the<br/>project's .mcp.json).<br/>rubric UAT: COVER=S<br/>STEPS=A FAIL=S DATA=A<br/>EVID…"
    Neo->>Cypher: "retro"
    Note right of Neo: "Neo retro: SDK fit well<br/>(ProgramTransport ~60<br/>lines). Friction: mcpApp<br/>keeps per-run state in<br/>closures<br/>(looked/answered) -<br/>fine, but a seco…"
    Trin->>Cypher: "retro"
    Note right of Trin: "Trin retro: 125 -> 163<br/>tests, all offline<br/>except local example<br/>servers. The cash-<br/>refusal e2e test caught<br/>DEF-07 before UAT.<br/>mcpTarget test…"
    Morpheus->>Cypher: "retro"
    Note right of Morpheus: "Morpheus retro:<br/>ADR-0011..0013 held,<br/>ARCH §9 risk (SDK<br/>exports) retired by a<br/>probe on day one.<br/>Revisit: 'showing' over<br/>the whole MCP view (…"
    Oracle->>Cypher: "retro"
    Note right of Oracle: "Oracle retro: 3 lessons,<br/>the absence-grep AC<br/>problem repeated from<br/>sprint 2 - now a lesson.<br/>CHANGELOG still says<br/>adapters (Cypher at<br/>launch…"
    Mouse->>Cypher: "retro"
    Note right of Mouse: "Mouse retro: 4 phases +<br/>close, one plan revision<br/>(loader and examples had<br/>to share a phase to keep<br/>the gate green). No<br/>anti-loop triggers.…"
    Cypher->>Cypher: "retro"
    Note right of Cypher: "Cypher retro: the<br/>choose-not-write<br/>assumption (Jev cannot<br/>write text) was the key<br/>owner-facing call -<br/>still open as a question<br/>for the owne…"
    Smith->>Cypher: "retro"
    Note right of Smith: "Smith retro: the goal<br/>case (Claude's own<br/>.mcp.json) found DEF-09<br/>- test the headline<br/>promise with real<br/>config, not fixtures.<br/>Messages were…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "*pm launch sprint-3.<br/>Sprint complete:<br/>sketch.yaml is the only<br/>format, MCP target<br/>(stdio + streamable HTTP<br/>with token headers,<br/>mcpServers in…"
```
