# Oracle State

## Context
- Doc map lives in README.md "Documentation" table; keep it current when docs are added.
- All user-facing commands are written as `bobp make ...` (owner: "USE BOBP"); team updates via `bobp chat`.
- agents/DOCUMENTATION_INDEX.md is Bob Protocol scaffolding - not understudy's index; left for Bob.
- Root AGENT.md/AGENTS.md/CHATGPT.md/GEMINI.md are symlinks made by `bobp setup-agent-links` - not orphans.
- Tag v0.1.0 is on 766a47c (sprint 1).
- Chat archives: agents/chat_archive/CHAT_sprint-*.md; latest CHAT_sprint-10-15.md.
- Screenshots: docs/images/dashboard*.png - six theme x mode looks at 1600x960 (idle evening) and
  dashboard-tube.png (the evening played to the end with a Jev double: flow, gauges, paper). Shot
  with scratch headless scripts that start their own dashboard (folder: 'examples', not a copy -
  the box office needs the project's node_modules). README shows dashboard-tube.png.

## Current Task
2026-10-17 groom done (owner request, after sprint 15): README dashboard paragraph current (flow,
STEP, gauges, latch, light/dark); all seven screenshots re-shot; PROJECT.md status to sprint 15;
task.md says between sprints; chat for sprints 10-15 archived. Committed on main, not pushed.

## Next Steps
- Next sprint close: groom, ADRs/lessons, `bobp chat-report --moniker sprint-<N>`.
- Re-shoot docs/images when the console's look changes (see Context).
