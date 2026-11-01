# UX gap review: what the console and the command line still lack

*   **By**: Smith (findings, run against the real software 2026-11-01) and Cypher (grouping and order)
*   **Feeds**: Sprint 22, the feature gap sprint. Not yet stories; Smith Gate 1 comes after the owner picks a direction (question at the end).
*   **Method**: ran `understudy` with good and bad arguments; opened the console in Chromium over the real household run (5,074 records, 1,876 events), over a failed run, an empty folder and a running run, at 1300 and 390 px wide; compared it with the approved design (`docs/design/DASHBOARD.md`) and the Sprint 21 stories.

## What works (keep)

Rack, printer, stage lamps and four gauges draw real data; live follow works; three themes and light/dark/auto work; no horizontal scroll at 390 px; empty and missing-run cases do not crash the page; bad `understudy` arguments exit 2 with a one-line message.

## Gaps, worst first

Each has the heuristic (H#, Nielsen) and one line of evidence.

| # | Gap | Evidence | Heuristic |
|---|---|---|---|
| G1 | **A failed run does not look failed.** The header lamp still says STANDING BY (amber), the reason is one log line among thousands, nothing says "this run failed at stage read: Jev needs a TypeSafe key". | failed-run screenshot: red `read` lamp and FAILED gauge only | H1, H9 |
| G2 | **The result of a run is invisible.** Outcome, mode (live/replay), `stale`, the files written and their row counts, and the `--with` values it ran with are in `run.json`, `summary.json` and the folder, but the console shows none of them. The question "what did it produce?" needs a terminal. | household run: 5 sinks, 5,074 records, shown nowhere | H1, H6 |
| G3 | **The tube hides the work.** One lamp per top-level stage; the household's 932 Jev reads and its child sketches (`readings.judge_payee[0].decide` ...) are only lines in the log. The approved design showed the statechart as a flow with the current state lit; the Python rebuild dropped it. No sense of progress inside a long stage. | 5 lamps for 937 stage events | H1, H2 |
| G4 | **No way to start, replay or stop a run from the console.** The design's core loop was "pick a sketch, set its inputs, press Play". Now it is `understudy run ... --with a=b` in a terminal and then a refresh. Sketches and their `--with` values are not listed anywhere. | owner decision 1 of Sprint 21 chose watch-only (assumption 1); gap is a real one if the console is meant for the owner's daily use | H3, H7 |
| G5 | **The printer cannot be searched or filtered.** 1,876 lines, no find, no "failures only", no filter by stage, no jump to the end or to a failure, no copy as text. | household run | H7, H8 |
| G6 | **Jev's part is a count.** The JEV gauge shows 932 requests; what was asked, what Jev answered (probabilities), which answers were low-confidence cannot be seen. This is exactly the owner's open question (1,706 records in review). | gauge only; captures sit in `.understudy/cache/` | H1, H6 |
| G7 | **Gauge needles use arbitrary full scales** (JEV full at 1,000 requests, ELAPSED full at 600 s). The text is real; the needle position is not a real fraction of anything the run knows. Breaks the owner's "gauges show real data" rule in spirit. | `gauges_of` constants | H2 |
| G8 | **The rack is a flat list of timestamps.** No grouping by sketch, no running badge on the tab, no outcome badge, no clean-up, no compare of two runs. | three tabs, all alike | H6, H7 |
| G9 | **The page cannot tell you it lost the server.** If the server stops, the page keeps showing the last data; no reconnect notice. The rack refreshes every 5 s with no stale marker. | code | H1 |
| G10 | **Header takes most of the first mobile screen** (theme and mode controls); the run is below the fold. | 390 px screenshot | H8 |
| G11 | **Command line:** (a) `dashboard` on a busy port prints a Python traceback, breaking the contract "never a traceback"; (b) `dashboard /nonexistent` starts quietly with no runs and no warning; (c) top-level `--help` lists `{run,check,dashboard}` with no descriptions and no examples; (d) `run` ends with `wrote <file>` but never prints the run id or how to watch it; (e) no `understudy runs` to list runs. | probes above | H5, H9, H10 |
| G12 | **No access control, listening on 0.0.0.0** (owner's choice). Not a usability defect; recorded because anyone on the network can open the console. | decision 4 | (Switch) |
| G13 | **Accessibility not verified.** Aria roles exist on rack, gauges and the printer; keyboard order, focus visibility, contrast in the three themes and screen-reader reading of the live log have not been tested. | none run | H4 |
| G14 | **`page.js` has no automated test.** Everything risky is in Python; DOM behaviour (follow, tab switching, theme memory) is only checked by hand. | ADR-0048 | (Trin) |

## Cypher's grouping and proposed order

**Theme A, trust the console (small, do first).** G1 failure banner and header lamp, G2 run summary panel (outcome, mode, stale, outputs with row counts, inputs), G9 stale/offline marker, G11 CLI fixes (a to e). All read data that already exists; no new event kinds. About 5 points.

**Theme B, see inside the run.** G3 nested stage tree with progress (collapsible by child sketch), G5 printer filter, search and jump-to-failure, G7 real needle scales (use the stage count and a per-run baseline, or drop the needle on JEV and ELAPSED), G8 rack badges and grouping. May add a `progress` fact to events. About 8 points.

**Theme C, see Jev's judgement.** G6 a Jev panel: question, options, probabilities, choice, flagged when below the review threshold, linked to the stage that asked. Reads the capture files; supports the household tuning work. About 5 points.

**Theme D, run it from the console.** G4: list sketches in a folder, show and set `--with` values, Play/Replay/Stop. Needs a decision on the console starting processes on a machine that listens on 0.0.0.0, so it needs Switch's design gate. About 8 points. **Owner question below.**

**Hygiene (any theme).** G10 mobile header, G13 accessibility pass, G14 a thin browser check (Playwright for Python, or none). About 3 points.

## Question for the owner

Should the console only **watch** runs (Themes A, B, C: about 18 points, safe on a network), or also **start** them (add Theme D, about 26 points, needs a login or a loopback-only start button)?
