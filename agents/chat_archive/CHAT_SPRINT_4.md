# CHAT_SPRINT_4 — Sprint Archive

## Summary

Sprint 4: owner asked for a live view of the understudy; shaping settled a browser page, live + replay, pick + confidence, pause/step. Smith approved stories (control-enabled note) and architecture (cut-short log note): event-stream log via XState inspection, node:http + SSE server with own SVG layout (Mermaid rejected, 122 MB), pause gate before each move. Six phases passed UAT (real Chromium) and review; findings fixed: layout legibility (visual check), replay grain (frames per line), Ctrl-C while paused. Close: SDLC green, 3 lessons, Smith found DEF-12 (outcome doubled) - fixed. Launched; merge awaits owner.

---
[<small>2026-10-15 22:39:53</small>] [**User**]->[**all**] *decide*:
 Owner agrees: Jev chooses argument values, never writes them - understudy is constrained automation by design. Asks for a good example doc for using MCP services.

---
[<small>2026-10-15 22:42:15</small>] [**make**]->[**all**] *build*:
 Build PASSED | make check | /home/drusifer/Projects/understudy/build/build.out
10:42PM INF no leaks found
10:42PM INF 1 commits scanned.
10:42PM INF scanned ~825 bytes (825 bytes) in 235ms
10:42PM INF no leaks found

---
[<small>2026-10-15 22:42:20</small>] [**Oracle**]->[**all**] *done*:
 Added docs/MCP_GUIDE.md (owner request): existing .mcp.json -> finished run, via as the worked example; linked from README, USER_GUIDE, SKETCHES. Sketch in the guide verified with check. Committed on sprint-3.

---
[<small>2026-10-15 22:43:21</small>] [**User**]->[**all**] *request*:
 push main

---
[<small>2026-10-15 22:43:47</small>] [**make**]->[**all**] *build*:
 Build PASSED | make push | /home/drusifer/Projects/understudy/build/build.out
10:43PM INF 0 commits scanned.
10:43PM INF scanned ~0 bytes (0) in 238ms
10:43PM INF no leaks found
To github.com:drusifer/understudy.git
b020fc5..1dc029f  main -> main

---
[<small>2026-10-15 22:43:56</small>] [**Tank**]->[**all**] *done*:
 Sprint 3 merged to main (1dc029f, --no-ff) and pushed via bobp make push (gate green, no leaks). origin/main up to date. Branch sprint-3 fully merged.

---
[<small>2026-10-15 22:46:30</small>] [**User**]->[**all**] *request*:
 /sprint 4 UX - see what the understudy is doing: a UX that displays the state machine diagram and shows state changes and Jev decisions in real time. Any questions?

---
[<small>2026-10-15 22:46:30</small>] [**Cypher**]->[**all**] *shaping*:
 Shaping sprint 4 with the owner before writing stories; asking one question at a time (where the UX lives first).

---
[<small>2026-10-15 22:47:05</small>] [**User**]->[**all**] *decide*:
 Owner decided: the live view is a browser page - run --watch serves a local page (127.0.0.1) drawing the statechart, highlighting the current state, streaming Jev decisions.

---
[<small>2026-10-15 22:47:23</small>] [**User**]->[**all**] *decide*:
 Owner decided: live + replay - the same page follows run --watch live and replays a finished run from its log (understudy watch <log.jsonl>); the log gains state changes.

---
[<small>2026-10-15 22:47:56</small>] [**User**]->[**all**] *decide*:
 Owner decided: each decision shows options offered, the pick, confidence, chosen arguments and the app's answer - no full probability distribution.

---
[<small>2026-10-15 22:48:24</small>] [**User**]->[**all**] *decide*:
 Owner decided: pause and step live from the page (plus play/pause/step in replay). Shaping questions done; assumptions listed in BACKLOG Sprint 4.

---
[<small>2026-10-15 22:50:28</small>] [**User**]->[**all**] *request*:
 /sprint 4 go

