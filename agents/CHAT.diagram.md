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
    Note over User,Tank: 📅 2026-10-15
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
```
