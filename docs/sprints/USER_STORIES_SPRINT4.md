# Sprint 4 User Stories: Watch the understudy live

*   **Total Points**: 16 (Tier 1)
*   **Branch**: `sprint-4`
*   **Source**: owner, 2026-10-15, in chat: "I want a way to see what the understudy is doing. Let's
    make a ux that displays the state machine diagram and shows the state changes and jev
    decisions in real time." Shaping answers recorded in `docs/BACKLOG.md` "Sprint 4" and
    `agents/CHAT.md`: a browser page; live and replay; decisions shown as pick + confidence;
    pause and step a live run from the page.
*   **Status**: Approved at Smith Gate 1 (2026-10-15), one note folded into UND-15 AC1
*   **Order**: UND-13 → UND-14 → UND-15 → UND-16 → UND-17 (each leaves `understudy` usable)

## Goal

An automation author can watch a stand-in think: a page in the browser shows the sketch's
statechart, lights up the state the understudy is in as it moves, and lists each Jev decision as
it is made - what was on offer, what Jev picked, how sure it was, and what the app answered. When a
sketch misbehaves, the author can pause the run before its next move and step through it, or open
a finished run's log and replay it. Today the only way to see this is reading JSON lines.

## Assumptions made for the owner

- **The picture is drawn from the sketch's own `turn:`** - every sketch gets a diagram with
  nothing extra to write. If the owner wants hand-made layouts, that is a later story.
- **Offline and local**: understudy serves the page and everything it needs itself (nothing is
  fetched from the internet), on `127.0.0.1` only, with no login. Watching from another machine
  means an SSH port forward.
- **The run log grows**: it gains a first line describing the sketch and its statechart, and a
  line per state change, so a replay needs only the log. Step lines and the final line keep every
  field they have today. Looks that change nothing (the understudy checking an app that has not
  moved) are counted, not listed, so an idle wait does not flood the log.
- **Watching never changes a run**: with `--watch` and no pause, the same steps, log and exit
  code as without it.
- **A paused run waits for the author**: the first-move and stall limits do not count while
  paused, and Ctrl-C still stops it. Closing the page does not resume it.

---

## STORY-UND-13: The log tells the whole story
**Points:** 3
**Depends on:** none

**As an** automation author,
**I want** a run's log to hold the sketch's statechart and every state change, not only the steps,
**so that** a finished run can be replayed and understood from its log alone.

### Acceptance Criteria
1. The first line of every run's log (and of stdout) describes the run: the sketch name, what it
   plays, and the statechart (states, initial state, transitions with their events and guards), e.g.
   `{"event":"start","sketch":"coffee-cli","plays":"node app.mjs","turn":{...}}`.
2. Each state change is one line, `{"event":"state","from":"looking","to":"answering","on":"phase is asking","at":"..."}`,
   in the order they happened, between the step lines.
3. A look that ends where it started without a move is not listed; the next listed line carries
   how many such looks happened before it (`"idle_looks": 12`), so a 30-second wait is one number,
   not hundreds of lines.
4. Step lines and the final line have exactly the fields they had in sprint 3; tools that read
   only those lines can skip any line that has an `event` field.
5. `bobp make test-live` still passes for all five examples, and each log starts with a `start`
   line and holds at least one `state` line per step.

## STORY-UND-14: Watch a run live in the browser
**Points:** 5
**Depends on:** UND-13

**As an** automation author,
**I want** `understudy run <sketch> --watch` to open a live view of the run,
**so that** I can see where the understudy is in its statechart and why it chose each move, as it
happens.

### Acceptance Criteria
1. `understudy run examples/cli --watch` prints `understudy: watch at http://127.0.0.1:<port>/...`
   on stderr before the first move; opening it shows the coffee sketch's statechart with every state
   and transition from its `turn:` labelled.
2. The state the understudy is in is highlighted, and the highlight moves within one second of
   each state change; the transition just taken is marked too.
3. Beside the diagram, a decision feed shows each step as it is made: step number, phase, the
   options offered, the pick and its confidence (`size:medium (0.95)`), any off-list retry, for an
   MCP move the chosen arguments (`film=f1, count=2`), and the app's answer (`status 402`, or the
   tool result's first line).
