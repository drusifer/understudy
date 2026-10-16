# CHAT_SPRINT_4 — Sprint Archive

## Summary

Sprint 4: owner asked for a live view of the understudy; shaping settled a browser page, live + replay, pick + confidence, pause/step. Smith approved stories (control-enabled note) and architecture (cut-short log note): event-stream log via XState inspection, node:http + SSE server with own SVG layout (Mermaid rejected, 122 MB), pause gate before each move. Six phases passed UAT (real Chromium) and review; findings fixed: layout legibility (visual check), replay grain (frames per line), Ctrl-C while paused. Close: SDLC green, 3 lessons, Smith found DEF-12 (outcome doubled) - fixed. Launched; merge awaits owner.

---

## Planning

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Oracle
    participant Tank
    participant Cypher
    participant Smith
    participant Morpheus
    participant Mouse
    participant Neo
    Note over User,Neo: 📅 2026-10-15
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
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories ready for user<br/>review: docs/sprints/USE<br/>R_STORIES_SPRINT4.md -<br/>UND-13 log tells the<br/>whole story (3), UND-14<br/>watch live (5), UND-15<br/>p…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. Stories<br/>approved. rubric<br/>STORIES: OUT=S TEST=S<br/>FAIL=A SCOPE=S SIZE=A<br/>DESIGN=A. Note folded<br/>into UND-15 AC1: only<br/>the applica…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture complete: d<br/>ocs/sprints/ARCH_SPRINT4<br/>.md - log as event<br/>stream (start/state<br/>lines via XState<br/>inspect, idle looks<br/>folded), watch…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve.<br/>Architecture approved.<br/>rubric ARCH: BOUND=A<br/>FLOW=S FAIL=A USER=A<br/>DECS=A FEAS=A. Folded<br/>in: a log with no final<br/>line replays…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: task.md<br/>- 6 phases (event-stream<br/>log, graph+server, live<br/>page + --watch,<br/>pause/step, replay,<br/>docs) + close. Sprint 3<br/>board…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Sprint plan approved.<br/>rubric PLAN: SIZE=A<br/>GATE=A VERIF=A ALIGN=A<br/>OWNER=A. Note: Phase 1<br/>changes stdout, so tests<br/>reading step lines<br/>(exampl…"
```

---

## Phase 1

Phase 1: the log tells the whole story (UND-13)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl complete:<br/>seat records transitions<br/>via XState inspect (idle<br/>looks folded into<br/>idle_looks), stream.mjs<br/>emits<br/>start/state/step/f…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed:<br/>test-live green x5,<br/>every log first line<br/>start, 10-14 state lines<br/>(>=1 per step), coffee-<br/>cli's waits folded<br/>(idle_looks…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed vs<br/>ADR-0014. Note: seat<br/>reads XState's<br/>_transitions (inspection<br/>microstep internals) -<br/>pinned by the run test's<br/>exact…"
```

---

## Phase 2

Phase 2: graph layout and the watch server (UND-14 server side)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl complete:<br/>turnGraph (turn -><br/>labelled nodes/edges,<br/>all examples), layered<br/>SVG layout, watch server<br/>(127.0.0.1, token path,<br/>pag…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed:<br/>tests cover<br/>graph/layout/server ACs.<br/>Visual check (layout<br/>rendered in Chromium)<br/>caught labels squeezed<br/>under boxes and…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed vs<br/>ADR-0015: no dependency,<br/>pure layout shared with<br/>the browser, server<br/>serves a whitelist only.<br/>Committing. @Neo *sw…"
```

---

## Phase 3

Phase 3: the live page and run --watch (UND-14)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Tank
    participant All
    participant Neo
    participant Trin
    participant Morpheus
    Note over Tank,Morpheus: 📅 2026-10-15
    Tank->>All: "done"
    Note right of Tank: "Task 3.2 (Tank):<br/>eslint.config.js gives<br/>src/watch/page.mjs<br/>browser globals<br/>(document, globalThis),<br/>same shape as the<br/>examples/web block, no…"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 3 impl complete:<br/>page.html/css/mjs (SVG<br/>diagram, current state +<br/>last transition,<br/>decision feed, ending,<br/>no reconnect loop), run<br/>--wa…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed:<br/>Chromium drove the live<br/>page during real runs of<br/>mcp, web, http (cli in<br/>tests): highlight<br/>followed each state<br/>change wi…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 3 review passed:<br/>page logic pure and<br/>tested, DOM thin, server<br/>before judge/target,<br/>'ended' log line is a<br/>reviewed arch amendment<br/>(fin…"
```

---

## Phase 4

Phase 4: pause and step a live run (UND-15)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 4 impl complete:<br/>gate.mjs<br/>(pause/step/resume/stop,<br/>paused time), run waits<br/>at the gate before each<br/>move (no Jev while<br/>paused, idle li…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 4 passed<br/>(live, Chromium):<br/>--pause -> 'paused<br/>before step 1' at<br/>choosing, Pause off /<br/>Step+Resume on, 12 s<br/>paused not stalled, St…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 4 review passed vs<br/>ADR-0016: gate before<br/>takeStep, no Jev while<br/>paused, stop() only<br/>short-circuits a paused<br/>run so --watch alone<br/>chan…"
```

---

## Phase 5

Phase 5: replay a finished run (UND-16)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 5 impl complete:<br/>replay.mjs (start line,<br/>JSON per line),<br/>understudy watch <log><br/>[--port N] (until<br/>Ctrl-C), page replay<br/>mode (frames:…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 5 passed<br/>(Chromium, real MCP<br/>log): understudy watch<br/><log> prints its<br/>address, Step<br/>forward/back walk each<br/>state change (finding f…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 5 review passed:<br/>replay is the live page<br/>fed the same events<br/>(ADR-0015), frames per<br/>line is a reviewed UX<br/>change, recorded in the<br/>UAT…"
```

---

## Phase 6

Phase 6: docs show how to watch (UND-17)

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
    Note right of Neo: "Phase 6 impl complete<br/>(Neo+Oracle): USER_GUIDE<br/>§5 Watch a run (live,<br/>pause/step, replay,<br/>SSH), troubleshooting +<br/>command reference,<br/>SKETCHE…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 6 passed:<br/>image links resolve<br/>(README, USER_GUIDE),<br/>every documented command<br/>gives the documented<br/>line (--help,<br/>--pause/--port wi…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "Phase 6 review passed:<br/>docs match code (event<br/>lines, controls,<br/>refusals), ADRs cite the<br/>Phase 2 and 5 findings.<br/>All phases reviewed.<br/>@Tank…"
    Tank->>Oracle: "devops handoff"
    Note right of Tank: "SDLC check passed:<br/>distclean -> install<br/>(manifest + lockfile<br/>unchanged) -> check<br/>green 200/200, imports<br/>in src/watch are node:<br/>built-ins on…"
    Oracle->>Smith: "ora handoff"
    Note right of Oracle: "Docs groomed:<br/>UAT_PLAN_SPRINT4 (6<br/>scenarios, 9 negative,<br/>DEF-10/11 resolved), 3<br/>lessons (look at a<br/>drawing, replay at the<br/>user's grain, a n…"
    Smith->>Trin: "user bug"
    Note right of Smith: "*user bug CMD: run <web<br/>sketch without showing><br/>--watch, let it stall |<br/>EXPECTED: 'stalled:<br/>nothing to do...' |<br/>ACTUAL: 'stalled:<br/>stalled:…"
    Trin->>Neo: "qa triage"
    Note right of Trin: "DEF-12 triaged Minor:<br/>endingOf always prefixes<br/>outcome, the watchPage<br/>test even asserted the<br/>doubled text. Fix:<br/>prefix only when the<br/>messag…"
    Smith->>All: "user approve"
    Note right of Smith: "User testing passed<br/>(DEF-12 fixed +<br/>retested). rubric UAT:<br/>COVER=S STEPS=A FAIL=S<br/>DATA=A EVID=S. Lessons<br/>x3: rubric LESSON: CTX=A<br/>ISSUE=S R…"
    Neo->>Cypher: "retro"
    Note right of Neo: "Neo retro: no dependency<br/>added, page logic pure<br/>and tested in Node, DOM<br/>thin. Friction: page.mjs<br/>is now the biggest file<br/>(~300 lines) - spl…"
    Trin->>Cypher: "retro"
    Note right of Trin: "Trin retro: 176 -> 200<br/>tests, real-browser UAT<br/>scripts caught what unit<br/>tests could not (layout<br/>legibility, replay<br/>grain). Backlog: keep a…"
    Morpheus->>Cypher: "retro"
    Note right of Morpheus: "Morpheus retro:<br/>ADR-0014..0016 held, one<br/>arch amendment (ended<br/>line). XState<br/>_transitions dependency<br/>is pinned by a test.<br/>Revisit: SSE reco…"
    Oracle->>Cypher: "retro"
    Note right of Oracle: "Oracle retro: 3 lessons,<br/>two of them UX findings<br/>from looking at real<br/>output. Docs: screenshot<br/>is from a real run.<br/>Backlog: none."
    Mouse->>Cypher: "retro"
    Note right of Mouse: "Mouse retro: 6 phases,<br/>no plan revision needed,<br/>no anti-loop. 16 pts.<br/>Phase 3 (page) was the<br/>largest - fine at 3<br/>tasks."
    Cypher->>Cypher: "retro"
    Note right of Cypher: "Cypher retro: stories<br/>held, one AC detail<br/>added at Gate 1 (enabled<br/>controls). Replay<br/>granularity was not<br/>specified - the AC said<br/>Step forwa…"
    Smith->>Cypher: "retro"
    Note right of Smith: "Smith retro: pausing a<br/>running run and a failed<br/>run's display were only<br/>proven end to end -<br/>worth keeping in the UAT<br/>plan. Backlog: shorten…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "*pm launch sprint-4.<br/>Sprint complete: run<br/>--watch live page<br/>(statechart, current<br/>state, decisions),<br/>pause/step/resume,<br/>understudy watch <lo…"
```
