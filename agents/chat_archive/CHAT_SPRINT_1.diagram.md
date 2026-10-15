# CHAT_SPRINT_1 — Sprint Archive

## Summary

Sprint 1 (MVP first run): Tank built the npm/Makefile env and SDLC; Smith rejected then approved stories (step cap, failure ACs) and approved the architecture (target interface, page hook, generic look/phase, off-list re-ask, exit 0/1/2). Phases 0-7 each passed Trin UAT and Morpheus review: vocabulary, CLI, part check, run loop, process target + CLI example (live), page target + web example (live), ADAPTERS.md. Close: SDLC check green, 6 ADRs + 4 lessons, Smith found 3 minor defects (fixed), retro fed docs/BACKLOG.md, Cypher launched. Merge/tag await owner.

---

## Planning

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Mouse
    participant Tank
    participant Smith
    participant Cypher
    participant Morpheus
    Note over User,Morpheus: 📅 2026-10-15
    User->>All: "request"
    Note right of User: "make it so - plan<br/>Understudy sprint 1 from<br/>recard's extraction map<br/>(recard: agents/morpheus<br/>/understudy_extraction_m<br/>ap.md). Decisions: web<br/>+…"
    Mouse->>Tank: "handoff"
    Note right of Mouse: "Files moved in from<br/>recard d817d3c: src/<br/>(escalate, decide,<br/>strategyFile, machine,<br/>seat, shutdown, library,<br/>table) + 7 tests<br/>(imports -> ..…"
    User->>All: "request"
    Note right of User: "/init"
    Tank->>All: "resume"
    Note right of Tank: "Resuming *devops build-<br/>env from last session<br/>(Mouse handoff):<br/>package.json, Makefile,<br/>docs/SDLC.md, then run<br/>the 7 copied tests."
    Tank->>All: "decide"
    Note right of Tank: "Build-env decision: npm<br/>+ package.json +<br/>package-lock (no<br/>lockfile exists,<br/>ecosystem default,<br/>matches recard). Node<br/>pinned >=24 via engines…"
    Tank->>Smith: "handoff"
    Note right of Tank: "build-env done<br/>(uncommitted):<br/>npm+lockfile, Node>=24,<br/>Makefile front door,<br/>make check =<br/>test+lint+secrets all<br/>green, 7 copied test<br/>files pa…"
    User->>All: "request"
    Note right of User: "/sprint mvp first run"
    User->>All: "decide"
    Note right of User: "Owner answers: scope as<br/>drafted (13 pts), work<br/>on sprint-1 branch,<br/>merge at close, agents<br/>commit per reviewed<br/>phase, never push<br/>(build-env…"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject rubric<br/>STORIES: OUT=S TEST=A<br/>FAIL=W SCOPE=A SIZE=W<br/>DESIGN=A. REASON: UND-2<br/>no failure AC, UND-1 can<br/>run forever (no step<br/>cap),…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories revised: step<br/>cap (50, --steps), off-<br/>list = re-ask once then<br/>stop exit 1, UND-2<br/>failure ACs (no Chromium<br/>-> exit 2 + install<br/>hint,…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. rubric<br/>STORIES: OUT=S TEST=S<br/>FAIL=S SCOPE=A SIZE=S<br/>DESIGN=A. Notes:<br/>install-browser is a new<br/>make target (Tank), keep<br/>exit c…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Architecture complete: d<br/>ocs/sprints/ARCH_SPRINT1<br/>.md. Target interface vi<br/>ew/act/talk/say/describe<br/>/close (process + page),<br/>adapter.mjs + part…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve. rubric<br/>ARCH: BOUND=S FLOW=S<br/>FAIL=S USER=A DECS=S<br/>FEAS=S. Notes: specify<br/>check success line,<br/>library listing format,<br/>log path…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: task.md,<br/>Phase 0 (Tank:<br/>run/install-<br/>browser/test-live<br/>targets) + phases 1-7,<br/>one Neo task each + Trin<br/>UAT + Morpheus review…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "rubric PLAN: SIZE=A<br/>GATE=S VERIF=S ALIGN=S<br/>OWNER=A. Approved. Note:<br/>Task 1.1 is the heaviest<br/>Neo task - keep the off-<br/>list change test-first…"
```

---

## Phase 0

Phase 0: make targets run/install-browser/test-live + SDLC update

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Tank
    participant Neo
    Note over Tank,Neo: 📅 2026-10-15
    Tank->>Neo: "devops handoff"
    Note right of Tank: "Phase 0 done (commit).<br/>run/install-<br/>browser/test-live<br/>targets, SDLC<br/>§3/§5/§9/§10 updated,<br/>make check green. @Neo<br/>*swe impl phase-1"
```

---

## Phase 1

Phase 1: generic vocabulary + look/phase + off-list re-ask

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl complete:<br/>vocabulary renamed (targ<br/>et/app/OBSERVE/changed/q<br/>uiet/ask), look+phase<br/>added, off-list re-ask<br/>(ADR-U4) with RunError,…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed: no<br/>old names left in<br/>src/tests, library keys<br/>match ARCH §5, off-list<br/>twice sends nothing<br/>(tests/library.test.js).<br/>51/51…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed<br/>(ARCH §5, ADR-U3/U4 met,<br/>renames separate from<br/>off-list logic in<br/>tests). Committed. @Neo<br/>*swe impl phase-2"
```

---

## Phase 2

Phase 2: understudy command, key check, library listing

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl complete:<br/>bin/understudy.mjs +<br/>src/cli.mjs<br/>(run/check/library,<br/>--steps, exit 0/1/2, no<br/>stacks), key check<br/>before start, librar…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2 passed:<br/>UND-4 AC1 (unset + blank<br/>key -> exit 2 exact<br/>message, real bin too),<br/>AC2 (check needs no<br/>key), UND-5 AC3 listing<br/>groupe…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed<br/>(ADR-U5 consistent,<br/>commands injectable so<br/>tests never start apps).<br/>Committed. @Neo *swe<br/>impl phase-3"
```

---

## Phase 3

Phase 3: part loader and understudy check

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 3 impl complete:<br/>src/part.mjs (adapter<br/>shape, questions types +<br/>literal/quoted-value<br/>check, turn via<br/>parseTurn with<br/>generic+adapter l…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed via<br/>real CLI: unknown actor<br/>-><br/>file/path/name/nearest,<br/>exit 2, no stack, no key<br/>needed. Found+fixed:<br/>paths outside cwd s…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 3 review passed<br/>(services object filled<br/>at run time keeps check<br/>side-effect free).<br/>Committed. @Neo *swe<br/>impl phase-4"
```

---

## Phase 4

Phase 4: the run loop with test doubles

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 4 impl complete:<br/>src/run.mjs (runPart: ke<br/>y->part->judge->target-<br/>>seat loop, step cap,<br/>10s first move, app-<br/>exited, Jev error wrap,<br/>Ctr…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 4 passed:<br/>UND-1 AC2-5 vs fakes -<br/>log == stdout lines,<br/>final line on all 7<br/>outcomes, nothing sent<br/>on off-list, target<br/>closed every…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 4 review passed vs<br/>ARCH §4/§6. Debt noted:<br/>second Ctrl-C closes<br/>target but message is<br/>whatever error follows<br/>(backlog). Committed.<br/>@N…"
```

---

## Phase 5

Phase 5: process target + CLI example, live Jev

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 5 impl complete:<br/>src/targets/process.mjs<br/>(terminal-like view with<br/>echoed input, sent<br/>count, exit),<br/>examples/cli coffee<br/>counter (adapt…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 5 passed LIVE:<br/>run examples/cli --steps<br/>20 -> 3 Jev steps<br/>(medium, whole, order),<br/>outcome done, exit 0.<br/>App killed after step 1<br/>-…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 5 review passed<br/>(ADR-U1 holds: process<br/>target is pure view/act,<br/>adapter needs no<br/>understudy internals).<br/>Committed. @Neo *swe<br/>impl pha…"
```

---

## Phase 6

Phase 6: page target + web example

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 6 impl complete:<br/>src/targets/page.mjs<br/>(127.0.0.1 static<br/>server, headless<br/>Chromium w/ system<br/>fallback, hook-driven<br/>view/act/talk/say,…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 6 passed LIVE:<br/>run examples/web exit 0<br/>(free/light/accept),<br/>parts name no transport,<br/>--headed -> exit 2, no<br/>hook -> exit 1 after…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 6 review passed<br/>(ADR-U2: hook-driven,<br/>page target cleans up on<br/>its own start failures).<br/>Committed. @Neo *swe<br/>impl phase-7"
```

---

## Phase 7

Phase 7: docs/ADAPTERS.md

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    participant Tank
    participant Oracle
    participant Smith
    participant All
    participant Cypher
    participant Mouse
    Note over Neo,Mouse: 📅 2026-10-15
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 7 impl complete:<br/>docs/ADAPTERS.md<br/>(adapter shape,<br/>process/page targets +<br/>views/actions, app<br/>hooks, part events/tags,<br/>questions + no-l…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 7 passed:<br/>every library name in<br/>the doc exists<br/>(understudy library),<br/>both adapters <150<br/>lines, cold-read answers<br/>'add my own guar…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "Phase 7 review passed.<br/>All phases reviewed.<br/>@Tank *devops sdlc-check"
    Tank->>Oracle: "devops handoff"
    Note right of Tank: "SDLC check passed: distc<br/>lean->install->install<br/>(lock unchanged)->check<br/>93/93, all imports<br/>declared (xstate, yaml,<br/>@typesafe-ai/sdk,<br/>playwri…"
    Oracle->>Smith: "ora handoff"
    Note right of Oracle: "Docs groomed:<br/>docs/DECISIONS.md<br/>ADR-0001..0006 (from<br/>ARCH U1-U6), 4 lessons<br/>in agents/oracle/lessons<br/>.md. rubric SDLC: TRUE=S<br/>WHOLE=A CLEAN=…"
    Smith->>Trin: "user bug"
    Note right of Smith: "*user bug CMD: check<br/>examples/nope |<br/>README.md | run --steps<br/>1 | run --steps |<br/>EXPECTED: 'no such<br/>directory', '1 step', '<br/>--steps needs a nu…"
    Trin->>Neo: "qa triage"
    Note right of Trin: "Triage: 3 Minor defects,<br/>one *fix each, small.<br/>DEF-01 part.mjs dir<br/>check, DEF-02 run.mjs<br/>plural, DEF-03 cli.mjs<br/>missing --steps value.<br/>@Neo…"
    Neo->>Trin: "swe handoff"
    Note right of Neo: "DEF-01..03 fixed test-<br/>first: no such directory<br/>/ not a directory, '1<br/>step', '--steps needs a<br/>number'. 96/96, lint 0.<br/>@Trin *qa verify"
    Trin->>Smith: "qa handoff"
    Note right of Trin: "Fixes verified (3 new<br/>tests + real CLI).<br/>@Smith *user test re-run"
    Smith->>All: "user approve"
    Note right of Smith: "*user approve. User<br/>testing passed (docs/spr<br/>ints/UAT_PLAN_SPRINT1.md<br/>): rubric UAT: COVER=S<br/>STEPS=A FAIL=S DATA=A<br/>EVID=A. Lessons:<br/>doubles=S…"
    Neo->>Cypher: "retro"
    Note right of Neo: "Neo retro: core moved by<br/>renaming only (ADR-0001<br/>paid off). Friction:<br/>lint rules (unicorn)<br/>cost ~1 round per phase,<br/>a blanket sed broke pro…"
    Trin->>Cypher: "retro"
    Note right of Trin: "Trin retro: 39->96<br/>tests, all offline, live<br/>paths covered by test-<br/>live. Caught a vacuous<br/>race test and an<br/>impossible Jev double.<br/>Backlog: a…"
    Morpheus->>Cypher: "retro"
    Note right of Morpheus: "Morpheus retro: ADRs<br/>held, generic look/phase<br/>made both parts<br/>identical. Revisit: page<br/>hook vs DOM mode<br/>(ADR-0002) once a real<br/>unmodified a…"
    Oracle->>Cypher: "retro"
    Note right of Oracle: "Oracle retro: 6 ADRs + 4<br/>lessons recorded, SDLC<br/>current. Gap: no README<br/>for the repo - newcomers<br/>land on nothing.<br/>Backlog: README (what<br/>it…"
    Mouse->>Cypher: "retro"
    Note right of Mouse: "Mouse retro: 8 phases<br/>(0-7) + close, one Neo<br/>task each, no blockers,<br/>no fix loops beyond 1<br/>round. Phase 1 and 6<br/>were the heaviest,<br/>sizing h…"
    Smith->>Cypher: "retro"
    Note right of Smith: "Smith retro: error<br/>messages are the<br/>strongest part<br/>(file/path/name/nearest,<br/>exit codes). Rough edges<br/>found only in edge args<br/>(DEF-01..03).…"
    Cypher->>Cypher: "retro"
    Note right of Cypher: "Cypher retro: Gate 1<br/>reject (no failure ACs,<br/>no step cap) made the<br/>stories testable - every<br/>AC became a test.<br/>Backlog groomed into<br/>docs/BAC…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "*pm launch sprint-1. MVP<br/>first run complete:<br/>understudy plays a CLI<br/>app and a web page live<br/>with Jev, check/library,<br/>96 tests, CHANGELOG +…"
```
