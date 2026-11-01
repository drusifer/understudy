# Agent State

Keep this working-memory file current. Preserve exactly these three top-level sections; see the
State Management Protocol in `agents/skills/bob-protocol/SKILL.md` for entry and exit steps.

## Context
- **Recent decisions:** {decision and reason, or None}
- **Key findings:** {finding and why it matters, or None}
- **Important notes:** {relevant durable context, or None}

## Current Task
- **Status:** {Not started | In progress | Waiting | Complete}
- **Assigned to:** {persona}
- **Started:** {YYYY-MM-DD or N/A}
- **Description:** {one-sentence task, or No active task}
- **Progress:** {completed work and remaining work}
- **Blockers:** {blocker and needed action, or None}
- **Consultations:** {persona and outcome, or None}

## Next Steps
- **Immediate next action:** {one concrete action, or None}
- **Waiting on:** {person/event, or None}
- **Planned work:** {ordered actions, or None}

---
*Last updated: {YYYY-MM-DD}*

---
## Update 2026-11-01
Baseline review agents/switch/reviews/2026-11-01-console-and-run-pipeline.md: SEC-001 Medium open, SEC-002 accepted by owner until 2026-12-01, SEC-003 Low, SEC-004 Info; dependency audit not run. Next: threat-model UND-79 secret at Sprint 22 design gate.
