# Changelog

## Sprint 1 — MVP first run (2026-10-15, merged to `main` at 766a47c, tag `v0.1.0`)

First release of understudy: Jev-driven stand-ins that play real apps.

- `understudy run <dir> [--steps N]` plays an example's part against its app with live Jev:
  one JSON line per step on stdout and in `build/runs/<adapter>/<ts>.jsonl`, a final
  outcome line, a step cap (default 50), Ctrl-C stops at a safe state.
- Two targets: a command-line **process** and a web **page** (headless Chromium, driven
  through the page's `window.__understudy` hook).
- `understudy check <dir>` refuses broken parts before anything starts, naming file, path,
  bad name and the nearest known one; `understudy library [<dir>]` lists every name.
- Examples: `examples/cli` (coffee counter) and `examples/web` (sign-up wizard).
- Exit codes 0 done / 1 failed after starting / 2 refused before starting.
- Core (statechart parts, Jev decisions, seat) moved from recard d817d3c and generalized.
- Docs: `docs/ADAPTERS.md`, `docs/DECISIONS.md`, `docs/SDLC.md`.
