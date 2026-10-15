# Decisions

Newest first. Each record follows `agents/templates/_template_DECISION.md`, kept short.
Sprint 1 records were made by Morpheus in `docs/sprints/ARCH_SPRINT1.md` §8 (approved at
Smith Gate 2, 2026-10-15) and recorded here by Oracle at sprint close.

---

## ADR-0006: `make test` never calls Jev or launches Chromium

*   **Status**: Accepted · **Deciders**: Morpheus, Tank · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, SDLC §5
*   **Context**: Jev calls cost money and need a key; Chromium is slow and machine-dependent. The gate must be cheap and repeatable.
*   **Options**: (1) unit tests with a judge double and fake/real-process targets, live runs in a separate target; (2) live calls in `make test` behind an env flag.
*   **Decision**: (1). `runPart` takes `makeJudge`/`makeTarget`; the page target takes `launch`. Live runs live in `make test-live`.
*   **Consequences**: + fast, offline gate (93 tests). − the real SDK and Chromium are exercised only at UAT; a live regression is caught later.

## ADR-0005: Exit codes 0 / 1 / 2 for every command

*   **Status**: Accepted · **Deciders**: Morpheus, Smith · **Date**: 2026-10-15 · **Related**: UND-1..4
*   **Context**: Smith Gate 1 asked for consistent exit codes so scripts and people can tell failures apart.
*   **Decision**: 0 done; 1 the run started and could not finish (`RunError`, with an `outcome`); 2 refused before anything started (`UsageError`). Every failure is one `understudy: <message>` line, no stack trace.
*   **Consequences**: + one rule everywhere. − an internal bug also exits 1 (`unexpected error: ...`) — indistinguishable by code from a failed run.

## ADR-0004: An off-list answer is re-asked once, then the run stops

*   **Status**: Accepted · **Deciders**: Morpheus, Cypher · **Date**: 2026-10-15 · **Related**: UND-1 AC3
*   **Context**: recard silently played its fallback move when Jev chose something not offered. For a testing tool that hides a broken question or option list.
*   **Options**: (1) fallback and continue (recard); (2) re-ask once, then stop with exit 1; (3) stop at once.
*   **Decision**: (2). The step records `offList` and the raw answer; nothing off-list is ever sent to the app.
*   **Consequences**: + broken parts surface. − one extra Jev call per miss; recard's own tests that relied on silent fallback had to change (they now model Jev picking only offered options).

## ADR-0003: Generic `look` actor and `phase` guard

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, UND-5
*   **Context**: every recard game wrote its own `<game>_look` actor and `<game>_phase` guard.
*   **Decision**: one `look` (calls `adapter.app.phase(view)`) and one `phase` guard (`is:`). Also renamed: `TABLE`→`OBSERVE`, `table_changed`→`changed`, `quiet_table`→`quiet`, `ask_table`→`ask`, `services.peer/game`→`target/app`, option `card`→`value`.
*   **Consequences**: + both example parts are the same shape; adapters stay small (51 and 24 lines). − recard's turn files must be renamed when recard migrates (no back-compat shims, per recard's rule).

## ADR-0002: The web target drives a page hook, not the DOM

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-2
*   **Context**: a web adapter needs a view and moves. recard used `window.__recardHarness`.
*   **Options**: (1) a hook the page exposes (`window[hook]`, configurable); (2) generic DOM reading (buttons, text).
*   **Decision**: (1), default `__understudy`. The hook should only read the page and press what is on it.
*   **Consequences**: + exact views, tiny adapters. − the app must cooperate; a DOM mode for unmodified pages is backlog.

## ADR-0001: Target interface `view / act / talk / say / describe / exited / close`

*   **Status**: Accepted · **Deciders**: Morpheus · **Date**: 2026-10-15 · **Related**: UND-1, UND-2, extraction map
*   **Context**: the moved core already called recard's `peer` (`view/act/talk/say`); targets must be transport-neutral (web + CLI now, HTTP next).
*   **Options**: (1) keep the peer shape, add `describe/exited/close`; (2) an event-stream interface (push observations).
*   **Decision**: (1). The process target makes a terminal-like view (lines, echoed input, `seq`, `sent`, `exited`).
*   **Consequences**: + the core changed by renaming only. − a process target must buffer output and expose `seq`; adapters must guard against answering a question twice (`questions > sent`).
