# BobProtocol Documentation Index

**Last Updated:** 2026-03-22

## Quick Access

Type `*help` for complete command reference with examples.

---

## Primary Documentation

### Getting Started
- **[STARTUP.md](../STARTUP.md)** - LLM startup instructions
- **[docs/WALKTHROUGH.md](../docs/WALKTHROUGH.md)** - Step-by-step user walkthrough: building an app with Bob Protocol
- **[skills/init/SKILL.md](skills/init/SKILL.md)** - Canonical session initialization & resume skill
- **[skills/prep-clear/SKILL.md](skills/prep-clear/SKILL.md)** - Pre-clear checkpointing & state preservation skill
- **[README.md](../README.md)** - Project overview and team reference
- **[SHORTHAND_GUIDE.md](../SHORTHAND_GUIDE.md)** - Complete trigger/command reference
- **[HELP.md](bob/HELP.md)** - Quick reference for all 9 personas and commands

### Tools
- **`bobp` CLI** - Agent tooling subcommands (`bobp chat`, `bobp make`, `bobp setup-agent-links`, …); run `bobp --help` for the full list

---

## Persona Documentation

### Active Personas (9)

| Persona | Role | SKILL.md | Prefix |
|---------|------|----------|--------|
| Bob | Prompt Engineering Expert | [bob/SKILL.md](bob/SKILL.md) | `*new` / `*reprompt` / `*learn` |
| Cypher | Product Manager | [cypher/SKILL.md](cypher/SKILL.md) | `*pm` |
| Morpheus | Tech Lead / Architect | [morpheus/SKILL.md](morpheus/SKILL.md) | `*lead` |
| Neo | Senior Software Engineer | [neo/SKILL.md](neo/SKILL.md) | `*swe` |
| Oracle | Knowledge Officer | [oracle/SKILL.md](oracle/SKILL.md) | `*ora` |
| Trin | QA / Guardian | [trin/SKILL.md](trin/SKILL.md) | `*qa` |
| Mouse | Scrum Master | [mouse/SKILL.md](mouse/SKILL.md) | `*sm` |
| Smith | Expert User & UX Advocate | [smith/SKILL.md](smith/SKILL.md) | `*user` |
| Tank | DevOps Engineer | [tank/SKILL.md](tank/SKILL.md) | `*devops` |

---

## Skills & Workflow Loops (`agents/skills/`)

Bob Protocol organizes autonomous workflows into hierarchical loops and supporting capabilities:

### Planning Loops (Strategic Scoping & Specification)
- **[skills/epic/SKILL.md](skills/epic/SKILL.md)** - Strategic Epic discovery, appetite framing, domain modeling, and de-risking spikes (*Shape Up* / *Inspired*)
- **[skills/story/SKILL.md](skills/story/SKILL.md)** - User story vertical slicing, INVEST acceptance criteria, ADRs, test strategies (*User Story Mapping* / *Agile Estimating*)
- **[skills/sprint/SKILL.md](skills/sprint/SKILL.md)** - Sprint planning, phase execution, review gates, retrospective, and launch (*Scrum Guide*)

### Work Loops (Tactical Execution & Verification)
- **[skills/bloop/SKILL.md](skills/bloop/SKILL.md)** - Conductor for multi-persona autonomous work loops
- **[skills/impl/SKILL.md](skills/impl/SKILL.md)** - TDD implementation loop: test-first, red-green-refactor, acceptance verification (*TDD: By Example*)
- **[skills/fix/SKILL.md](skills/fix/SKILL.md)** - Defect diagnosis & surgical fix: reproduce first, confirm diagnosis, surgical repair, regression sweep (*Debugging*)
- **[skills/refactor/SKILL.md](skills/refactor/SKILL.md)** - Behavior-preserving refactoring: Two-Hats rule, green baseline, zero behavioral drift (*Refactoring*)
- **[skills/spike/SKILL.md](skills/spike/SKILL.md)** - Disposable timeboxed spike: rapid prototyping, zero production code, findings/ADR output (*XP Installed*)
- **[skills/uat/SKILL.md](skills/uat/SKILL.md)** - User acceptance testing: end-to-end scenario verification, UX heuristic evaluation (*Agile Testing*)
- **[skills/deploy/SKILL.md](skills/deploy/SKILL.md)** - Delivery & release loop: pipeline-as-code via Makefile, live smoke test verification (*Continuous Delivery*)

