# Understudy — SDLC

How this project is built, tested, changed and released — the source of truth for change
management across the whole project. **Owned by Tank**; to change anything here,
ask `@Tank *devops sdlc <what and why>` — the mechanism and this document change together.

## 1. Toolchain

| | JavaScript (Node ESM, `.mjs` sources) |
|---|---|
| Runtime version | Node 24 — `engines.node: ">=24"` in `package.json` and `.nvmrc` (`24`). Verified on v24.13.0. |
| Manifest | `package.json` (tasks in `scripts`) |
| Lockfile | `package-lock.json` (committed) |
| Package manager | npm (11.x) |
| Local environment | `node_modules/` (gitignored) |
| Test runner | `node:test` (built in, no dependency) |

Other required tools: `make`, `bobp` (agents run every target through `bobp make <target>`),
`gitleaks` on `PATH` for `make secrets` / `make check` and the pre-commit hook.

## 2. Setup

From a clean checkout:

```sh
make install     # npm ci (npm install only if the lockfile is missing)
make test        # expect "fail 0"
make hooks       # optional: gitleaks pre-commit hook
```

Nothing is installed globally. Run local tools with `npx`, never `npm install -g`.

## 3. Make targets

The Makefile is the only entry point; recipes call `package.json` scripts rather than
repeating their commands. `make help` lists them.

| Target | Runs | Notes |
|---|---|---|
| `install` | `npm ci` | exact lockfile install; idempotent; the only target that touches the network |
| `test` | `npm test -- $(ARGS)` → `node --test tests/*.test.js` | e.g. `ARGS="--test-name-pattern=seat"` |
| `lint` | `npm run lint` → eslint over `src/**/*.mjs`, `tests/**` | config `eslint.config.js` (recommended + unicorn + sonarjs, as in recard) |
| `secrets` | `gitleaks git` over history + uncommitted tracked changes | needs `gitleaks` installed |
| `hooks` | `git config core.hooksPath .githooks` | installs the gitleaks pre-commit hook |
| `check` | `test` + `lint` + `secrets` | the full gate |
| `clean` | removes `build/`, `coverage/`, `.eslintcache` | keeps `node_modules` |
| `distclean` | `clean` + removes `node_modules/` | used for the from-clean check |
| `help` | lists targets | parses `## comment` suffixes |

Standard targets deliberately absent:
- `format` — no formatter chosen; eslint is the only style tool (same as recard).
- `build` — nothing is bundled; recard consumes understudy as source via a git dependency.
- `run` — there is no CLI entry point yet (`bin/` does not exist). Added with the story that
  creates `bin/understudy.mjs`, together with `bin` in `package.json`.

## 4. Dependencies

- **Add a runtime dependency:** `npm install {pkg}`; **dev tool:** `npm install -D {pkg}`.
- **Upgrade / remove:** `npm install {pkg}@{version}` / `npm uninstall {pkg}`.
- **Commit afterwards:** `package.json` **and** `package-lock.json`, together.
- **Who:** Neo adds and bumps dependencies, in the story whose code first imports them. A
  different package manager, a Node version change or a new language is a mechanism change — Tank's.
- Never hand-edit the lockfile; never mix lockfiles from two package managers.
- Declare only what the code imports. Expected next, with recard's ranges:
  `@typesafe-ai/sdk ^0.6.0` (Jev — required), `playwright ^1.62.1` (web target),
  later `@modelcontextprotocol/sdk ^1.30.0`, `zod ^4.6.5`, `@xstate/graph ^3.0.4`.

## 5. Quality gates

| Gate | Target | Required before |
|---|---|---|
| Tests | `make test` | every handoff to Trin; sprint close |
| Lint | `make lint` | every handoff to Trin; sprint close |
| Live Jev runs | `make run ...` with `TYPESAFE_API_KEY` | UAT only; small runs with a step cap (owner, 2026-10-15). `make test` never calls Jev — it uses a judge test double. |
| Secret scan | `make secrets` | every commit (pre-commit hook, if `make hooks` was run); sprint close |
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
| Release | a commit recard pins as its git dependency | user | user | `make check` | git tag / commit hash in recard's `package.json` |
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
- Never commit: secrets, `.env*`, `node_modules/`, `build/` (bobp output capture), `.via/`, `.mcp.json`,
  `.claude/settings.local.json`. The relative agent-discovery symlinks (`.agents`, `.claude/skills/`,
  `.cursorrules`) are committed.
- **Rollback:** `git revert` the offending commit; recard stays pinned to the previous good commit.
- **Changing this document:** only Tank edits it; every edit updates the Last verified line.

## 7. Versioning and release

- **Version lives in:** `version` in `package.json` (`0.1.0`).
- **Bumped:** not yet decided — open question for the user (proposal: bump and tag at sprint close,
  which is what recard pins).
- **CLI entry points:** `bin` in `package.json` — none yet (see section 3).
- **Artifact:** None — not published to npm. recard consumes understudy as a git dependency.

## 8. CI / deploy

None — everything runs locally on the dev Pi. A CI job, if added, must run
`make install && make check`, not raw tool commands.

## 9. Known deviations

- `gitleaks` is a system binary (`~/.local/bin/gitleaks`), not an npm dependency — same as recard.
  `make secrets` fails with an install hint if it is missing.
- `seed/` holds non-running reference copies from recard; it is excluded from lint and tests
  until each file is generalized into `src/` (see `seed/README.md`).
- eslint rules turned off, all matching recard's config for the same reasons:
  `unicorn/filename-case` (camelCase files), `unicorn/no-null` (JSON-safe sentinel),
  `unicorn/consistent-class-member-order`, `unicorn/no-break-in-nested-loop`.
- The lint script passes `--no-error-on-unmatched-pattern` because `tests/**/*.mjs` is empty today.

## 10. Conformance check

Run by Tank at sprint close (`*devops sdlc-check`):

1. `make distclean && make install && make check` passes.
2. `make install` a second time leaves `package-lock.json` unchanged (`git status` clean).
3. Every imported package is in `dependencies`/`devDependencies`; only one lockfile exists.
4. Every target in section 3 exists and maps to a `package.json` script or a documented command.
5. No doc or script tells people to install globally or bypass `make`.
6. `node_modules/` and `build/` are ignored; `.nvmrc` and `engines.node` agree.
7. This sprint's changes followed section 6: right class, right approval, recorded where it says.
8. Nothing under `src/` or `tests/` imports from `seed/`.

---
*Last verified: 2026-10-15 against 66ce717 + uncommitted build-env files by Tank
(distclean → install → install → check, 46/46 tests). Branch/commit rules added 2026-10-15 (owner).*
