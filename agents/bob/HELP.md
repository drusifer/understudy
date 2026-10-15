# BobProtocol — Quick Reference

Type `*help` anytime to see this. One AI switches between 9 specialized personas driven by `agents/CHAT.md`.

**Basic usage:**
- `*chat <message>` — auto-routes to the right persona
- `*chat @<Persona> *<command> <args>` — direct invocation
- `@<Persona> <message>` — direct invocation (Gemini-style)
- `*<command> <args>` — skip the chat layer, invoke a persona directly

**Note on Direct Invocations**: Different AI harnesses use different prefixes for direct persona invocation (e.g., `@persona` or `/persona` in Gemini CLI, `/persona` in Claude, `$persona` in Codex). If you are invoked directly via such a command, you MUST log the invocation to `agents/CHAT.md` immediately upon entry if it has not already been logged.

---

## Session Lifecycle Triggers

Formalized in `agents/skills/init/SKILL.md` & `agents/skills/prep-clear/SKILL.md`.

| Command / Trigger | Action | Primary Handler |
|-------------------|--------|-----------------|
| `*init`, `/init`, `*startup` | Initialize session, sync links, display quick reference | Bob (`*prompt`) |
| `*resume` | Cold-start recovery from last CHAT.md handoff | Last active persona |
| `*prep-clear`, `/prep-clear`, `*checkpoint` | Reconcile state, write resume plan, prepare for `/clear` | Active persona |

---

## Workflow Loops (Bloop — Hierarchical SDLC Cycles)

Multi-persona autonomous workflows decomposed into two tiers:

### Planning Loops (Strategic Scoping & Specification)
| Command | Primary Handler & Gates | Output / Deliverable |
|---------|-------------------------|----------------------|
| `*plan epic <name>` | Cypher → Smith gate → Morpheus domain → (Spikes) | `VISION.md`, appetite, `docs/DOMAIN.md` |
| `*plan story <slice>` | Cypher → Smith gate 1 → Morpheus → Trin → Smith gate 2 | Vertical slices, `ARCH.md` ADRs, `TEST_STRATEGY.md` |
| `*plan sprint [tier1\|tier2]` | Cypher → Smith gate → Morpheus → Smith gate → Mouse | Sprint commitment, `task.md` with typed Work Loops |

### Work Loops (Tactical Execution Chains)
| Command | Chain | Invariant / Focus |
|---------|-------|-------------------|
| `*impl <task>` | Neo TDD → Trin UAT → Morpheus review | **Test-First**: failing test required before production code |
| `*fix <bug>` | Neo diagnose → User confirm → Neo fix → Trin → Morpheus | **Reproduce First**: diagnose & confirm before code edits |
| `*refactor <target>` | Morpheus plan → Trin baseline → Neo → Trin parity → Morpheus | **Two Hats**: zero behavioral change, 100% green before/after |
| `*spike <topic>` | Oracle survey → Neo prototype → Morpheus decision | **Disposable**: timeboxed, zero prod code, `FINDING.md` / ADR |
| `*uat <scope>` | Trin matrix → Smith UX audit → Cypher sign-off | **Real-World**: live running software, UX evaluation |
| `*deploy <env>` | Tank Makefile deploy → Trin live smoke test | **Pipeline as Code**: automated release via `bobp make deploy` |

---

## The Team

### Bob — Prompt Engineer
`agents/bob/SKILL.md` · prefix: `*new` / `*reprompt` / `*learn`

| Command | Action |
|---------|--------|
| `*new <desc>` | Create a new agent |
| `*reprompt <instructions>` | Update existing agents |
| `*learn <lesson>` | Broadcast lesson to all agents |
| `*help` | Show this reference |

### Cypher — Product Manager
`agents/cypher/SKILL.md` · prefix: `*pm`

| Command | Action |
|---------|--------|
| `*pm story <request>` | Write user stories |
| `*pm req <feature>` | Define requirements and acceptance criteria |
| `*pm prioritize` | Prioritize the backlog |
| `*pm update` | Post product status update |
| `*pm doc <topic>` | Create a PRD or product document |

### Morpheus — Tech Lead
`agents/morpheus/SKILL.md` · prefix: `*lead`

| Command | Action |
|---------|--------|
| `*lead arch <topic>` | Architecture review or decision |
| `*lead plan <story>` | Create technical implementation plan |
| `*lead decide <choice>` | Make and record an architectural decision |
| `*lead guide <area>` | Provide technical guidance |
| `*lead refactor <target>` | Plan a refactoring strategy |

### Neo — Software Engineer
`agents/neo/SKILL.md` · prefix: `*swe`

| Command | Action |
|---------|--------|
| `*swe impl <task>` | Implement a feature |
| `*swe fix <issue>` | Diagnose and fix a bug |
| `*swe test <scope>` | Write and run tests |
| `*swe refactor <target>` | Refactor code |

### Oracle — Knowledge Officer
`agents/oracle/SKILL.md` · prefix: `*ora`

| Command | Action |
|---------|--------|
| `*ora ask <question>` | Query the knowledge base |
| `*ora record <type> <content>` | Log a decision, lesson, or finding |
| `*ora groom` | Audit and organise the file structure |
| `*ora distill <file>` | Break down a large doc with TL;DR + ToC |
| `*ora tldr` | Write/update TLDR blocks in all files |
| `*ora archive` | Archive old CHAT.md messages |

