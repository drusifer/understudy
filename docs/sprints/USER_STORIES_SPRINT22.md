# Sprint 22 User Stories: the console you can trust, see into, and start runs from

*   **Planning Size** (optional): 29 points
*   **Branch**: `sprint-22`
*   **Source**: Owner, 2026-11-01 (`OWNER_DECISIONS_SPRINT22.md` 1); gaps G1-G14 in `UX_GAPS_SPRINT22.md`; old criteria carried over from `OLD_VERSION_PARITY.md`.
*   **Status**: Draft, revised to the template after the owner asked whether the templates were used; awaiting Smith Gate 1 again (the earlier approval used the retired A/S/W rubric line and is void)

## Goal

When this sprint is done, the owner can open the console and see at once whether a run worked and what it produced, look inside a long run and into Jev's judgements, and start, replay or stop a run without a terminal. Starting a run is possible only for someone who holds the access secret, because the console is reachable from the whole network. It matters now because the household pipeline is the owner's daily work and today every question about a run needs a terminal.

**Order.** UND-76 first (the others read its summary). UND-77 and UND-78 are independent after UND-76. UND-79 waits for Switch's security design gate, then needs UND-76. UND-80 last.

## Assumptions made for the owner

1. "Start a run" means the console runs `understudy run` on the machine the console is on, for a sketch in a folder the owner names; it never runs anything outside that folder.
2. Starting, stopping and replaying need a secret shown when the console starts; watching stays open to the network (Sprint 21 decision 4). Switch may change this at the design gate.
3. A gauge needle shows only a fraction the run itself knows (stages done of total, failed of total). Requests to Jev and elapsed time show a figure without a needle.
4. Statechart diagram, stepping, replay of a log, decision detail and the YAML editor are not in this sprint; they are Sprints 23 and 24 (`OLD_VERSION_PARITY.md`).

---

## STORY-UND-76: A run says how it went
**Points:** 5

**As the** owner,
**I want** the console to say plainly whether a run is going, done or failed and what it produced,
**so that** I never read a log to find out.

### Acceptance Criteria
1. The header lamp and word read RUNNING, DONE or FAILED for the chosen run; STANDING BY appears only when no run is chosen.
2. A failed run shows a banner above the printer naming the stage and the reason (for example `read: Jev needs a TypeSafe key`); choosing the banner scrolls the printer to that line.
3. A run that ended says how in one line: `done after N stages`, or the outcome and its message.
4. A summary shows the outcome, whether the run was live or replayed, whether it is stale, how long it took, the `--with` values it had, and each output file with its row count.
5. When the console cannot reach its server the page says "disconnected, retrying", marks the data on screen as stale, and recovers by itself when the server returns.
6. At 390 px wide the run's status is visible without scrolling past the theme and mode controls.
7. A run whose files are missing or unreadable shows "no details for this run" and its id; it does not break the page or the other runs.

## STORY-UND-77: See inside a run
**Points:** 8

**As the** owner,
**I want** to see child sketches and nested stages, find a line in the log, and tell runs apart,
**so that** a run with nearly two thousand lines is navigable.

### Acceptance Criteria
1. Top-level stages show their child stages as groups (for example `readings.judge_payee` and `named.name_merchant`), each with a count and a state; opening a group lists its stages.
2. While a run is going, the stage in progress is lit and its group shows how many iterations are done.
3. The printer has a text filter, a "failures only" switch, a stage filter, and jumps to the start, the first failure and the end; lines that arrive while a filter is on are filtered too.
4. A filter that matches nothing says "no lines match" and offers to clear it.
5. Gauge needles read only fractions the run knows; the figures for Jev requests and elapsed time show without a needle.
6. Each rack tab carries a running or failed badge; tabs are grouped by sketch with the newest run of each first.

## STORY-UND-78: See Jev's judgements
**Points:** 5

**As the** owner,
**I want** to see what Jev was asked and what it answered,
**so that** I can tune the records that land in review without reading cache files.

### Acceptance Criteria
1. A Jev list shows each request of the run: the stage that asked, the question, each option with its probability, and the choice made.
2. A request whose top option is below the review threshold, or whose choice was `none_of_these`, is flagged, and the list can be filtered to those.
3. For a replayed run the list shows the answers it replayed; for a run that never asked Jev it shows a plain note saying so.
4. Two gauges show Jev's confidence in its last choice and how many answers were asked as against reused.
5. If a run's captured answers are missing, the list says which are missing and the rest of the console still works.

## STORY-UND-79: Start, replay and stop a run from the console
**Points:** 8

**As the** owner,
**I want** to pick a sketch, set its inputs and press Play,
**so that** I do not need a terminal for a daily run.

### Acceptance Criteria
1. A list of sketches shows each sketch in the folder given to the console, with its description and the `--with` names it takes.
2. A sketch that fails `check` is listed greyed out with its check message and cannot be started.
3. A folder with no sketches, or a path that is not a folder, is refused before the console starts, with one message that says what to fix.
4. Choosing a sketch shows a field for each `--with` name; a name that must be a file is checked to exist before Play is allowed.
5. Play starts the run; it appears in the rack at once and is followed live. Stop ends it and the run is marked stopped.
6. Replay lists the captured runs the sketch can replay and runs from the chosen one.
7. A run that cannot start (no key, a missing file) says why on the page; when any run ends the controls unlock and the outcome shows.
8. Starting, stopping and replaying work only for someone who has the access secret shown when the console started; without it the console still watches and the controls say why they are off. The secret is not in the address bar and not in any log.
9. A sketch outside the chosen folder, or any extra argument, is refused with a message.
10. A second Play for a sketch that is already running says "already running" and offers to open that run.

## STORY-UND-80: The command line and the page keep their promises
**Points:** 3

**As the** owner,
**I want** every failure to be one plain line and every control reachable by keyboard,
**so that** I can recover from mistakes and use the console without a mouse.

### Acceptance Criteria
1. `understudy dashboard` on a busy port prints one `understudy: <message>` line and exits 2, with no traceback.
2. `understudy --help` describes each command with an example; `understudy run` ends by printing the run id and how to watch it.
3. `understudy runs` lists the runs under the runs folder, newest first, with their state.
4. Every control on the page is reachable and usable with the keyboard alone, shows where focus is, and has an accessible name and value.
5. Text meets a contrast ratio of 4.5:1 in each of the three themes in light and dark, or the exception is recorded in the UAT plan with the owner's acceptance.
6. Rack switching, live following, the failed-run banner, and start and stop each have a repeatable browser check, written down in the UAT plan.

---

## Out of Scope
- The statechart diagram, pause and step, replay of a finished run's story, decision detail, the YAML editor and typed inputs: Sprints 23 and 24 (`OLD_VERSION_PARITY.md`).
- Logging in with a name and password, or more than one user: one shared secret is enough for one owner.
- Starting runs from another computer's sketches: only the folder on this machine.
- Changing what `events.jsonl` records: this sprint reads what is already there.

## Open Questions
1. Should the secret be asked once per browser (remembered) or on every start? Smith and Switch answer at the design gate; assumed once per browser until then.
2. Which review threshold marks a Jev answer as low confidence? Assumed to be the household's own (0.7); the owner can overturn.
