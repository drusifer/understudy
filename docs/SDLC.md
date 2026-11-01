# Understudy — SDLC

How this project is built, tested, changed and released — the source of truth for change
management across the whole project. **Owned by Tank**; to change anything here,
ask `@Tank *devops sdlc <what and why>` — the mechanism and this document change together.

## 1. Toolchain

| | Python (the only toolchain) |
|---|---|
| Runtime version | CPython 3.12.15 in `.python-version` |
| Manifest | `pyproject.toml` |
| Lockfile | `uv.lock` (committed) |
| Package manager | uv 0.13.0 |
| Local environment | `.venv/` (gitignored) |
| Test runner | `unittest` (built in) |
| Linter | ruff 0.9.10 (dev group) |
| Dependency audit | pip-audit 2.10.1 (dev group) |
| Browser check | Playwright for Python 1.64.1 (optional `browser` group; drives the system Chromium, downloads none) |

There is no Node: since Sprint 21 (ADR-0048) the repository has no `package.json`, eslint or `node:test`. The dashboard's browser files (`src/dashboard/page.html`, `page.js`, CSS, fonts) are plain files served as they are: no build, no lint, no test runner; what the page shows is decided in Python (`src/dashboard/server.py`) and tested there. The fonts are copied into `src/dashboard/fonts/` (SIL OFL).

Everything runs in the Python package `src/sketch` (ADR-0038, ADR-0045, ADR-0047): `python-statemachine`, DuckDB 1.5.6 (the
SQL a stage may run), `dateparser` 1.2.1 and `holidays` 0.107 (dates and business days), `iso18245` (MCC names),
`jinja2` 3.1.6 (sketches are templates), `ruamel.yaml` 0.19.1 (sketches are read as YAML 1.2, so `70:30` stays text),
`jsonschema` 4.26.0 (the sketch JSON Schema) and `typesafe-sdk` 0.7.5 for Jev, all pinned in `pyproject.toml` and
`uv.lock`; the capture cache lives in git-ignored `.understudy/`. SQLMesh and the MCP source servers were removed in
Sprint 20 when the household ETL became a sketch. `bin/understudy` is a shell script that starts the Python CLI; the dashboard server is standard-library `http.server` (no dependency). The run database is
opened by one process at a time. Private run output is refused under `data/` and any non-git-ignored
project path (UND-54 AC4).
Other required tools: `make`, `bobp` (agents run every target through `bobp make <target>`),
`gitleaks` on `PATH` for `make secrets` / `make check` and the pre-commit hook.

## 2. Setup

From a clean checkout:

```sh
bobp make install     # installs the locked uv environment
bobp make test        # Python unit tests; expect "OK"
bobp make hooks       # optional: gitleaks pre-commit hook
```

Nothing is installed globally.

## 3. Make targets

The Makefile is the only entry point; its recipes hold the commands. `bobp make help` lists them.

| Target | Runs | Notes |
|---|---|---|
| `install` | `install-py` | installs the exact lockfile; touches the network |
| `install-py` | `uv sync --locked` | exact Python lockfile install into `.venv`; touches the network on first setup |
| `lock` / `lock-py` | `uv lock --python 3.12.15` | updates `uv.lock` after a manifest change; touches the network |
| `test` | `test-py` | offline; no Jev or browser calls |
| `test-py` | `python -m unittest discover -s tests/python` | `ARGS="test_sketch*.py"` runs only the files matching that pattern |
| `run` | `bin/understudy $(ARGS)` (starts `python -m src.sketch.cli`) | e.g. `ARGS="run tests/fixtures/coffee/coffee_week.yaml --replay"`; a live run reads `TYPESAFE_API_KEY` from `.env` |
| `dashboard` | `bin/understudy dashboard $(ARGS)` | serves the read-only console over `build/runs` on 0.0.0.0:4180 (all interfaces, no login) |
| `lint` | `.venv/bin/ruff check src tests/python` | ruff 0.9.10 pinned in `pyproject.toml` (dev group); rule sets E, W, F, I, B, SIM, UP, N, C4, PERF, RUF, ERA, ARG, C90 (max complexity 12), PL, T20, RET, PTH, line length 135; test doubles and the CLI stdout are the only per-file ignores |
| `secrets` | `gitleaks git` over history + uncommitted tracked changes | needs `gitleaks` installed |
| `hooks` | `git config core.hooksPath .githooks` | installs the gitleaks pre-commit hook |
| `security-scan-python` | `uv export --locked --no-emit-project --no-hashes --all-groups` (dev and browser tools too) then `pip-audit --no-deps --disable-pip` over that file | audits the locked versions against the PyPI advisory database; any advisory fails; touches the network; pip-audit 2.10.1 is in the dev group |
| `security-scan` | `secrets` + `security-scan-python` | clean before a release and after any dependency change; not part of `check` because it needs the network |
| `install-browser` | `uv sync --locked --group browser` | adds the optional browser tools (`playwright`, `greenlet`, `pyee`); a later `install` removes them again; touches the network |
| `test-browser` | `python -m unittest discover -s tests/browser` with `CHROMIUM` (default `/usr/bin/chromium`) | drives the console in a real Chromium: rack, banner, live follow, start and stop, keyboard reach, and text contrast in all six theme and mode looks (UND-80); skipped with a reason when the group or Chromium is missing; not part of `check` |
| `check` | `test` + `lint` + `secrets` | the full gate |
| `push` | `check`, then `scripts/push.sh`: stage all → gitleaks scan of the staged files → commit with `MSG` → `git push --follow-tags origin <current branch>` | the only way changes are committed for publishing and pushed; `MSG="..."` required when anything is uncommitted; `ARGS="--dry-run"` commits nothing and previews; never `--force`; touches the network |
| `clean` | removes `build/`, `coverage/` | keeps the installed environment |
| `distclean` | `clean` + removes `.venv/` | used for the from-clean check |
| `help` | lists targets | parses `## comment` suffixes |

