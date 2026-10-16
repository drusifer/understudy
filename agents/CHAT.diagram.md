# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Bob
    participant Mouse
    participant Trin
    participant Morpheus
    participant Cypher
    Note over User,Cypher: 📅 2026-10-16
    User->>All: "request"
    Note right of User: "I need to bind to the<br/>nic to test (owner,<br/>after /remote-control):<br/>the watch page must be<br/>reachable from another<br/>device."
    User->>All: "decide"
    Note right of User: "Owner: stop one-off<br/>verifications - use<br/>tests. From now on<br/>checks are committed<br/>tests, scratch<br/>Playwright/ad-hoc runs<br/>are not evidence."
    Bob->>All: "note"
    Note right of Bob: "Correction: 'no one-off<br/>verifications' is<br/>already AGENTS.md<br/>principle 1 (Automation<br/>First, no uncaptured<br/>shell) and the<br/>impl/bloop CAPTURE/…"
    User->>All: "request"
    Note right of User: "now please - turn sprint<br/>4's scratch browser<br/>checks into committed<br/>tests behind a make<br/>target"
    Mouse->>All: "plan"
    Note right of Mouse: "Follow-up on sprint-4<br/>(owner-approved): Tank<br/>adds make test-browser<br/>(npm run test:browser<br/>over tests/browser/,<br/>Chromium, no Jev), Trin<br/>writ…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "Trin: tests/browser/watc<br/>hPage.test.js (4 tests,<br/>headless Chromium, Jev<br/>double) replaces the<br/>sprint 4 scratch UAT<br/>scripts, layout<br/>legibility…"
    Morpheus->>All: "lead approve"
    Note right of Morpheus: "Review passed: browser<br/>tests drive the real<br/>page against real<br/>example runs, no<br/>Jev/key, make test stays<br/>browser-free (ADR-0006).<br/>Committing…"
    User->>All: "request"
    Note right of User: "Owner: add more logic to<br/>the box office - prefers<br/>horror films, evenings,<br/>only if row E, F or D is<br/>available (in that<br/>order), seats togethe…"
    User->>All: "decide"
    Note right of User: "Owner decided: all<br/>preferences are hard<br/>rules in sketch.yaml<br/>(filters + orderings on<br/>the values Jev may<br/>choose), not Jev's<br/>judgment."
    User->>All: "decide"
    Note right of User: "Owner decided: rules<br/>filter (orderings keep<br/>the best available), Jev<br/>picks among what is<br/>left."
    User->>All: "decide"
    Note right of User: "Owner: bring in more MCP<br/>servers for enrichment<br/>(a sketch plays several<br/>servers), wants the<br/>Rotten Tomatoes score.<br/>Noted: no open RT API,<br/>O…"
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Owner decided: fake<br/>ratings only (in-repo<br/>ratings MCP server,<br/>made-up scores).<br/>Checkpoint: Cypher state<br/>has the open shaping<br/>questions (rul…"
```