---
[<small>2026-10-15 22:51:30</small>] [**Cypher**]->[**Smith**] *pm handoff*:
 Stories ready for user review: docs/sprints/USER_STORIES_SPRINT4.md - UND-13 log tells the whole story (3), UND-14 watch live (5), UND-15 pause/step (3), UND-16 replay (3), UND-17 docs (2). Self-check rubric STORIES: OUT=S TEST=S FAIL=A SCOPE=S SIZE=A DESIGN=A. @Smith *user review sprint-4

---
[<small>2026-10-15 22:51:45</small>] [**Smith**]->[**Morpheus**] *user approve*:
 *user approve. Stories approved. rubric STORIES: OUT=S TEST=S FAIL=A SCOPE=S SIZE=A DESIGN=A. Note folded into UND-15 AC1: only the applicable control is enabled, all disabled after the run ends. Watch for arch: idle looks must not flood the log (UND-13 AC3); a paused page must never make a Jev call (UND-15 AC3). @Morpheus *lead arch sprint

---
[<small>2026-10-15 22:53:20</small>] [**Morpheus**]->[**Smith**] *lead handoff*:
 Architecture complete: docs/sprints/ARCH_SPRINT4.md - log as event stream (start/state lines via XState inspect, idle looks folded); watch server (node:http + SSE, per-run token, 127.0.0.1) + own SVG layout (no mermaid: 122MB); pause gate before each move (no Jev call while paused). No new deps; eslint browser-globals block for Tank. ADR-0014..0016. rubric ARCH self: BOUND=A FLOW=S FAIL=A USER=A DECS=A FEAS=A. @Smith *user feedback arch sprint-4

---
[<small>2026-10-15 22:53:29</small>] [**Smith**]->[**Mouse**] *user approve*:
 *user approve. Architecture approved. rubric ARCH: BOUND=A FLOW=S FAIL=A USER=A DECS=A FEAS=A. Folded in: a log with no final line replays and says so. UX checks OK: one URL printed before the first move; labels read as words ('done: phase is asking'); no new flags beyond the stories. @Mouse *sm plan sprint

---
[<small>2026-10-15 22:54:03</small>] [**Mouse**]->[**Morpheus**] *sm handoff*:
 Sprint planned: task.md - 6 phases (event-stream log; graph+server; live page + --watch; pause/step; replay; docs) + close. Sprint 3 board archived. rubric PLAN self: SIZE=A GATE=A VERIF=A ALIGN=A OWNER=A. @Morpheus *lead review sprint plan

---
[<small>2026-10-15 22:54:10</small>] [**Morpheus**]->[**Neo**] *lead handoff*:
 Sprint plan approved. rubric PLAN: SIZE=A GATE=A VERIF=A ALIGN=A OWNER=A. Note: Phase 1 changes stdout, so tests reading step lines (examples, run, mcpRemote) must skip event lines in the same phase to keep the gate green. Phase 1 ready. @Neo *swe impl phase-1

---
[<small>2026-10-15 22:54:10</small>] [**Mouse**]->[**all**] *phase 1*:
 Phase 1: the log tells the whole story (UND-13)

---
[<small>2026-10-15 22:56:09</small>] [**make**]->[**all**] *build*:
 Build PASSED | make lint | /home/drusifer/Projects/understudy/build/build.out

> understudy@0.1.0 lint
> eslint --no-error-on-unmatched-pattern 'src/**/*.mjs' 'bin/**/*.mjs' 'examples/**/*.mjs' 'examples/**/*.js' 'tests/**/*.js' 'tests/**/*.mjs'


---
[<small>2026-10-15 22:56:16</small>] [**Neo**]->[**Trin**] *swe handoff*:
 Phase 1 impl complete: seat records transitions via XState inspect (idle looks folded into idle_looks), stream.mjs emits start/state/step/final to stdout+log+listeners, shared transitionLabel. Step/final fields unchanged (pinned by test). 168 pass, lint 0. @Trin *qa uat phase-1

---
[<small>2026-10-15 22:56:24</small>] [**make**]->[**all**] *build*:
 Build PASSED | make test-live | /home/drusifer/Projects/understudy/build/build.out
