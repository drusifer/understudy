# Sprint 22 User Stories: the console you can trust, see into, and start runs from

*   **Total Points**: 29 (Tier 1: new surface that starts processes)
*   **Branch**: `sprint-22`
*   **Source**: Owner, 2026-11-01 (`OWNER_DECISIONS_SPRINT22.md` 1); gaps G1-G14 in `UX_GAPS_SPRINT22.md`.
*   **Status**: Smith Gate 1: approved with notes (2026-11-01), notes applied

## Goal

The owner can open the console, see at once whether a run worked and what it produced, look inside a long run and into Jev's judgements, and start, replay or stop a run without a terminal, with nothing on the network able to start a run unless it has the secret.

**Order.** UND-76 first (everything else reads its summary). UND-77 and UND-78 are independent after 76. UND-79 needs Switch's design gate, then 76. UND-80 last.

## Assumptions made for the owner

1. "Start a run" means the console launches `understudy run` as a child process on the machine it runs on, with `--with` values the sketch declares. It never runs anything the sketch folder does not contain.
2. Access control is a secret token printed when the dashboard starts and required (cookie after first use) for every start, stop and replay; watching stays open (decision 4 of Sprint 21). Switch may change this at the design gate.
3. Needle positions use only quantities the run knows (stages done of total, failed of total). JEV and ELAPSED become figures without a needle.

---

## STORY-UND-76: A run says how it went
**Points:** 5 (gaps G1, G2, G9, G10)

**As the** owner, **I want** the console to say plainly whether a run is running, finished, or failed and what it produced, **so that** I never read a log to find out.

**Acceptance criteria**
1. The header lamp and word show RUNNING, DONE or FAILED for the chosen run, not STANDING BY.
2. A failed run shows a banner naming the stage and the reason (`read: Jev needs a TypeSafe key`) above the printer; the printer jumps to that line when the banner is clicked.
2a. When a run ends, the page says how in one line: `done after N stages`, or the outcome and message (old UND-14 AC5).
3. A summary panel shows outcome, mode (live or replay), stale, duration, the `--with` values the run had, and each output file with its row count.
4. If the server cannot be reached, the page says "disconnected, retrying" and keeps the last data marked stale; it recovers by itself.
5. At 390 px wide the run's status is visible without scrolling past the theme controls (they collapse into one menu).

## STORY-UND-77: See inside a run
**Points:** 8 (G3, G5, G7, G8)

**As the** owner, **I want** to see child sketches and nested stages, find a line in the log, and tell runs apart, **so that** a 1,876-line run is navigable.

**Acceptance criteria**
1. The tube shows top-level stages with their children (`readings.judge_payee`, `named.name_merchant`) collapsed into groups with a count and a state; opening a group lists its stages.
2. While a run is going, the lamp of the stage in progress is lit and its group shows how many iterations are done.
3. The printer has a text filter, a "failures only" toggle, a stage filter, and jump to start, failure and end; filtering does not stop live lines arriving.
4. Gauge needles read only real fractions; JEV and ELAPSED show their figure without a needle.
5. Rack tabs carry a running or failed badge and group by sketch; the newest run of each is first.

## STORY-UND-78: See Jev's judgements
**Points:** 5 (G6)

**As the** owner, **I want** to see what Jev was asked and what it answered, **so that** I can tune the 1,706 low-confidence records without reading cache files.

**Acceptance criteria**
1. A Jev panel lists each request of the run: the stage that asked, the question, each option with its probability, and the choice made.
2. Requests where the top option is below the review threshold, or `none_of_these` won, are flagged and can be filtered to.
3. The panel works for a replayed run (reads the capture it replayed) and shows nothing, with a plain note, for a run without Jev.
4. Private values (merchant names, amounts) are shown only on the owner's own machine; the panel reads capture files already on disk and adds nothing to what is stored.

## STORY-UND-79: Start, replay and stop a run from the console
**Points:** 8 (G4, G12)

**As the** owner, **I want** to pick a sketch, set its inputs and press Play, **so that** I do not need a terminal for a daily run.

**Acceptance criteria**
1. A "Sketches" list shows the sketches under a folder given to `understudy dashboard` (`--sketches DIR`, default `examples`), each with its description and its `--with` names.
1a. A sketch that fails `check` is listed greyed out with its check message and cannot be started; a folder with no sketches, or a path that is not a folder, is refused before the server starts (old UND-27).
1b. A run that cannot start (no `TYPESAFE_API_KEY`, missing file) says why on the page, and when any run ends the controls unlock and show the outcome (old UND-29).
2. Choosing one shows a form for its `--with` values (file paths checked to exist) and Play, Replay (offers captured runs) and Check.
3. Play starts `understudy run` as a child process; the new run appears at once in the rack and is followed live; Stop ends the process and the run is marked stopped.
4. Starting, stopping and replaying need the access token printed at startup; without it the console still watches, and the Play controls say why they are off. The token is never in the page's URL or logs.
5. Only sketches inside `--sketches DIR` can be started; a path outside it, or an extra argument, is refused with a message (tested).
6. Only one run per sketch at a time; a second Play says "already running" and offers to open it.

## STORY-UND-80: The command line and the page match the contract
**Points:** 3 (G11, G13, G14)

**Acceptance criteria**
1. `understudy dashboard` on a busy port or a missing folder prints one `understudy: <message>` line and exits 2; no traceback.
2. `understudy --help` describes each command with an example; `understudy run` ends by printing the run id and `understudy dashboard` as the way to watch it; `understudy runs` lists runs.
3. A keyboard-only pass and a contrast check of the three themes in light and dark are recorded in the UAT plan with the fixes made.
4. A thin browser check (Playwright for Python in the dev group, or a documented manual script) covers: rack switch, live follow, failed-run banner, start and stop.
