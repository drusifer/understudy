# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `bobp chat-diagram` (or it regenerates automatically on every `bobp chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Cypher
    participant All
    participant smith
    participant Smith
    participant cypher
    participant Morpheus
    participant Mouse
    participant Neo
    Note over Cypher,Neo: 📅 2026-10-30
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Checkpoint saved in<br/>agents/cypher/state.md.<br/>Sprint 19 merged and<br/>pushed (ea5f76b),<br/>nothing in flight. Next:<br/>plan slice B (translate<br/>the old…"
    Cypher->>smith: "handoff"
    Note right of Cypher: "Sprint 20 stories<br/>drafted (UND-68..71, 21<br/>pts): evening + seating<br/>subsketch, ETL as sketch<br/>on file sources, purge<br/>old shapes. Owner chose<br/>f…"
    Smith->>cypher: "reject"
    Note right of Smith: "rubric STORIES: OUT=A<br/>TEST=W FAIL=A SCOPE=A<br/>SIZE=W DESIGN=A. *user<br/>reject REASON: UND-68<br/>AC2 has no concrete<br/>case, 68 depends on 69<br/>and hid…"
    Cypher->>smith: "handoff"
    Note right of Cypher: "Stories revised:<br/>concrete input cases<br/>(UND-70), model gaps<br/>split out as UND-68,<br/>seating UND-69 before<br/>the evening, ETL fixture<br/>captured fir…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "rubric STORIES: OUT=A<br/>TEST=S FAIL=A SCOPE=A<br/>SIZE=S DESIGN=A. *user<br/>approve. Both findings<br/>fixed: concrete input<br/>cases, dependencies and<br/>ord…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture drafted (do<br/>cs/sprints/ARCH_SPRINT20<br/>.md): SQLMesh stays, ETL<br/>Jev reads become<br/>kind:jev sources, CSV as<br/>file format, candidates…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "rubric ARCH: BOUND=A<br/>FLOW=A FAIL=A USER=A<br/>DECS=A FEAS=A. *user<br/>approve. Messages match<br/>the stories, UND-73 is a<br/>real gap and is now in<br/>the…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint 20 planned in<br/>task.md: 7 phases (68<br/>gaps, 73 candidates, 69<br/>seating, 70 evening, 71<br/>in two phases with the<br/>ETL expected file<br/>frozen…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "rubric PLAN: SIZE=A<br/>GATE=A VERIF=A ALIGN=A<br/>OWNER=A. Plan approved.<br/>Phase 5 freezes the ETL<br/>expected file before any<br/>ETL change, as the stor…"
    Morpheus->>All: "lead"
    Note right of Morpheus: "Syntax decisions with<br/>owner (ADR-0050): no<br/>inputs block, every<br/>sketch is a Jinja2<br/>template over standard<br/>YAML 1.2, values come<br/>from --with…"
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Sprint 20 phase 1 code<br/>committed locally<br/>(ef98618): Jinja2 +<br/>--with/with, each,<br/>outcome, outputs/from<br/>(decider keyword gone).<br/>179 tests, li…"
    Morpheus->>All: "lead"
    Note right of Morpheus: "Owner reviewed choices<br/>A-F (all accepted, B<br/>kept for now). Open item<br/>2 answered by Morpheus:<br/>retire 'decider' from<br/>the domain (Decision<br/>Row…"
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Checkpoint (context<br/>62%): sprint-20 local at<br/>2dce220, 220 tests, lint<br/>clean. Done: phases 1-3,<br/>stage model<br/>(map/reduce/sink/sketch,<br/>kind:st…"
```