understudy: step 1 asking -> button:Free (1)
understudy: step 2 asking -> button:Light (0.9)
understudy: step 3 asking -> button:Accept (0.98)

---
[<small>2026-10-15 22:56:32</small>] [**Trin**]->[**Morpheus**] *qa handoff*:
 UAT phase 1 passed: test-live green x5; every log first line start, 10-14 state lines (>=1 per step), coffee-cli's waits folded (idle_looks 1 x4), step/final fields unchanged (test). @Morpheus *lead review phase-1

---
[<small>2026-10-15 22:56:33</small>] [**Morpheus**]->[**Neo**] *lead handoff*:
 Phase 1 review passed vs ADR-0014. Note: seat reads XState's _transitions (inspection microstep internals) - pinned by the run test's exact transition list, so an XState upgrade that changes it fails loudly. Committing. @Neo *swe impl phase-2

---
[<small>2026-10-15 22:56:33</small>] [**Mouse**]->[**all**] *phase 2*:
 Phase 2: graph layout and the watch server (UND-14 server side)

---
[<small>2026-10-15 23:00:26</small>] [**make**]->[**all**] *build*:
 Build PASSED | make lint | /home/drusifer/Projects/understudy/build/build.out

> understudy@0.1.0 lint
> eslint --no-error-on-unmatched-pattern 'src/**/*.mjs' 'bin/**/*.mjs' 'examples/**/*.mjs' 'examples/**/*.js' 'tests/**/*.js' 'tests/**/*.mjs'


---
[<small>2026-10-15 23:00:35</small>] [**Neo**]->[**Trin**] *swe handoff*:
 Phase 2 impl complete: turnGraph (turn -> labelled nodes/edges, all examples), layered SVG layout, watch server (127.0.0.1, token path, page files only, SSE history->live->end, replay end without final, control live-only, busy port UsageError). 176 pass, lint 0. @Trin *qa uat phase-2

---
[<small>2026-10-15 23:00:35</small>] [**Trin**]->[**Morpheus**] *qa handoff*:
 UAT phase 2 passed: tests cover graph/layout/server ACs. Visual check (layout rendered in Chromium) caught labels squeezed under boxes and back-edge labels colliding - fixed (gaps sized to labels, back edges arc over the top); re-rendered clean. Lesson candidate: look at a drawing, tests can't. @Morpheus *lead review phase-2

---
[<small>2026-10-15 23:00:35</small>] [**Morpheus**]->[**Neo**] *lead handoff*:
 Phase 2 review passed vs ADR-0015: no dependency, pure layout shared with the browser, server serves a whitelist only. Committing. @Neo *swe impl phase-3

---
[<small>2026-10-15 23:00:35</small>] [**Mouse**]->[**all**] *phase 3*:
 Phase 3: the live page and run --watch (UND-14)

---
[<small>2026-10-15 23:02:43</small>] [**make**]->[**all**] *build*:
 Build FAILED exit=2 | make lint | /home/drusifer/Projects/understudy/build/build.out

✖ 11 problems (11 errors, 0 warnings)
1 error and 0 warnings potentially fixable with the `--fix` option.


---
[<small>2026-10-15 23:02:50</small>] [**Tank**]->[**all**] *done*:
 Task 3.2 (Tank): eslint.config.js gives src/watch/page.mjs browser globals (document, globalThis), same shape as the examples/web block; no gate changed.

---
[<small>2026-10-15 23:05:20</small>] [**make**]->[**all**] *build*:
 Build PASSED | make test | /home/drusifer/Projects/understudy/build/build.out
✔ a busy port is refused before anything starts (5.381175ms)
ℹ tests 184
ℹ suites 0
ℹ pass 184
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5579.275302

---
[<small>2026-10-15 23:05:38</small>] [**Neo**]->[**Trin**] *swe handoff*:
 Phase 3 impl complete: page.html/css/mjs (SVG diagram, current state + last transition, decision feed, ending; no reconnect loop), run --watch [--port N] (server before judge/target, URL on stderr), ended line before a failed run's final line (arch amended), CLI options table. 184 pass, lint 0. @Trin *qa uat phase-3

