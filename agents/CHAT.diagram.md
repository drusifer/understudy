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
    Note over User,Cypher: 📅 2026-10-16
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
    User->>All: "decide"
    Note right of User: "Owner: knobs set inputs<br/>before a run, the<br/>dashboard starts it (a<br/>Go lever). Not live<br/>tuning."
    User->>All: "decide"
    Note right of User: "Owner: the dashboard<br/>opens a folder of<br/>sketches to choose from,<br/>each sketch's declared<br/>inputs define its knobs<br/>and switches."
    User->>All: "decide"
    Note right of User: "Owner: a new switch<br/>input (on/off) turns a<br/>gate on or off via when:<br/><switch>."
    Cypher->>All: "update"
    Note right of Cypher: "Dashboard mockup<br/>published for owner<br/>review: https://claude.a<br/>i/artifact/KDDBABtgUpn5N<br/>bnKT9h1TQ (brass panel,<br/>sketch rack, mood<br/>selector, we…"
    User->>All: "feedback"
    Note right of User: "Owner mockup feedback:<br/>physical knobs, mood =<br/>rotary pointer dial<br/>(oblong, smaller centre)<br/>with options around it,<br/>LED lamps for switches,…"
    User->>All: "feedback"
    Note right of User: "Owner: under each weight<br/>slider, a slide-down<br/>panel with simple edit<br/>boxes to change that<br/>factor's defaults<br/>(range, order, question,<br/>defaul…"
    User->>All: "decide"
    Note right of User: "Owner: drawer edits are<br/>saved to the sketch,<br/>with a reset to defaults<br/>- reset by turning the<br/>console off and back on<br/>(power cycle)."
    Cypher->>All: "update"
    Note right of Cypher: "Mockup v6: bigger state<br/>tube with labelled<br/>transitions (events,<br/>guards) and the power<br/>ring + blended orb<br/>inside it, POWER switch<br/>(off then…"
    User->>All: "feedback"
    Note right of User: "Owner: an access panel<br/>under the mood dial to<br/>edit the moods (rename,<br/>add, remove) and the<br/>default. Added to the<br/>mockup (v7), the dial<br/>spre…"
```
