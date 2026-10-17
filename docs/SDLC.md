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
| `install` | `npm ci` | exact lockfile install; idempotent; touches the network |
| `install-browser` | `npx playwright install chromium` | needed only for web targets; touches the network; see §9 |
| `test` | `npm test -- $(ARGS)` → `node --test tests/*.test.js` | e.g. `ARGS="--test-name-pattern=seat"` |
| `test-browser` | `npm run test:browser` → `node --test tests/browser/*.test.js` (one file at a time) | the watch page driven in headless Chromium against real runs of the examples with a Jev double - no key, no cost; needs Chromium (`make install-browser`); `make test` stays browser-free (ADR-0006) |
| `test-live` | `understudy run <sketch> --steps 30` for every `examples/*/`, each run's final `outcome` checked (`done`), then `examples/evening` again with `BOX_STATE=full` (`walked-away`); serves the box office over HTTP with a throwaway token (`MCP_TOKEN`, `BOX_PORT`, default 8765) for `examples/mcp-remote` and stops it after | live Jev (paid) and, for web examples, Chromium; UAT only |
| `run` | `node bin/understudy.mjs $(ARGS)` | e.g. `ARGS="check examples/cli"` |
| `lint` | `npm run lint` → eslint over `src/**/*.mjs`, `tests/**` | config `eslint.config.js` (recommended + unicorn + sonarjs, as in recard) |
| `secrets` | `gitleaks git` over history + uncommitted tracked changes | needs `gitleaks` installed |
| `hooks` | `git config core.hooksPath .githooks` | installs the gitleaks pre-commit hook |
| `check` | `test` + `lint` + `secrets` | the full gate |
| `push` | `check`, then `scripts/push.sh`: stage all → gitleaks scan of the staged files → commit with `MSG` → `git push --follow-tags origin <current branch>` | the only way changes are committed for publishing and pushed; `MSG="..."` required when anything is uncommitted; `ARGS="--dry-run"` commits nothing and previews; never `--force`; touches the network |
| `clean` | removes `build/`, `coverage/`, `.eslintcache` | keeps `node_modules` |
| `distclean` | `clean` + removes `node_modules/` | used for the from-clean check |
| `help` | lists targets | parses `## comment` suffixes |

Standard targets deliberately absent:
- `format` — no formatter chosen; eslint is the only style tool (same as recard).
- `build` — nothing is bundled; understudy is used from a checkout (or as a git dependency).
- (`run` calls `bin/understudy.mjs`, which is also `bin.understudy` in `package.json`.)

## 4. Dependencies

- **Add a runtime dependency:** `npm install {pkg}`; **dev tool:** `npm install -D {pkg}`.
- **Upgrade / remove:** `npm install {pkg}@{version}` / `npm uninstall {pkg}`.
- **Commit afterwards:** `package.json` **and** `package-lock.json`, together.
- **Who:** Neo adds and bumps dependencies, in the story whose code first imports them. A
  different package manager, a Node version change or a new language is a mechanism change — Tank's.
- Never hand-edit the lockfile; never mix lockfiles from two package managers.
- Declare only what the code imports. Runtime today: `xstate`, `yaml`, `@typesafe-ai/sdk`
  (Jev), `playwright` (page target; locked at 1.62.1 so its Chromium download is shared with
  recard's), `@modelcontextprotocol/sdk` (mcp target client; the example server) and `zod` (the
  example server's tool schemas; the SDK's peer) - both added in sprint 3; `lru-cache` (a deciding sketch's answered calls,
  fixed size, least recently used forgotten) - added in sprint 5. `@fontsource/cinzel`, `@fontsource/spectral`,
  `@fontsource/vt323`, `@fontsource/dotgothic16` (the dashboard's fonts, OFL, served locally so the
  page fetches nothing from the internet) - added in sprint 6; `@fontsource/antonio` (the starship
  theme's lettering, OFL) - added in sprint 9. Dev: `ajv` (tests check `schema/sketch.schema.json`
  against the examples) - added in sprint 10. `elkjs` (the dashboard lays the statechart out as a
  layered flow, on the server) - added in sprint 14. Expected later:
  `@xstate/graph ^3.0.4`.

## 5. Quality gates

| Gate | Target | Required before |
|---|---|---|
| Tests | `make test` | every handoff to Trin; sprint close |
| Lint | `make lint` | every handoff to Trin; sprint close |
| Live Jev runs | `make test-live` with `TYPESAFE_API_KEY` | UAT only; small runs with a step cap (owner, 2026-10-15). `make test` never calls Jev — it uses a judge test double. |
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

- **Version lives in:** `version` in `package.json` (`0.1.0`).
- **Bumped:** only when the owner asks for a release (owner, 2026-10-15). Sprint closes do not
  bump the version on their own.
- **CLI entry points:** `bin.understudy` in `package.json` → `bin/understudy.mjs`.
- **Artifact:** None — not published to npm; a release is a tag on `main`.

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
- Playwright's Chromium is downloaded by `make install-browser` into Playwright's default
  `~/.cache/ms-playwright`, outside the project (same as recard): browsers are large and shared
  across projects. `make test` never launches it; only `test-live` and web runs do.
- Three targets touch the network: `install`, `install-browser` and `push`.
- The lint script passes `--no-error-on-unmatched-pattern` because `tests/**/*.mjs` is empty today.

## 10. Conformance check

Run by Tank at sprint close (`*devops sdlc-check`):

1. `make distclean && make install && make check` passes, and `make test` made no network call
   to Jev and launched no browser (unit tests use a judge double and fake targets).
2. `make install` a second time leaves `package-lock.json` unchanged (`git status` clean).
3. Every imported package is in `dependencies`/`devDependencies`; only one lockfile exists.
4. Every target in section 3 exists and maps to a `package.json` script or a documented command.
5. No doc or script tells people to install globally or bypass `make`.
6. `node_modules/` and `build/` are ignored; `.nvmrc` and `engines.node` agree.
7. This sprint's changes followed section 6: right class, right approval, recorded where it says.
8. Nothing under `src/` or `tests/` imports from `seed/`.

---
*Last verified: 2026-10-17 by Tank (sprint-14 close: clean → check green, browser tests green;
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
