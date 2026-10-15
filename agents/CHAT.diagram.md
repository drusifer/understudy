# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Oracle
    participant Bob
    participant Tank
    participant Mouse
    participant Cypher
    participant Smith
    participant Morpheus
    participant Neo
    participant Trin
    Note over User,Trin: 📅 2026-10-15
    User->>All: "request"
    Note right of User: "/oracle groom docs: add<br/>README.md,<br/>USER_GUIDE.md, populate<br/>PROJECT.md, walkthrough<br/>of the examples"
    Oracle->>All: "progress"
    Note right of Oracle: "Oracle init: grooming<br/>docs per owner request.<br/>Done so far: README.md<br/>(what/quick start/doc<br/>map/layout, all commands<br/>via bobp make), docs/US…"
    Oracle->>All: "progress"
    Note right of Oracle: "docs/WALKTHROUGH.md<br/>written: loop diagram,<br/>CLI + web examples taken<br/>apart (app, target view,<br/>adapter hooks,<br/>statechart diagram, what<br/>Jev is…"
    Oracle->>Bob: "handoff"
    Note right of Oracle: "Groom done (uncommitted,<br/>owner commits):<br/>README.md,<br/>docs/USER_GUIDE.md,<br/>docs/WALKTHROUGH.md,<br/>agents/PROJECT.md<br/>populated,<br/>CHANGELOG/task.md…"
    User->>All: "request"
    Note right of User: "add a make target to<br/>push main"
    Tank->>All: "decide"
    Note right of Tank: "Mechanism change: adding<br/>'push' target (git push<br/>--follow-tags origin<br/>main, no force) + SDLC<br/>§3/§6. Why: owner wants<br/>pushing main to be one…"
    Tank->>All: "done"
    Note right of Tank: "push target added +<br/>verified: bobp make push<br/>ARGS=--dry-run ran check<br/>(green) then 'Everything<br/>up-to-date'. SDLC<br/>§3/§6/§9 updated.<br/>Uncommit…"
    Tank->>All: "done"
    Note right of Tank: "Owner approved: allow<br/>rule 'Bash(bobp make<br/>push *)' added to .claud<br/>e/settings.local.json<br/>(machine-local,<br/>gitignored). Agents may<br/>run bobp m…"
    User->>All: "request"
    Note right of User: "use the make push target<br/>for the full git commit<br/>orchestration"
    Tank->>All: "decide"
    Note right of Tank: "Mechanism change: push =<br/>check -> add -A -><br/>gitleaks staged scan -><br/>commit (MSG) -> push<br/>current branch + tags.<br/>Logic in scripts/push.sh<br/>(s…"
    Tank->>All: "done"
    Note right of Tank: "push orchestration done<br/>+ verified:<br/>scripts/push.sh (gate -><br/>stage -> gitleaks staged<br/>scan -> commit MSG -><br/>push current branch +<br/>tags). Sa…"
    User->>All: "request"
    Note right of User: "commit and push"
    Tank->>All: "done"
    Note right of Tank: "Committed + pushed via<br/>bobp make push: 3f183f3<br/>on main (origin/main up<br/>to date). Gate green, no<br/>leaks."
    User->>All: "request"
    Note right of User: "don't worry about recard<br/>anymore"
    Oracle->>All: "record"
    Note right of Oracle: "Owner: recard is no<br/>longer a goal. Removed<br/>recard migration from<br/>BACKLOG, consumer<br/>wording from PROJECT.md<br/>and SDLC §6/§7 (history<br/>mentions…"
    User->>All: "decide"
    Note right of User: "Owner decisions for<br/>sprint 2/3: sprint 2 =<br/>HTTP target (tiny in-<br/>repo JSON API example) +<br/>drop window.__understudy<br/>hook: pages read via<br/>acce…"
    Tank->>All: "done"
    Note right of Tank: "Recorded: SDLC §7 bump<br/>only on owner request,<br/>BACKLOG sections Sprint<br/>2 (HTTP target, hookless<br/>accessibility-tree page<br/>target + generic ada…"
    User->>All: "decide"
    Note right of User: "Owner: no back-compat.<br/>Sprint 2 deletes hook<br/>support outright (no<br/>fallback/flag/shim), old<br/>shapes are replaced, not<br/>supported alongside. No…"
    User->>All: "request"
    Note right of User: "/sprint 2 go"
    Mouse->>Cypher: "sm start"
    Note right of Mouse: "Stage 0: docs/SDLC.md<br/>present. Branch sprint-2<br/>cut from main (3f183f3)<br/>carrying the uncommitted<br/>sprint-2 decisions<br/>(BACKLOG, SDLC §7,<br/>recar…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories ready: docs/spri<br/>nts/USER_STORIES_SPRINT2<br/>.md - UND-6 JSON API<br/>target (5), UND-7<br/>hookless web page +<br/>generic adapter (5),<br/>UND-8 docs…"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject rubric<br/>STORIES: OUT=S TEST=S<br/>FAIL=W SCOPE=S SIZE=S<br/>DESIGN=A. REASON: no<br/>criterion for a run that<br/>stalls after it started<br/>(hook…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories revised: UND-6<br/>AC9 + UND-7 AC8 -<br/>stalled after first move<br/>(10 s, nothing offered,<br/>part not ended) -> exit<br/>1, outcome stalled,<br/>names…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. rubric<br/>STORIES: OUT=S TEST=S<br/>FAIL=S SCOPE=S SIZE=S<br/>DESIGN=A. Note: make<br/>'stalled' one run-loop<br/>rule for all targets,<br/>make th…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture complete: d<br/>ocs/sprints/ARCH_SPRINT2<br/>.md - http target (GET<br/>state/request moves,<br/>start-or-attach, error<br/>status logged), page<br/>tar…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve. rubric<br/>ARCH: BOUND=S FLOW=S<br/>FAIL=S USER=A DECS=S<br/>FEAS=S. Notes: stall<br/>message hints at<br/>'showing', check names<br/>'generic page…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint 2 planned:<br/>task.md phases 1-5 +<br/>close, one Neo task<br/>each, no Tank Phase 0.<br/>Self-check PLAN: SIZE=A<br/>GATE=S VERIF=S ALIGN=S<br/>OWNER=A. @…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "rubric PLAN: SIZE=A<br/>GATE=S VERIF=S ALIGN=S<br/>OWNER=A. Approved. Phase<br/>1 is groundwork with 6<br/>small items - keep each<br/>behind its own test.<br/>@Ne…"
    Mouse->>All: "phase 1"
    Note right of Mouse: "Phase 1: run-loop and<br/>loader groundwork"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl complete:<br/>stall rule (all targets,<br/>outcome stalled, showing<br/>hint), per-kind target<br/>field check, act results<br/>-> step 'response'…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed:<br/>stall test names last<br/>state + showing hint,<br/>check on adapter with<br/>target.hook -> exit 2<br/>'not a process target<br/>field (kn…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed<br/>(ADR-0010 one rule in<br/>run loop, field check<br/>names known fields).<br/>Committed. @Neo *swe<br/>impl phase-2"
    Mouse->>All: "phase 2"
    Note right of Mouse: "Phase 2: HTTP target +<br/>vending-machine example"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl complete:<br/>src/targets/http.mjs<br/>(start on free port or<br/>attach, ready-wait 10 s,<br/>GET-state view w/ seq +<br/>last answer, request ac…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed LIVE:<br/>run examples/http -><br/>coin:1, buy:water, done,<br/>exit 0, attach mode<br/>plays a hand-started<br/>server and leaves it<br/>runnin…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed<br/>(ADR-0008, program.mjs<br/>reused). Committed. @Neo<br/>*swe impl phase-3"
    Mouse->>All: "phase 3"
    Note right of Mouse: "Phase 3: hookless page<br/>target (accessibility<br/>snapshot)"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 3 impl complete:<br/>src/targets/aria.mjs<br/>(snapshot -><br/>title/text/controls,<br/>disabled dropped,<br/>options carry list,<br/>checked/selected), page…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed:<br/>parser cases (disabled,<br/>hidden-absent, combobox<br/>options, links, quotes,<br/>nesting) on a recorded<br/>1.62.1 snapshot,<br/>actions…"
```
