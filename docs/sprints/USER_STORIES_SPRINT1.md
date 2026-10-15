# Sprint 1 User Stories: An understudy plays a part in two kinds of app

*   **Total Points**: 13 (Tier 1)
*   **Branch**: `sprint-1`
*   **Source**: Drew, 2026-10-15, recard chat log ("generalize the Jev and XState harness
    into a standalone automation tool") and recard `agents/morpheus/understudy_extraction_map.md`
    (decisions: web + CLI/HTTP targets, recard consumes via git dependency, Jev required).
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

An automation author can write a part for an understudy - a statechart in YAML plus the
questions Jev answers - and run it against a real app, with no code beyond a small adapter
that says what the app looks like and what moves it offers. Sprint 1 proves this works for
two very different apps, a web page and a command-line program, so the tool is shown to be
general rather than a card-game harness renamed. This is the foundation recard will later
move onto.

## Assumptions made for the owner

- Sprint 1 proves neutrality with **two** targets: a web page and a CLI program. HTTP is the
  third target and comes in a later sprint; the contract is designed so HTTP fits without
  changing it.
- Moving recard onto understudy is a **later sprint**. Sprint 1 copies recard's core modules
  into understudy (with their tests) but does not delete anything in recard.
- The two demo apps live in this repo under `examples/` and are tiny on purpose: a web page
  and a CLI that each offer a few moves and reach an end state.
- The command is `understudy` (installed bin), run from a checkout as `bobp make run ...`.

---

## STORY-UND-1: Run a part against a command-line program
**Points:** 5

**As an** automation author,
**I want** to point understudy at a command-line program and a part I wrote,
**so that** Jev plays the program the way a person would, without me scripting each input.

### Acceptance Criteria
1. Given the CLI example and its part (`examples/cli/part/`: `turn.yaml`, `questions.yaml`)
   and a valid TypeSafe key, when I run `understudy run examples/cli`, the actor reads the
   program's output, Jev picks one of the moves the adapter offers, the move is sent as
   input, and this repeats until the program reaches its end state; the command exits 0.
2. Every step is one JSON line on stdout (state seen, options offered, move picked, Jev's
   confidence) and one readable line on stderr; the same JSON lines land in
   `build/runs/<part>/<timestamp>.jsonl`.
3. Jev can only pick a move the adapter offered: an off-list answer is never sent to the
   program, and the step records the fallback that was used instead.
4. If the program exits unexpectedly, the run stops with a message naming the program and
   its exit code, and the command exits non-zero.

## STORY-UND-2: Run the same kind of part against a web page
**Points:** 3

**As an** automation author,
**I want** the same part format to drive a web page in a headless browser,
**so that** one tool and one way of writing parts covers my web apps too.

### Acceptance Criteria
1. Given the web example (`examples/web/`: a static page and its part), when I run
   `understudy run examples/web`, understudy serves the page, opens it in headless
   Chromium, and the actor plays it to its end state; the command exits 0.
2. The part files for the web example use the same statechart vocabulary as the CLI example;
   nothing in either part names the transport (browser, process).
3. Steps are logged exactly as in STORY-UND-1 AC2.
4. `--headed` is NOT offered; headless only (recard precedent, US-119).

## STORY-UND-3: A broken part is refused before anything runs
**Points:** 2

**As an** automation author,
**I want** mistakes in my part files caught at load with a clear message,
**so that** I fix them in seconds instead of watching a run fail halfway.

### Acceptance Criteria
1. A part that uses an unknown guard, action or actor name is refused before the app is
   started, with a message naming the file, the path inside it, the bad name and the nearest
   known name.
2. A question whose prose contains a literal value (a number or a quoted value outside
   backticks) is refused the same way, naming the question.
3. Refusals exit with code 2 and print no stack trace.
4. `understudy check <example>` runs the same load checks without starting the app or
   calling Jev, and exits 0 when the part is good.

## STORY-UND-4: Jev is required, and says so plainly
**Points:** 1

**As an** automation author,
**I want** a clear message when Jev can't be reached,
**so that** I know immediately that the run needs my TypeSafe key.

### Acceptance Criteria
1. `understudy run` with no TypeSafe key set exits 2 before starting the app, naming the
   environment variable to set.
2. `understudy check` does not need the key.

## STORY-UND-5: An adapter is small and documented
**Points:** 2

**As a** developer adding a new app,
**I want** one documented adapter shape with two working examples to copy,
**so that** I can wire up my own app (or recard) without reading understudy's internals.

### Acceptance Criteria
1. `docs/ADAPTERS.md` describes the adapter: what the target provides (look, act, and an
   optional talk channel) and what the app knowledge provides (what the state means, which
   moves are offered, what a move does), with the CLI and web examples as references.
2. Each example's adapter is under 150 lines.
3. `understudy library` lists every guard, action and actor name a part may use, each with
   its one-line meaning.

---

## Out of Scope
- HTTP targets (next sprint; the contract leaves room for them).
- Moving recard onto understudy, or deleting anything in recard.
- An MCP server for understudy (recard's `harnessServer.mjs` split is a later sprint).
- Multi-actor scenarios (several understudies in one run, recard's table/scenario file).
- Running without Jev (owner decision: Jev is required).
- Headed browser mode.

## Open Questions
1. Name of the TypeSafe key variable - recard uses the SDK default; assumed the same
   (`TYPESAFE_API_KEY`) until Morpheus confirms from the SDK.