---
[<small>2026-10-15 23:06:08</small>] [**Trin**]->[**Morpheus**] *qa handoff*:
 UAT phase 3 passed: Chromium drove the live page during real runs of mcp, web, http (cli in tests): highlight followed each state change within ~50 ms, reload after step 1 rebuilt history and kept following, feed rows show offered/pick+confidence/args/answer, ending 'done after N steps'; --watch output identical to plain (test); busy port refused before target (test); no Chromium left. @Morpheus *lead review phase-3

---
[<small>2026-10-15 23:06:08</small>] [**Morpheus**]->[**Neo**] *lead handoff*:
 Phase 3 review passed: page logic pure and tested, DOM thin; server before judge/target; 'ended' log line is a reviewed arch amendment (final fields untouched). Committing. @Neo *swe impl phase-4

---
[<small>2026-10-15 23:06:08</small>] [**Mouse**]->[**all**] *phase 4*:
 Phase 4: pause and step a live run (UND-15)

---
[<small>2026-10-15 23:09:29</small>] [**make**]->[**all**] *build*:
 Build PASSED | make lint | /home/drusifer/Projects/understudy/build/build.out

> understudy@0.1.0 lint
> eslint --no-error-on-unmatched-pattern 'src/**/*.mjs' 'bin/**/*.mjs' 'examples/**/*.mjs' 'examples/**/*.js' 'tests/**/*.js' 'tests/**/*.mjs'


---
[<small>2026-10-15 23:09:46</small>] [**Neo**]->[**Trin**] *swe handoff*:
 Phase 4 impl complete: gate.mjs (pause/step/resume/stop, paused time), run waits at the gate before each move (no Jev while paused; idle limits minus paused time), Ctrl-C while paused stops at once (interrupted, no move), control endpoint wired, page Pause/Step/Resume enabled per state, --pause (needs --watch). 194 pass, lint 0. @Trin *qa uat phase-4

---
[<small>2026-10-15 23:10:23</small>] [**Trin**]->[**Morpheus**] *qa handoff*:
 UAT phase 4 passed (live, Chromium): --pause -> 'paused before step 1' at choosing, Pause off / Step+Resume on; 12 s paused not stalled; Step x2 = exactly one move each; all controls off after done; Ctrl-C while paused -> exit 1 interrupted, 0 moves, page + log say 'stopped by Ctrl-C while paused'; no process left (2 matches were an unrelated 15-day-old devserver). Pause-from-running covered by gate/page tests (runs are ~1 s). @Morpheus *lead review phase-4

---
[<small>2026-10-15 23:10:23</small>] [**Morpheus**]->[**Neo**] *lead handoff*:
 Phase 4 review passed vs ADR-0016: gate before takeStep, no Jev while paused; stop() only short-circuits a paused run so --watch alone changes nothing. Committing. @Neo *swe impl phase-5

---
[<small>2026-10-15 23:10:23</small>] [**Mouse**]->[**all**] *phase 5*:
 Phase 5: replay a finished run (UND-16)

---
[<small>2026-10-15 23:12:37</small>] [**make**]->[**all**] *build*:
 Build PASSED | make lint | /home/drusifer/Projects/understudy/build/build.out

> understudy@0.1.0 lint
> eslint --no-error-on-unmatched-pattern 'src/**/*.mjs' 'bin/**/*.mjs' 'examples/**/*.mjs' 'examples/**/*.js' 'tests/**/*.js' 'tests/**/*.mjs'


---
[<small>2026-10-15 23:12:54</small>] [**Neo**]->[**Trin**] *swe handoff*:
 Phase 5 impl complete: replay.mjs (start line, JSON per line), understudy watch <log> [--port N] (until Ctrl-C), page replay mode (frames: start/each step/end; Play/Pause, Step back/forward, click a step; future steps faded; cut-short log said). 199 pass, lint 0. @Trin *qa uat phase-5

---
[<small>2026-10-15 23:13:57</small>] [**make**]->[**all**] *build*:
 Build PASSED | make lint | /home/drusifer/Projects/understudy/build/build.out

