# Chat Message Template:

Agents **must** use this for every message posted to CHAT.md:


> ## [{msg_num}]: From: @{AgentName}, Subject: {Subject}
> 
> {TLDR(LastStep)};
> 
> ### Request: { An '@' or '*' targeted command  for a specic purpose like 'perform this task Y' or 'help me with X}

---

> **Previous sprint archived:** `agents/chat_archive/CHAT_SPRINT_1.md` (2026-10-15 14:39:27) — Sprint 1 (MVP first run): Tank built the npm/Makefile env and SDLC; Smith rejected then approved stories (step cap, failure ACs) and approved the architecture (target interface, page hook, generic look/phase, off-list re-ask, exit 0/1/2). Phases 0-7 each passed Trin UAT and Morpheus review: vocabulary, CLI, part check, run loop, process target + CLI example (live), page target + web example (live), ADAPTERS.md. Close: SDLC check green, 6 ADRs + 4 lessons, Smith found 3 minor defects (fixed), retro fed docs/BACKLOG.md, Cypher launched. Merge/tag await owner.

---

> **Previous sprint archived:** `agents/chat_archive/CHAT_SPRINT_2.md` (2026-10-15 18:36:41) — Sprint 2: owner asked for the HTTP player and to ditch the page hook (no back-compat), MCP deferred to sprint 3. Smith rejected stories once (no stall criterion), then approved stories and architecture (accessibility snapshot, generic page app, showing guard, one stall rule). Phases 1-5 passed UAT and review: groundwork, http target + vending example (live), aria page target, generic page app + unmodified web example (live), docs. Close: SDLC check green, 3 lessons, Smith found DEF-05/06 (required target fields) - fixed. Launched; merge awaits owner.

---

> **Previous sprint archived:** `agents/chat_archive/CHAT_SPRINT_3.md` (2026-10-15 22:02:15) — Sprint 3: owner shaped an MCP target (understudy as MCP client, SDK, mcpServers config inline or by reference, token headers) and one sketch.yaml as the only format; Cypher's stories rejected once by Smith (argument values, nothing-offerable), then approved with the architecture (ProgramTransport on program.mjs, generic MCP app, Jev chooses arguments). Plan revised once (loader + examples in one phase). Phases 1-4 passed UAT and review: sketch loader + converted examples, local MCP + box office (DEF-07: candidates from last non-error result), remote MCP + test-live (Tank), docs (SKETCHES.md, ADR-0011..0013). Close: SDLC check green, 3 lessons, Smith played a real server from .mcp.json and found DEF-09 (absolute config paths) - fixed. Launched; merge awaits owner.

---

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