Standard targets deliberately absent:
- `format` — no formatter chosen; ruff's lint rules are the only style tool.
- `build` — nothing is bundled; understudy is used from a checkout.

## 4. Dependencies

- **Add or upgrade Python dependencies:** edit `pyproject.toml`, run `bobp make lock-py`, then `bobp make install-py`.
- **Commit afterwards:** `pyproject.toml` and `uv.lock` together.
- **Who:** Neo adds and bumps dependencies, in the story whose code first imports them. A
  different package manager, a runtime version change or a new language is a mechanism change — Tank's.
- Never hand-edit the lockfile.
- Declare only what the code imports. There is no JavaScript dependency: the page loads nothing from the internet, and
  its fonts (Cinzel, Spectral, VT323, DotGothic16, Antonio; OFL) are committed under `src/dashboard/fonts/`.

## 5. Quality gates

| Gate | Target | Required before |
|---|---|---|
| Tests | `bobp make test` | every handoff to Trin; sprint close |
| Lint | `make lint` | every handoff to Trin; sprint close |
| Live Jev runs | `bobp make run ARGS="run <sketch>"` with `TYPESAFE_API_KEY` | UAT only, one run with the owner's go-ahead (Sprint 19). `make test` never calls Jev: tests use a Jev double or `--replay` captures. |
| Secret scan | `make secrets` | every commit (pre-commit hook, if `make hooks` was run); sprint close |
| Security scan | `make security-scan` | a release; any change to `pyproject.toml` or `uv.lock`; sprint close when dependencies changed. An advisory is fixed (upgrade, swap, remove) or accepted by the owner with an expiry (`agents/skills/security/SKILL.md` section 4); never ignored with a flag |
| All of the above | `make check` | sprint close |

## 6. Change management

This document is the project's source of truth for how a change gets from request to done.
Where another document, skill or habit disagrees with it, this one wins — and the disagreement
is reported to Tank so one of them gets fixed.

### Change classes

| Class | Examples | Proposed by | Approved by | Must pass | Recorded in |
|---|---|---|---|---|---|
| Routine | feature, fix, refactor, docs, adding a dependency via section 4 | Cypher story / user request | Morpheus review (Bloop chain) | section 5 gates | `task.md`, commit |
| Mechanism | toolchain, manifest layout, make targets, gates, CI, this document | anyone, via `@Tank *devops sdlc` | Tank + user | from-clean rebuild + section 5 | this file, `agents/CHAT.md` |
| Release | a tagged commit on `main` | user | user | `make check` | git tag on `main`, `CHANGELOG.md` |
| Emergency | hotfix outside a sprint | user | user (may be after the fact) | `make test` at minimum | `agents/CHAT.md`, reviewed at next sprint close |

### Flow

1. **Request** — the user asks; Cypher/Mouse turn it into stories and tasks in `task.md`
   (Tier 1 or Tier 2 planning, see `agents/skills/sprint/SKILL.md`).
2. **Branch** — each sprint works on a `sprint-<N>` branch cut from `main` at Stage 0; it is
   merged into `main` at sprint close, after Cypher's launch. Fixes between sprints go on `main`.
3. **Implement** — through `make` targets only; tests accompany behaviour changes.
4. **Gate** — the section 5 gates pass locally before handoff.
5. **Review** — Trin verifies, Morpheus reviews; Smith gates stories.
6. **Integrate** — agents commit once per phase, after Morpheus's review passes (one commit per
   phase, message `Phase <N>: <summary>`, ending with the agent's attribution line). Outside a
   sprint, agents commit only when the user asks.
7. **Record** — `task.md`, `agents/CHAT.md`, and this file for mechanism changes.

### Rules

- Agents commit per reviewed phase (flow step 6); they never push, merge to `main` or tag
  without the user asking.