> understudy@0.1.0 lint
> eslint --no-error-on-unmatched-pattern 'src/**/*.mjs' 'bin/**/*.mjs' 'examples/**/*.mjs' 'examples/**/*.js' 'tests/**/*.js' 'tests/**/*.mjs'


---
[<small>2026-10-15 23:14:21</small>] [**Trin**]->[**Morpheus**] *qa handoff*:
 UAT phase 5 passed (Chromium, real MCP log): understudy watch <log> prints its address; Step forward/back walk each state change (finding fixed: frames were per step, so the diagram sat on 'waiting' - now one frame per line), click step 2 jumps there, Play runs to 'done after 3 steps', controls off at the bounds; Ctrl-C exit 0; sprint 3 style log (no start) exit 2; non-JSON file names line 1. @Morpheus *lead review phase-5

---
[<small>2026-10-15 23:14:21</small>] [**Morpheus**]->[**Neo**] *lead handoff*:
 Phase 5 review passed: replay is the live page fed the same events (ADR-0015); frames per line is a reviewed UX change, recorded in the UAT plan. Committing. @Neo *swe impl phase-6

---
[<small>2026-10-15 23:14:21</small>] [**Mouse**]->[**all**] *phase 6*:
 Phase 6: docs show how to watch (UND-17)

---
[<small>2026-10-15 23:15:45</small>] [**Neo**]->[**Trin**] *swe handoff*:
 Phase 6 impl complete (Neo+Oracle): USER_GUIDE §5 Watch a run (live, pause/step, replay, SSH), troubleshooting + command reference, SKETCHES §7 event lines, README opening + real screenshot docs/images/watch.png, ADR-0014..0016. @Trin *qa uat phase-6

---
[<small>2026-10-15 23:16:05</small>] [**make**]->[**all**] *build*:
 Build PASSED | make check | /home/drusifer/Projects/understudy/build/build.out
11:16PM INF no leaks found
11:16PM INF 1 commits scanned.
11:16PM INF scanned ~24398 bytes (24.40 KB) in 250ms
11:16PM INF no leaks found

---
[<small>2026-10-15 23:16:15</small>] [**Trin**]->[**Morpheus**] *qa handoff*:
 UAT phase 6 passed: image links resolve (README, USER_GUIDE), every documented command gives the documented line (--help, --pause/--port without --watch exit 2, run --watch prints address, watch <log> replays, Ctrl-C exit 0); bobp make check green 200/200. @Morpheus *lead review phase-6

---
[<small>2026-10-15 23:16:15</small>] [**Morpheus**]->[**Tank**] *lead handoff*:
 Phase 6 review passed: docs match code (event lines, controls, refusals); ADRs cite the Phase 2 and 5 findings. All phases reviewed. @Tank *devops sdlc-check

---
[<small>2026-10-15 23:16:37</small>] [**make**]->[**all**] *build*:
 Build PASSED | make check | /home/drusifer/Projects/understudy/build/build.out
11:16PM INF no leaks found
11:16PM INF 1 commits scanned.
11:16PM INF scanned ~15593 bytes (15.59 KB) in 243ms
11:16PM INF no leaks found

---
[<small>2026-10-15 23:16:43</small>] [**Tank**]->[**Oracle**] *devops handoff*:
 SDLC check passed: distclean -> install (manifest + lockfile unchanged) -> check green 200/200; imports in src/watch are node: built-ins only; eslint browser-globals block recorded. Last verified updated. @Oracle *ora groom

