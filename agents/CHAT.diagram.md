# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Mouse
    participant Tank
    participant Smith
    participant Cypher
    participant Morpheus
    Note over User,Morpheus: 📅 2026-10-15
    User->>All: "request"
    Note right of User: "make it so - plan<br/>Understudy sprint 1 from<br/>recard's extraction map<br/>(recard: agents/morpheus<br/>/understudy_extraction_m<br/>ap.md). Decisions: web<br/>+…"
    Mouse->>Tank: "handoff"
    Note right of Mouse: "Files moved in from<br/>recard d817d3c: src/<br/>(escalate, decide,<br/>strategyFile, machine,<br/>seat, shutdown, library,<br/>table) + 7 tests<br/>(imports -> ..…"
    User->>All: "request"
    Note right of User: "/init"
    Tank->>All: "resume"
    Note right of Tank: "Resuming *devops build-<br/>env from last session<br/>(Mouse handoff):<br/>package.json, Makefile,<br/>docs/SDLC.md, then run<br/>the 7 copied tests."
    Tank->>All: "decide"
    Note right of Tank: "Build-env decision: npm<br/>+ package.json +<br/>package-lock (no<br/>lockfile exists,<br/>ecosystem default,<br/>matches recard). Node<br/>pinned >=24 via engines…"
    Tank->>Smith: "handoff"
    Note right of Tank: "build-env done<br/>(uncommitted):<br/>npm+lockfile, Node>=24,<br/>Makefile front door,<br/>make check =<br/>test+lint+secrets all<br/>green, 7 copied test<br/>files pa…"
    User->>All: "request"
    Note right of User: "/sprint mvp first run"
    User->>All: "decide"
    Note right of User: "Owner answers: scope as<br/>drafted (13 pts), work<br/>on sprint-1 branch,<br/>merge at close, agents<br/>commit per reviewed<br/>phase, never push<br/>(build-env…"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject rubric<br/>STORIES: OUT=S TEST=A<br/>FAIL=W SCOPE=A SIZE=W<br/>DESIGN=A. REASON: UND-2<br/>no failure AC, UND-1 can<br/>run forever (no step<br/>cap),…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories revised: step<br/>cap (50, --steps), off-<br/>list = re-ask once then<br/>stop exit 1, UND-2<br/>failure ACs (no Chromium<br/>-> exit 2 + install<br/>hint,…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. rubric<br/>STORIES: OUT=S TEST=S<br/>FAIL=S SCOPE=A SIZE=S<br/>DESIGN=A. Notes:<br/>install-browser is a new<br/>make target (Tank), keep<br/>exit c…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture complete: d<br/>ocs/sprints/ARCH_SPRINT1<br/>.md. Target interface vi<br/>ew/act/talk/say/describe<br/>/close (process + page),<br/>adapter.mjs + part…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve. rubric<br/>ARCH: BOUND=S FLOW=S<br/>FAIL=S USER=A DECS=S<br/>FEAS=S. Notes: specify<br/>check success line,<br/>library listing format,<br/>log path…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: task.md,<br/>Phase 0 (Tank:<br/>run/install-<br/>browser/test-live<br/>targets) + phases 1-7,<br/>one Neo task each + Trin<br/>UAT + Morpheus review…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "rubric PLAN: SIZE=A<br/>GATE=S VERIF=S ALIGN=S<br/>OWNER=A. Approved. Note:<br/>Task 1.1 is the heaviest<br/>Neo task - keep the off-<br/>list change test-first…"
```
