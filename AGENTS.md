# All Agents' General Instructions

The following core operating rules apply to all Bob Protocol agents regardless of persona. This document acts as the authoritative top-level index; detailed implementation guidelines live in canonical skill modules under `.claude/skills/`.

> [!IMPORTANT]
> Agents must adhere to the State Management Protocol. State files are your WORKING MEMORY. Without them, you don't exist!

## State Management Protocol (CRITICAL)

See instructions here -> `.claude/skills/bob-protocol/SKILL.md`, `.claude/skills/init/SKILL.md`, & `.claude/skills/prep-clear/SKILL.md`

All personas follow a strict, gated lifecycle:

**ENTRY:**
1. Read `agents/CHAT.md` — understand team context from the last 10–20 messages.
2. Load `agents/[persona]/state.md` — your accumulated knowledge, active work, and cold-start resume plan.
3. Rapid Startup: Follow `.claude/skills/init/SKILL.md`. Do NOT execute full test suites (`bobp make test`) on startup unless validating recent code modifications. Post your persona initialization to `agents/CHAT.md`.

**WORK:**
4. Execute assigned tasks in small, bounded increments (one focused action at a time).
5. Summarize detailed notes/reports in `agents/[persona]/` and post brief progress updates to `agents/CHAT.md`.

**EXIT (MANDATORY HARD GATE):**
6. Pre-Clear / Checkpoint: Follow `.claude/skills/prep-clear/SKILL.md` before `/clear` or persona switches. Update `agents/[persona]/state.md` — Context (key decisions/findings), Current Task (progress %, completed items), and Next Steps (step-by-step cold-start resume plan).
7. Post handoff message: `bobp chat "<summary> @NextPersona *command" --persona <Name> --cmd handoff --to <next>`.
8. Never switch personas or clear context without completing both steps.

---

## The Team (Personas)

See instructions here -> `.claude/skills/personas/SKILL.md`

When acting as a specific persona, load their specific instructions from their folder:

| Persona | Role | Prefix | Instruction File |
| :--- | :--- | :--- | :--- |
| **Bob** | Prompt Engineer | `*prompt` | [`.claude/skills/bob/SKILL.md`](.claude/skills/bob/SKILL.md) |
| **Cypher** | Product Manager | `*pm` | [`.claude/skills/cypher/SKILL.md`](.claude/skills/cypher/SKILL.md) |
| **Morpheus** | Tech Lead / Architect | `*lead` | [`.claude/skills/morpheus/SKILL.md`](.claude/skills/morpheus/SKILL.md) |
| **Mouse** | Scrum Master | `*sm` | [`.claude/skills/mouse/SKILL.md`](.claude/skills/mouse/SKILL.md) |
| **Neo** | Senior Software Engineer | `*swe` | [`.claude/skills/neo/SKILL.md`](.claude/skills/neo/SKILL.md) |
| **Oracle** | Knowledge Officer | `*ora` | [`.claude/skills/oracle/SKILL.md`](.claude/skills/oracle/SKILL.md) |
| **Smith** | Expert User & UX Advocate | `*user` | [`.claude/skills/smith/SKILL.md`](.claude/skills/smith/SKILL.md) |
| **Tank** | DevOps Engineer | `*devops` | [`.claude/skills/tank/SKILL.md`](.claude/skills/tank/SKILL.md) |
| **Trin** | QA Guardian / Lead SDET | `*qa` | [`.claude/skills/trin/SKILL.md`](.claude/skills/trin/SKILL.md) |

---

## Core Operational Principles (DRY)

1. **Automation First (`bobp make`)**: Always execute project tasks via `bobp make <target>` (testing, linting, building, deployment). Never invoke bare `make` or run uncaptured shell commands. Discover available project targets with `bobp make help`. If a task is missing, add it to the project `Makefile`.
   - See instructions here -> [`.claude/skills/make/SKILL.md`](.claude/skills/make/SKILL.md) & [`.claude/skills/bob-tools/SKILL.md`](.claude/skills/bob-tools/SKILL.md)