---
[<small>2026-10-15 23:17:19</small>] [**Oracle**]->[**Smith**] *ora handoff*:
 Docs groomed: UAT_PLAN_SPRINT4 (6 scenarios, 9 negative, DEF-10/11 resolved); 3 lessons (look at a drawing; replay at the user's grain; a new wait point needs its own exit). rubric SDLC: OWN=A FLOW=A GATE=S DEPS=S VERIFY=S. rubric DECISION (0014-0016): CTX=A OPT=A WHY=S CONS=A. @Smith *user test sprint-4

---
[<small>2026-10-15 23:18:25</small>] [**Smith**]->[**Trin**] *user bug*:
 *user bug CMD: run <web sketch without showing> --watch, let it stall | EXPECTED: 'stalled: nothing to do...' | ACTUAL: 'stalled: stalled: nothing to do...' | UX ISSUE: the page prefixes the outcome to a message that already starts with it. DEF-12 (minor). @Trin triage

---
[<small>2026-10-15 23:18:25</small>] [**Trin**]->[**Neo**] *qa triage*:
 DEF-12 triaged Minor: endingOf always prefixes outcome; the watchPage test even asserted the doubled text. Fix: prefix only when the message does not already start with '<outcome>:'. @Neo *swe fix DEF-12

---
[<small>2026-10-15 23:18:59</small>] [**make**]->[**all**] *build*:
 Build PASSED | make lint | /home/drusifer/Projects/understudy/build/build.out

> understudy@0.1.0 lint
> eslint --no-error-on-unmatched-pattern 'src/**/*.mjs' 'bin/**/*.mjs' 'examples/**/*.mjs' 'examples/**/*.js' 'tests/**/*.js' 'tests/**/*.mjs'


---
[<small>2026-10-15 23:19:18</small>] [**Smith**]->[**all**] *user approve*:
 User testing passed (DEF-12 fixed + retested). rubric UAT: COVER=S STEPS=A FAIL=S DATA=A EVID=S. Lessons x3: rubric LESSON: CTX=A ISSUE=S RULE=S REF=A. HCI notes (backlog): the stall message embeds the raw view JSON - long on the page; the decision feed could show Jev's reading state on demand. @all *sprint retro

---
[<small>2026-10-15 23:19:18</small>] [**Neo**]->[**Cypher**] *retro*:
 Neo retro: no dependency added; page logic pure and tested in Node, DOM thin. Friction: page.mjs is now the biggest file (~300 lines) - split model/DOM next time it grows. Backlog: none.

---
[<small>2026-10-15 23:19:18</small>] [**Trin**]->[**Cypher**] *retro*:
 Trin retro: 176 -> 200 tests; real-browser UAT scripts caught what unit tests could not (layout legibility, replay grain). Backlog: keep a Playwright UAT script in the repo (make target, Tank's call) instead of scratch files.

---
[<small>2026-10-15 23:19:18</small>] [**Morpheus**]->[**Cypher**] *retro*:
 Morpheus retro: ADR-0014..0016 held; one arch amendment (ended line). XState _transitions dependency is pinned by a test. Revisit: SSE reconnect when a page loses the stream mid-run (today: 'connection lost', reload).

---
[<small>2026-10-15 23:19:18</small>] [**Oracle**]->[**Cypher**] *retro*:
 Oracle retro: 3 lessons, two of them UX findings from looking at real output. Docs: screenshot is from a real run. Backlog: none.

---
[<small>2026-10-15 23:19:18</small>] [**Mouse**]->[**Cypher**] *retro*:
 Mouse retro: 6 phases, no plan revision needed, no anti-loop. 16 pts. Phase 3 (page) was the largest - fine at 3 tasks.

---
[<small>2026-10-15 23:19:19</small>] [**Cypher**]->[**Cypher**] *retro*:
 Cypher retro: stories held; one AC detail added at Gate 1 (enabled controls). Replay granularity was not specified - the AC said Step forward/back, which hid the grain question. Backlog: none new.

---
[<small>2026-10-15 23:19:19</small>] [**Smith**]->[**Cypher**] *retro*:
 Smith retro: pausing a running run and a failed run's display were only proven end to end - worth keeping in the UAT plan. Backlog: shorten the stall message's raw view on the page; show what Jev read for a step on demand.

---
[<small>2026-10-15 23:19:41</small>] [**Cypher**]->[**all**] *pm launch*:
 *pm launch sprint-4. Sprint complete: run --watch live page (statechart, current state, decisions), pause/step/resume, understudy watch <log> replay, log as event stream. 200 tests, no new dependency. Retro fed BACKLOG; CHANGELOG updated. Merge/push await owner.

