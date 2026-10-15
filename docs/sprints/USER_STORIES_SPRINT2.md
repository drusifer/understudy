# Sprint 2 User Stories: Play a JSON API, and any web page without changing it

*   **Total Points**: 12 (Tier 1)
*   **Branch**: `sprint-2`
*   **Source**: owner, 2026-10-15, in chat: "for sprint 2 do the http player and ditch the special
    hook"; follow-up answers recorded in `agents/CHAT.md` and `docs/BACKLOG.md` (tiny in-repo JSON
    API example; built-in generic page adapter; no back-compat).
*   **Status**: Revised after Smith Gate 1 reject (FAIL: stalled runs) — awaiting re-review
*   **Order**: UND-6 → UND-7 → UND-8 (each leaves `understudy` usable)

## Goal

An automation author can point understudy at a third kind of app, a JSON API, and play it with the
same part format as the program and web examples. And a web page no longer has to be changed to
be played: understudy reads what a person would see on it and uses its controls, so the author
writes a part and at most a few lines of adapter. Together these make understudy useful against
apps the author does not control.

## Assumptions made for the owner

- The HTTP example is a tiny **vending machine API** in `examples/http/`: it shows its state, takes
  coins, and dispenses an item; the run ends when something has been bought.
- On a web page, the understudy uses what can be **chosen**: buttons, links, checkboxes, radio
  buttons and drop-down options. Typing free text into a field needs a source for the text and is
  left for a later sprint.
- "No back-compat" (owner rule): the page hook is removed, not kept as an option; the docs describe
  only the new way.

---

## STORY-UND-6: Play a JSON API
**Points:** 5
**Depends on:** none (the run loop, step log and checks from sprint 1)

**As an** automation author,
**I want** to point understudy at an HTTP JSON API and a part I wrote,
**so that** Jev exercises the service the way a client would, without me scripting each request.

### Acceptance Criteria
1. `understudy run examples/http` starts the example API, plays it until the part reaches its end
   state (an item bought), stops the API, and exits 0. Each step is one JSON line on stdout and
   in `build/runs/<adapter>/<timestamp>.jsonl`, in the same format as the other examples.
2. The HTTP part uses the same statechart vocabulary as the CLI and web parts; nothing in the part
   names the transport (no "request", "endpoint", "status code", "HTTP").
3. An adapter may name the URL of a service that is **already running** instead of a command to
   start; understudy then plays it without starting anything and leaves it running afterwards.
4. If the API does not answer within 10 seconds of starting, the run exits 1 naming the URL; a
   server understudy started is stopped.
5. If the server understudy started exits before the end state, the run exits 1 naming the command
   and its exit code (as for a program).
6. A move the API answers with an error status (4xx/5xx) is recorded in that step's log line with
   the status, and the run continues - an error answer is the app's behaviour, not a crash. A
   connection lost mid-run stops the run, exit 1, naming the URL.
7. `understudy check examples/http` passes without the key and without starting the API.
8. The example's adapter is under 150 lines.
9. If, after the first move, the API offers nothing for 10 seconds and the part has not ended, the
   run exits 1 with outcome `stalled`, naming the last state and what the API last showed; a
   server understudy started is stopped.

## STORY-UND-7: Play a web page without changing it
**Points:** 5
**Depends on:** none (independent of UND-6)

**As an** automation author,
**I want** understudy to play a web page using only what is on screen,
**so that** I can test pages I cannot or do not want to modify.

### Acceptance Criteria
1. `examples/web` contains no understudy-specific code in its page (`index.html`, `app.js`), and
   `understudy run examples/web` still plays it to the "Welcome aboard" end and exits 0.
2. A web adapter needs only a `name` and a `target`; when it gives no `app` hooks, the controls a
   person could choose on the page (buttons, links, checkboxes, radio buttons, drop-down options)
   are the moves on offer. `examples/web/adapter.mjs` is at most 10 lines and has no `app` hooks.
3. Jev sees the page's visible text and its choosable controls, and each step's log line names the
   control it used by its kind and visible label (for example `button:Pro (paid monthly)`), so a
   log reads without knowing the page's HTML.
4. A control that is hidden or disabled is never offered.
5. A page that still defines `window.__understudy` is played exactly like one that does not - the
   hook is ignored. No doc mentions it.
6. If no choosable control appears within 10 seconds of opening the page, the run exits 1 naming
   the URL and the page's visible text; the browser and the local server are closed.
7. `understudy check examples/web` passes without the key and without opening a browser.
8. If, after the first move, the page offers no choosable control for 10 seconds and the part has
   not ended, the run exits 1 with outcome `stalled`, naming the last state and the page's visible
   text; the browser and the local server are closed.

## STORY-UND-8: The docs teach the three targets and the hookless web page
**Points:** 2
**Depends on:** UND-6 and UND-7

**As a** developer adding a new app,
**I want** the guides and the reference to describe the HTTP target and hookless pages,
**so that** I can wire up an API or a web page from the docs alone.

### Acceptance Criteria
1. `docs/ADAPTERS.md` describes all three targets (program, web page, HTTP API) with their views
   and moves, and the generic web adapter; `docs/USER_GUIDE.md` and `docs/WALKTHROUGH.md` cover the
   HTTP example and the hookless web example with real run output.
2. `grep -rn "__understudy" docs README.md examples src` finds nothing.
3. The decision that replaces the page hook is recorded in `docs/DECISIONS.md`, and ADR-0002 is
   marked superseded by it.

---

## Out of Scope
- Typing free text into fields, logins, file uploads (needs a value source - later sprint).
- The MCP server (sprint 3).
- Playing a remote web page by URL; the web target serves a local example as in sprint 1.
- Any compatibility path for the old page hook (owner: no back-compat).
- Authentication headers or cookies for APIs beyond what the example needs.

## Open Questions
None. (Example domain, generic adapter and no back-compat were answered by the owner.)