4. A page opened (or reloaded) mid-run shows everything so far, then follows live.
5. When the run ends the page says how (`done after 3 steps`, or the outcome and its message,
   e.g. `stalled: ...`) and keeps showing the run.
6. Without pausing, `--watch` changes nothing about the run: the same stdout lines, log and exit
   code as without it; the run does not wait for a page to be opened.
7. `--port N` picks the port; if it is taken the run refuses before starting anything, exit 2:
   `understudy: port N is in use - choose another with --port`. Without `--port` a free port is
   used.
8. The page needs no internet connection, and only this machine can open it (`127.0.0.1`).
9. `--watch` works for all four targets (`process`, `page`, `http`, `mcp`); for a web page the
   headless browser stays headless - the watch page is separate.

## STORY-UND-15: Pause and step a live run
**Points:** 3
**Depends on:** UND-14

**As an** automation author debugging a sketch,
**I want** to pause a watched run before its next move and release it one step at a time,
**so that** I can read each decision before the next one happens.

### Acceptance Criteria
1. The live page has **Pause**, **Step** and **Resume**. Pause stops the run before its next move
   (a move already being made finishes first); Step lets exactly one move happen, then it is paused
   again; Resume lets it run on. Only the button that applies is enabled (Pause while running;
   Step and Resume while paused), and all three are disabled once the run has ended (Smith Gate 1).
2. `understudy run <sketch> --watch --pause` starts paused before the first move; stderr says
   `understudy: paused - step or resume from the page, or Ctrl-C`.
3. While paused, the page shows `paused before step N` and the move the understudy is about to
   decide on is not yet asked of Jev - no Jev call is made while paused.
4. A run paused for longer than the first-move or stall limit (10 s) is not stopped for it; the
   limits count only time spent running.
5. Ctrl-C stops a paused run at once, as a stopped run (`interrupted`), closing its app; the page
   shows it.
6. `--pause` without `--watch` is refused, exit 2: `understudy: --pause needs --watch (the page is
   where you step it)`.

## STORY-UND-16: Replay a finished run
**Points:** 3
**Depends on:** UND-13, UND-14

**As an** automation author,
**I want** `understudy watch <log>` to replay a finished run on the same page,
**so that** I can study a run after it happened, or one someone sent me.

### Acceptance Criteria
1. `understudy watch build/runs/coffee-cli/<timestamp>.jsonl` prints the page's address and serves
   the same view, built from the log alone - no sketch, app, key or network needed.
2. Replay has **Play**, **Pause**, **Step back**, **Step forward**, and the decision feed's steps are
   clickable: clicking step 2 shows the diagram and the feed as they were at step 2.
3. The whole log is replayed, including how it ended (`done`, or the outcome and message).
4. A log from before sprint 4 (no `start` line) is refused, exit 2:
   `understudy: <log>: no start line - replay needs a log written by understudy run (sprint 4 or later)`.
   A file that is not a run log at all is refused naming the first line that is not JSON.
5. `understudy watch` stops with Ctrl-C, exit 0.

## STORY-UND-17: The docs show how to watch
**Points:** 2
**Depends on:** UND-13 to UND-16

**As a** user,
**I want** the guides to show the live view and replay,
**so that** I know it exists and how to use it, from the docs alone.

### Acceptance Criteria
1. `docs/USER_GUIDE.md` has a "Watch a run" section: `--watch`, `--port`, `--pause`, the page's
   parts, pause/step/resume, `understudy watch <log>`, and watching from another machine over SSH.
2. `docs/SKETCHES.md` §7 documents the `start` and `state` log lines and `idle_looks`.
3. `README.md` mentions the live view in its opening, with one screenshot of the page taken from a
   real run.
4. The decision to draw the statechart and serve the page from understudy itself is recorded in
   `docs/DECISIONS.md`.

---

## Out of Scope
- Showing Jev's full probability distribution (owner: pick + confidence is enough).
- Controlling a run in any other way than pause / step / resume (no choosing the move for Jev,
  no editing the sketch from the page).
- Watching from another machine without a port forward; logins; several people controlling one run.
- Opening the browser automatically (the machine running understudy may have no screen).
- Hand-made diagram layouts; nested statecharts (turns are flat).
- Watching several runs on one page.

## Open Questions
None - the owner answered where the view runs, live vs replay, the decision detail and controls.