### Session Lifecycle & Protocol Skills
- **[skills/init/SKILL.md](skills/init/SKILL.md)** - Canonical session initialization, link validation, and cold-start resume
- **[skills/prep-clear/SKILL.md](skills/prep-clear/SKILL.md)** - Pre-clear checkpointing, state preservation, and cold-start resume plan
- **[skills/judge/SKILL.md](skills/judge/SKILL.md)** - Prompt & skill evaluation, bug/anti-pattern cataloging, and instruction optimization
- **[skills/bob-protocol/SKILL.md](skills/bob-protocol/SKILL.md)** - Multi-persona coordination protocol, state management, and routing
- **[skills/bob-tools/SKILL.md](skills/bob-tools/SKILL.md)** - `bobp` CLI operations, output capture, and link management
- **[skills/build-env/SKILL.md](skills/build-env/SKILL.md)** - Language build environment setup, manifests, and `docs/SDLC.md` management
- **[skills/chat/SKILL.md](skills/chat/SKILL.md)** - Structured team communication and handoffs in `CHAT.md`
- **[skills/linter/SKILL.md](skills/linter/SKILL.md)** - Code quality, linting, type checks, and static analysis
- **[skills/make/SKILL.md](skills/make/SKILL.md)** - Project Makefile execution with build output capture
- **[skills/make-discover/SKILL.md](skills/make-discover/SKILL.md)** - Makefile target self-discovery guide
- **[skills/personas/SKILL.md](skills/personas/SKILL.md)** - Persona switching and direct specialist delegation
- **[skills/render/SKILL.md](skills/render/SKILL.md)** - Render cloud infrastructure and deployment management
- **[skills/test-runner/SKILL.md](skills/test-runner/SKILL.md)** - Bounded test execution and quiet test runners
- **[skills/via/SKILL.md](skills/via/SKILL.md)** - Strict symbol lookup and relationship queries

---

## Team Communication

- **[CHAT.md](CHAT.md)** - Team communication log (append-only)
- Each persona maintains state in their `<name>/` folder:
  - `state.md` - Working memory: Context, Current Task, and Next Steps sections

---

## Template Files

Located in `agents/templates/`:

- `ARTIFACTS.md` - Artifact inventory, rubric quality standards, and review gates
- `_template_USER_STORIES.md` - Sprint user stories (rubric: STORIES)
- `_template_ARCH.md` - System & sprint architecture (rubric: ARCH)
- `_template_DOMAIN.md` - Domain model & ubiquitous language specification (rubric: DOMAIN)
- `_template_task.md` - Sprint task board (rubric: PLAN)
- `_template_SDLC.md` - Software development lifecycle (rubric: SDLC; variants for python, javascript)
- `_template_LESSON.md` - Engineering lessons learned (rubric: LESSON)
- `_template_DECISION.md` - Architecture decision record / MADR (rubric: DECISION)
- `_template_finding.md` - Research spike & technical finding (rubric: FINDING)
- `_template_TEST_STRATEGY.md` - Quality & UAT strategy (rubric: STRATEGY)
- `_template_UAT_PLAN.md` - Sprint acceptance test plan (rubric: UAT)
- `_template_state.md` - Agent working memory state
- `_template_CHAT.md` - CHAT.md message format
- `_template_tldr.md` - TLDR block formats

---

## Tools

Shipped as `bobp` CLI subcommands, not project-local scripts:

- `bobp chat` - Post messages to CHAT.md
- `bobp make <target>` - Run this project's own `make <target>`, captured to build/build.out and posted to CHAT.md
- `bobp setup-agent-links` - Create `.claude/skills/` symlinks (run once on setup)

---

## Archived Documentation

Files prefixed with `.archive_` are historical and no longer active:
- `.archive_COMMANDS.md` - (Consolidated into HELP.md)
- `.archive_state_management_fix.md` - (Implemented in protocol)

---

## Documentation Standards

### File Naming
- Persona definitions: `[PersonaName]_[ROLE]_AGENT.md`
- State files: `state.md`
- MCP tools: `[toolname]_mcp.md`
- Templates: `_template_*.md`
- Archived: `.archive_*.md`

### Structure
- All persona docs in `agents/[persona]/`
- All MCP tool docs in `agents/tools/`
- Team communication in `agents/CHAT.md`
- Primary references in `agents/bob/`

### Maintenance
- Update `*help` when adding commands
- Update tool docs when changing MCPs
- Archive outdated docs with `.archive_` prefix
- Keep `agents/bob/HELP.md`, `STARTUP.md`, and `SHORTHAND_GUIDE.md` in sync with active skills and templates

---

## Quick Command Reference

```bash
*help                          # Show complete help (Bob)
*init                          # Initialize session & ready team (Bob)
*prep-clear                    # Checkpoint state before /clear (Active)
*plan epic <name>              # Strategic epic discovery & shaping
*plan story <slice>            # User story slicing & ADRs
*plan sprint                   # Sprint planning container & task board
*impl <task>                   # Feature TDD work-loop (Neo → Trin → Morpheus)
*fix <defect>                  # Defect diagnosis & surgical fix work-loop
*refactor <target>             # Behavior-preserving refactoring work-loop
*spike <topic>                 # Timeboxed disposable research spike
*uat <scope>                   # End-to-end acceptance & UX audit
*deploy <env>                  # Pipeline deployment & smoke test
*swe impl <task>               # Direct implementation (Neo)
*qa test <scope>               # Direct testing (Trin)
*lead arch <topic>             # Direct architecture guidance (Morpheus)
*ora ask <question>            # Query knowledge base (Oracle)
*sm status                     # Sprint progress & blockers (Mouse)
*pm story <request>            # User story requirements (Cypher)
*user review <scope>           # Usability & HCI review (Smith)
*devops deploy <env>           # Infrastructure & deployment (Tank)
```

---

**For Help:** Type `*help` or read `agents/bob/HELP.md`