- Commit-and-publish is `bobp make push MSG="<message>"` only (never a bare `git commit` +
  `git push`): full gate, stage everything, secret-scan what is staged, commit, push the
  current branch with its annotated tags. Agents end `MSG` with their attribution lines.
  Moving a published tag still needs a manual `git push --force origin <tag>` by the owner -
  the target never forces.
- Never commit: secrets, `.env*`, `node_modules/`, `build/` (bobp output capture), `.via/`, `.mcp.json`,
  `.claude/settings.local.json`. The relative agent-discovery symlinks (`.agents`, `.claude/skills/`,
  `.cursorrules`) are committed.
- **Rollback:** `git revert` the offending commit and publish with `bobp make push`.
- **Changing this document:** only Tank edits it; every edit updates the Last verified line.

## 7. Versioning and release

- **Version lives in:** `version` in `pyproject.toml` (`0.1.0`).
- **Bumped:** only when the owner asks for a release (owner, 2026-10-15). Sprint closes do not
  bump the version on their own.
- **CLI entry point:** `bin/understudy` (a shell script over `python -m src.sketch.cli`).
- **Artifact:** None — not published; a release is a tag on `main`.

## 8. CI / deploy

None — everything runs locally on the dev Pi. A CI job, if added, must run
`bobp make install && bobp make check`, not raw tool commands.

## 9. Known deviations

- `gitleaks` is a system binary (`~/.local/bin/gitleaks`), not a Python dependency.
  `make secrets` fails with an install hint if it is missing.
- The dashboard's browser script (`page.js`) has no automated test and no linter (owner: JavaScript is fine in the
  dashboard, Sprint 21). A browser check is done by hand at UAT; page logic that matters lives in Python.
- Network targets: `install`, `lock`, `install-py`, `install-browser`, `lock-py` and `push`.
- The browser check is outside `check` on purpose: it needs a Chromium and the optional group, and takes about a minute. Run it
  after any change to `src/dashboard/` (Tank, owner decision pending on making it a release gate). Playwright's wheel bundles its
  own small Node driver (about 130 MB installed); it is a dev-only detail of that package, not a Node toolchain of this project
  (no `package.json`, no `npm`).

## 10. Conformance check

Run by Tank at sprint close (`*devops sdlc-check`):

1. `bobp make distclean && bobp make install && bobp make check` passes, and `bobp make test` made no network call
   to Jev and launched no browser (unit tests use a Jev double or `--replay` captures); `bobp make test-browser` is run
   separately when `src/dashboard/` changed.
2. `bobp make install` a second time leaves `uv.lock` unchanged (`git status` clean).
3. Every imported package is declared in `pyproject.toml` and `uv.lock`.
4. Every target in section 3 exists in the Makefile.
5. No doc or script tells people to install globally or bypass `make`; no Node file has come back.
6. `.venv/` and `build/` are ignored; runtime pins match the manifest.
7. This sprint's changes followed section 6: right class, right approval, recorded where it says.
8. Nothing under `src/` or `tests/` imports from `seed/`.

---
*Last verified: 2026-11-01 by Tank (Sprint 21 close: Node removed, Python-only; `bobp make check` green (lint, 233 tests, gitleaks); Makefile targets match section 3; no package.json, eslint, `.mjs` or lockfile other than `uv.lock` remains; the from-clean `distclean` → `install` run was not repeated this sprint because no dependency changed.)*
*Previous verification: 2026-10-30 by Tank (Sprint 19 close: distclean → install → check green; repeated install passed idempotently; Python manifest matches `pyproject.toml`/`uv.lock` including `ruamel.yaml` and `jsonschema`; the old Node player, its tests, the `test-browser`/`test-live`/`install-browser` targets and nine npm dependencies removed with the owner's decisions (one kind of sketch, old commands may break)).*
*Previous verification: 2026-10-17 by Tank (sprint-15 close: clean → check green, browser tests green;
no dependency or mechanism change. Sprint-14 close: clean → check green, browser tests green;
routine dependency `elkjs` per §4. Sprint-13 close: clean → check green; no dependency or
mechanism change. Sprint-12 close: clean → check green, browser tests green; no
dependency or mechanism change. Sprint-11 close: clean → check green, browser tests green; no
dependency or mechanism change. Sprint-10 close: clean → check green; routine dev dependency
`ajv` per §4. Sprint-9 close: clean → check, browser tests 7/7; routine
dependency `@fontsource/antonio` per §4. Sprint-8 close: clean → check, browser tests 6/6; no
mechanism change - the dashboard's request body cap is code, not tooling. Sprint-6 close: Routine
dependencies added per §4 (`@fontsource/*` fonts); eslint browser-globals block now also covers
`src/dashboard/page.mjs` (Mechanism, small, owner-approved with the sprint plan); `.factory/`
git-ignored. Sprint 5: `test-live` outcome checks and the full-house walk-away run).*
