# Owner decisions: Sprint 21

1. (2026-11-01) Sprint 21 takes epic slices C and D together: rebuild the dashboard and watch page in Python over `events.jsonl`, then delete the last Node (launcher, package.json, eslint, node:test). The epic closes with this sprint. Epic: `docs/sprints/EPIC_PYTHON_PORT.md`.
2. (2026-11-01) "It's okay to use JavaScript in the dashboard": the browser page stays plain JavaScript; Node tooling still goes (ADR-0048).
3. (2026-11-01) "Sprint till done" and "are you using Bob protocol?": the sprint runs through the personas and gates; the planning artifacts written after the build are noted in the retro.
4. (2026-11-01) "Remove the localhost hardcode and use 0.0.0.0": the console listens on every interface, no `--host` option, no login.