### Trin — QA Guardian
`agents/trin/SKILL.md` · prefix: `*qa`

| Command | Action |
|---------|--------|
| `*qa test <scope>` | Run tests (`all`, `unit`, `integration`, or specific) |
| `*qa verify <feature>` | Verify acceptance criteria |
| `*qa review <change>` | Code review |
| `*qa report` | Summarise codebase health |
| `*qa repro <issue>` | Reproduce a bug |

### Mouse — Scrum Master
`agents/mouse/SKILL.md` · prefix: `*sm`

| Command | Action |
|---------|--------|
| `*sm status` | Current sprint progress |
| `*sm plan <sprint>` | Create or update a sprint plan |
| `*sm tasks` | List active tasks |
| `*sm next` | Identify and assign the next task |
| `*sm blocked` | Report and triage a blocker |
| `*sm done <task>` | Mark a task complete |
| `*sm assign <task> <persona>` | Assign a task |
| `*sm velocity` | Team velocity metrics |

### Smith — Expert User & UX Advocate
`agents/smith/SKILL.md` · prefix: `*user`

| Command | Action |
|---------|--------|
| `*user review <stories>` | Review user stories and acceptance criteria |
| `*user test <feature>` | Usability-test a feature by running the software |
| `*user consult <question>` | Quick, non-blocking UX opinion |
| `*user feedback <question>` | Deeper investigation of open UX/domain questions |
| `*user approve [gate]` | Approve a sprint review gate |
| `*user reject REASON: … | FIX: …` | Block a sprint gate |
| `*user bug CMD: … | EXPECTED: … | ACTUAL: … | UX ISSUE: …` | File a usability defect |

### Tank — DevOps Engineer
`agents/tank/SKILL.md` · prefix: `*devops`

| Command | Action |
|---------|--------|
| `*devops deploy` | Orchestrate deployment |
| `*devops infra` | Declarative IaC management |
| `*devops ci` | Maintain CI/CD pipelines |
| `*devops env` | Environment hygiene & secrets |
| `*devops bootstrap <lang>` | Setup build environment & manifest |
| `*devops sdlc [check]` | Create or audit docs/SDLC.md |

---

## Sprint Cycle (Quick Reference)

```
*plan sprint (or *plan epic / *plan story)
  └─ Stage 0: SDLC Gate (docs/SDLC.md verified by Tank)
  └─ Cypher *pm plan sprint
  └─ [Smith *user approve]         ← Gate 1 (STORIES Rubric)
  └─ Morpheus *lead arch sprint
  └─ [Smith *user approve]         ← Gate 2 (ARCH Rubric)
  └─ Mouse *sm plan sprint (task.md with typed Work Loops)
  └─ Morpheus *lead review sprint plan

Per task / phase (execute typed Work Loops):
  └─ *impl <task>          (Neo TDD → Trin verify → Morpheus review)
  └─ *fix <defect>         (Neo diagnose/fix → Trin test → Morpheus review)
  └─ *refactor <target>    (Neo restructure → Trin parity → Morpheus review)
  └─ *spike <unknown>      (Neo prototype → Morpheus decision / ADR)
  └─ *uat <phase>          (Trin acceptance → Smith UX evaluation)
  └─ *deploy <target>      (Tank automated deploy → Trin smoke)

Sprint close:
  └─ Tank *devops sdlc-check
  └─ Oracle *ora groom
  └─ Smith *user test + *user feedback
  └─ All *sprint retro             ← feeds backlog
  └─ Cypher *pm launch <sprint>
```

---

## State Management Protocol (CRITICAL)

See `agents/skills/bob-protocol/SKILL.md`, `agents/skills/init/SKILL.md`, & `agents/skills/prep-clear/SKILL.md`.

- **ENTRY**: Read `agents/CHAT.md` (last 10–20 messages) → load `agents/[persona]/state.md`.
- **WORK**: Update working memory (`state.md`), post brief updates to `agents/CHAT.md`.
- **EXIT (Mandatory Hard Gate)**:
  1. **Pre-Clear / Checkpoint**: Follow `agents/skills/prep-clear/SKILL.md` before `/clear` or persona switch. Update `agents/[persona]/state.md` (Context, Current Task progress %, Next Steps cold-start resume plan).
  2. **Handoff Message**: `bobp chat "<summary> @NextPersona *command" --persona <Name> --cmd handoff --to <next>`.
  3. Never switch personas or clear context without completing both steps.

---

## Active Anti-Loop Guard

If any loop iteration or step repeats **more than twice** without resolution:
1. **PAUSE** execution immediately.
2. Consult **Oracle**: `bobp chat "@Oracle *ora ask <error>" --persona <Name> --cmd ask --to Oracle`.
3. Allow **ONE** retry with a fresh approach based on Oracle's insight.
4. If that fails, escalate to the user with full logs. **No third attempt** without explicit user guidance.

---

## Common Make Targets (Single Front Door via bobp make)

```bash
bobp make help       # list all project targets
bobp make test       # run tests (captured to build/build.out, quiet on pass)
bobp make test-q     # targeted quiet test runner (e.g. ARGS="-k test_name")
bobp make -vvv test  # full output live
bobp chat            # post to CHAT.md
```

See **[SHORTHAND_GUIDE.md](../../SHORTHAND_GUIDE.md)** for the full trigger reference.
