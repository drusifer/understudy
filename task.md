# Sprint 3 Task Board: One sketch file, and any MCP server as an app

*   **Goal**: every example is one `sketch.yaml` (code only in `hooks.mjs` where needed), and `understudy run examples/mcp` / `examples/mcp-remote` play an MCP server over stdio and over HTTP with a token, choosing tool arguments with Jev.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 15 (UND-9 5, UND-10 5, UND-11 3, UND-12 2)
*   **Branch**: `sprint-3`
*   **Stories / Arch**: `docs/sprints/USER_STORIES_SPRINT3.md`, `docs/sprints/ARCH_SPRINT3.md` (sprint 2 board: `docs/sprints/TASKS_SPRINT2.md`)
*   **Status**: Approved (Morpheus plan review, after one revision) — Phase 1 in progress
*   **Commits**: one local commit per phase after Morpheus's review (`Phase <N>: ...`); publishing only via `bobp make push` when the owner asks (SDLC §6). No back-compat (owner rule).

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` present; `sprint-3` cut from `main` (0b52a7e). No Tank Phase 0: ARCH §7 adds only ordinary dependencies (SDLC §4, Neo). The `test-live` recipe edit is Tank's, in Phase 3. (*Owner: Mouse*)

---

## Sprint Execution Phases

### Phase 1: Sketch loader and the three examples converted — UND-9
*Phase goal: `sketch.yaml` is loaded and checked as a whole; check/library/run take a sketch; the old layout is refused; cli, web and http are sketches and play live as in sprint 2. (Loader and conversion share a phase so the gate is green at the commit - Morpheus plan review.)*
- [x] **Task 1.1:** `src/sketch.mjs` replaces `part.mjs` (find dir-or-file, top-level keys, target fields per kind, `app: hooks.mjs` loading + hook checks, `steps`, `player`, questions under `questions.`, old-layout refusal); `parseTurn(config, ...)` with `turn.` paths; `cli.mjs`/`run.mjs` wording, `steps` precedence, log dir by sketch name. Tests ported from `part.test.js` to `sketch.test.js` on fixture sketches. TDD. (*Owner: Neo | Verification: `bobp make test ARGS="tests/sketch.test.js"` green*)
- [x] **Task 1.2:** `examples/{cli,web,http}/sketch.yaml` (+ `hooks.mjs` for cli/http); delete `adapter.mjs` and `part/`; `tests/examples.test.js` on sketches. (*Owner: Neo | Verification: `bobp make test` fail 0; `bobp make lint`; `check examples/<each>` exit 0*)
- [x] **Task 1.3:** UAT UND-9 AC1–7 (each refusal exit 2; check line for dir and file; `--steps` beats `steps:`; `bobp make test-live` green on 3 examples, same log fields) then Morpheus review vs ARCH §3/§5. (*Owner: Trin → Morpheus | Verification: `bobp make test-live` + `bobp make check`; commit `Phase 1`*)

### Phase 2: Local MCP target, generic MCP app, argument filling, box office — UND-10
*Phase goal: `understudy run examples/mcp` plays the box office over stdio to a ticket with no understudy code in the example.*
- [x] **Task 2.1:** `npm install @modelcontextprotocol/sdk zod` (SDLC §4); confirm `shared/stdio.js` exports (ARCH §9 risk); `src/mcpConfig.mjs` (inline / `config:`+`server:`, shape checks, `${VAR}`/`${VAR:-d}`), `program.mjs` stderr tail, `src/targets/mcpTransport.mjs`, `src/targets/mcp.mjs` (stdio path: handshake 10 s, view, act, errors as answers, close). Tests against the example server over stdio. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 2.2:** `src/fill.mjs`, `src/apps/mcp.mjs` (calls/values, not-offered line once, `idle`), `library.play` second request + off-list rule, `run.checkIdle` uses `app.idle`; `examples/mcp/` (`server.mjs` stdio + `--http`, `sketch.yaml` inline, test that the end text is in no tool description). Tests with a Jev double. (*Owner: Neo | Verification: `bobp make test`; `bobp make run ARGS="check examples/mcp"` exit 0*)
- [x] **Task 2.3:** UAT UND-10 AC1–9 (live `run examples/mcp --steps 20` exit 0; not-offered line; tool error logged; server exits early → exit 1 with code; unset `${VAR}` → exit 2) then Morpheus review vs ADR-0012/0013. (*Owner: Trin → Morpheus | Verification: live run + `bobp make check`; commit `Phase 2`*)

### Phase 3: Remote MCP over HTTP — UND-11
*Phase goal: a running box office behind a URL and a token is played and left running.*
- [x] **Task 3.1:** `mcp.mjs` HTTP path (streamable HTTP + headers, 10 s connect retry, refused status, client-only close); `examples/mcp-remote/` (`sketch.yaml` by reference, `servers.json`, `README.md`); token-never-printed test. (*Owner: Neo | Verification: `bobp make test`*)
- [x] **Task 3.2:** `make test-live` starts the example server in HTTP mode with a throwaway token for `examples/mcp-remote`, stops it after; SDLC Last verified updated. (*Owner: Tank | Verification: `bobp make test-live` green, 5 examples*)
- [x] **Task 3.3:** UAT UND-11 AC1–5 (wrong token → exit 1 with 401, no token in output; nothing at URL → exit 1 ≤ 10 s; server left running) then Morpheus review. (*Owner: Trin → Morpheus | Verification: live + `bobp make check`; commit `Phase 3`*)

### Phase 4: Docs — UND-12
*Phase goal: the docs teach sketches and four targets only.*
- [x] **Task 4.1:** `docs/SKETCHES.md` replaces `docs/ADAPTERS.md`; `README.md`, `docs/USER_GUIDE.md`, `docs/WALKTHROUGH.md` (MCP with real output); ADR-0011..0013 (Oracle records; supersede notes). (*Owner: Neo + Oracle | Verification: UND-12 AC3 grep empty*)
- [x] **Task 4.2:** UAT: cold-read "write a sketch for my MCP server" from docs alone; every documented command runs; then Morpheus review. (*Owner: Trin → Morpheus | Verification: inspection + each command; commit `Phase 4`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Verification: `bobp make distclean && bobp make install && bobp make check`*)
- [ ] **Task C.2:** Groom, lessons, UAT plan `docs/sprints/UAT_PLAN_SPRINT3.md`, chat report `SPRINT_3`. (*Owner: Oracle | Verification: `bobp chat-report --moniker SPRINT_3`*)
- [ ] **Task C.3:** End-to-end user test vs the UAT plan. (*Owner: Smith | Verification: `bobp chat "*user approve"`*)
- [ ] **Task C.4:** Retro → backlog. (*Owner: All | Verification: retros in CHAT.md*)
- [ ] **Task C.5:** Launch; merge / push / version only when the owner says. (*Owner: Cypher | Verification: `bobp chat "*pm launch"`*)
