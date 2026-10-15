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
    Note over User,Smith: 📅 2026-10-15
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
```
