# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Cypher
    participant Smith
    participant Morpheus
    participant Mouse
    participant All
    participant Neo
    participant Trin
    Note over Cypher,Trin: 📅 2026-10-27
    Cypher->>Smith: "handoff"
    Note right of Cypher: "Sprint 16 launched and<br/>archived. Sprint 17<br/>stories (UND-49..54) are<br/>drafted in docs/sprints/<br/>USER_STORIES_SPRINT17.md<br/>, they wait for the own…"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject REASON:<br/>UND-53 (8 pts, 7 AC)<br/>hides two stories (place<br/>in existing category /<br/>name a new one), UND-51<br/>AC1 'described as a<br/>payme…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Cypher: stories revised<br/>per Smith's rejection<br/>(UND-53 split into<br/>53+55, UND-51 rule +<br/>transfer-label counts,<br/>Depends-on lines,<br/>merchant key…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. Sprint 17<br/>stories re-reviewed:<br/>every cited fix present,<br/>29 pts adds up, criteria<br/>testable. rubric<br/>STORIES: OUT=A TEST=A<br/>FAIL…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture complete (d<br/>ocs/sprints/ARCH_SPRINT1<br/>7.md). SQL owns pairing/<br/>transfers/refunds,<br/>Python MCP source<br/>servers, Jev for refund<br/>origin…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve. Gate 2:<br/>arch reviewed, added the<br/>missing failure mode<br/>(Amex account not<br/>detectable or tied, with<br/>--amex-account refusal<br/>text…"
    Mouse->>All: "phase 0"
    Note right of Mouse: "*phase 0"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: Phase 0<br/>spike, then 5 phases<br/>(UND-49 sources, 50<br/>purchases, 51+52<br/>transfers/refunds, 53+55<br/>categories, 54 output)<br/>each impl…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Sprint plan approved:<br/>phases are 1-3 tasks,<br/>each story mapped to a<br/>typed loop, Phase 0<br/>gates the controller<br/>language. rubric PLAN:<br/>SIZE=A G…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 0 spike done (agen<br/>ts/morpheus/spike_sprint<br/>17.md). Q1 python-<br/>statemachine YAML runs<br/>stages+guards+failure<br/>(gap: no tags). Q2<br/>typesafe-…"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl done:<br/>Python MCP source<br/>servers + hydration. 16<br/>py tests pass, real<br/>files: Monarch 14,522 /<br/>Amex 4,321 records<br/>(counts only, s…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed<br/>(UND-49 AC1-5). Review<br/>found+fixed one bug<br/>(f-string docstring left<br/>a tool undescribed).<br/>@Morpheus *lead review<br/>phase-1"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed:<br/>server contract,<br/>1000-row page limit,<br/>error messages, privacy<br/>match ARCH_SPRINT17,<br/>moved the date helper<br/>out of Spri…"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl done:<br/>purchase_pairs SQL<br/>(same-date exact/order +<br/>3-day pass), Amex-<br/>account detection with<br/>refusals. Real files<br/>(counts only):…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed<br/>(UND-50 AC1-5, account<br/>detection). Finding:<br/>only 60 pairs match on<br/>statement text, so<br/>exact-first matters<br/>little. @Morph…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed:<br/>pairing rule matches<br/>ADR-0039 as amended,<br/>deterministic, one-to-<br/>one verified on real<br/>counts, no data in<br/>fixtures. No…"
    Cypher->>All: "checkpoint"
    Note right of Cypher: "Checkpoint: Sprint 17<br/>phases 0-2 done and<br/>committed on sprint-17<br/>(not pushed). Stopped<br/>before Phase 3:<br/>Monarch's card account<br/>switches sign…"
    Cypher->>All: "decision"
    Note right of Cypher: "Owner: keep the run to<br/>2026 YTD, use fresh<br/>exports. Period rule<br/>added: default start =<br/>Amex export's first<br/>date, --since overrides,<br/>older M…"
    Cypher->>Neo: "decision"
    Note right of Cypher: "Owner rule: Venmo and<br/>Zelle payments are<br/>expenses, real transfers<br/>are between the owner's<br/>own accounts (a<br/>Ridgewood savings<br/>account counts,…"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 3 impl done:<br/>transfer_pairs +<br/>refund_candidates SQL<br/>(business days), Jev<br/>client (typesafe-sdk<br/>0.7.5), refund Choice<br/>stage, transfer-p…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed<br/>(UND-51, UND-52) with<br/>Jev doubles, live Jev<br/>outcome still to run<br/>with the owner's go-<br/>ahead. @Morpheus *lead<br/>review phase…"
    Neo->>All: "correction"
    Note right of Neo: "Correction to my Phase 3<br/>handoff: the Python<br/>suite has 40 tests, not<br/>45 (25 -> now 26 model<br/>tests)."
```