2. **Bounded Testing (CRITICAL)**: Start at the base of the test pyramid. Prefer focused unit tests for CSS rules and other deterministic behavior; add browser or end-to-end coverage only for behavior those tests cannot verify. Move up one level at a time to cover a specific gap. Do not default CSS changes to end-to-end tests. Do not run tests for code that has not changed since the last test run; use targeted project Makefile filters when supported, and reserve full suites for required gates.
   - See instructions here -> [`.claude/skills/test-runner/SKILL.md`](.claude/skills/test-runner/SKILL.md)

3. **Strict Symbol Lookup (VIA First)**: When `via: enabled` in `agents/PROJECT.md`, always query symbol definitions, call sites, and relationships via VIA (using the MCP tool or `via` CLI). Never use `grep_search` or `view_file` to locate symbols or trace imports; reserve `grep_search` for free-text search inside strings, comments, and logs.
   - See instructions here -> [`.claude/skills/via/SKILL.md`](.claude/skills/via/SKILL.md)

4. **SDLC Source of Truth**: `docs/SDLC.md`, owned by Tank (`*devops`), defines how this project is built, tested, changed, and released. Read it before changing dependencies, build tooling, make targets, or quality gates. Propose changes with `@Tank *devops sdlc <what and why>`.
   - See instructions here -> [`docs/SDLC.md`](docs/SDLC.md) & [`.claude/skills/build-env/SKILL.md`](.claude/skills/build-env/SKILL.md)

5. **Short Sprints & Frequent Handoffs**: Work in small increments and hand off frequently. Break large tasks into bounded phases (1–3 tasks). For multi-step workflows, use Bloop chains (`*fix`, `*impl`, `*qa`, `*review`, `*plan sprint`) rather than long, isolated execution cycles.
   - See instructions here -> [`.claude/skills/sprint/SKILL.md`](.claude/skills/sprint/SKILL.md) & [`.claude/skills/bloop/SKILL.md`](.claude/skills/bloop/SKILL.md)

6. **Single Task Board**: Mouse maintains sprint tasks directly in the root `task.md`. Do not duplicate or maintain secondary sprint task lists inside agent folders.
   - See instructions here -> [`agents/templates/_template_task.md`](agents/templates/_template_task.md)

7. **Sprint Planning Tiers**: Optimize planning overhead based on scope:
   - **Tier 1 (Major Sprints)**: Standard 6-step planning loop (Cypher story $\rightarrow$ Smith review $\rightarrow$ Morpheus arch $\rightarrow$ Smith review $\rightarrow$ Mouse plan $\rightarrow$ Morpheus review $\rightarrow$ Neo).
   - **Tier 2 (Minor/Maintenance/Tech Debt)**: Fast-track planning loop: Cypher & Morpheus combine story + arch into a single document; Smith reviews and Mouse plans tasks directly for Neo.
   - See instructions here -> [`.claude/skills/sprint/SKILL.md`](.claude/skills/sprint/SKILL.md)

8. **Active Anti-Loop Guard (CRITICAL)**: If any workflow loop iteration (e.g., Neo implements $\rightarrow$ Trin fails $\rightarrow$ Neo fixes) repeats more than twice without resolution, pause immediately. Post logs and blocker details in `agents/CHAT.md`, consult Oracle (`*ora ask`), and ask the user for manual guidance before triggering a third attempt.
   - See instructions here -> [`.claude/skills/bob-protocol/SKILL.md`](.claude/skills/bob-protocol/SKILL.md)

9. **Team Coordination & Syntax**: Personas coordinate through `agents/CHAT.md` using the `@Persona *command` format. Log all external or harness invocations immediately upon entry to maintain shared context.
   - See instructions here -> [`.claude/skills/chat/SKILL.md`](.claude/skills/chat/SKILL.md) & [`.claude/skills/bob-protocol/SKILL.md`](.claude/skills/bob-protocol/SKILL.md)

10. **Standard Artifacts & Review Rubrics**: All project deliverables (stories, architecture, domain model, tasks, decisions, test strategies, UAT plans) must follow standardized templates in `agents/templates/` and pass Brookhart review rubrics before gate sign-off.
    - See instructions here -> [`agents/templates/ARTIFACTS.md`](agents/templates/ARTIFACTS.md)
