# Sprint 5 User Stories: A decision engine - gates, scores, Jev

*   **Total Points**: 29 (Tier 1) - the largest sprint yet, kept whole by the owner
*   **Branch**: `sprint-5`
*   **Source**: owner, 2026-10-16, in chat: "I prefer horror films, and I want to go in the
    evenings but only if row E, F, or D is available (in that order), seats together but not too
    far from the center." Shaped in chat the same day into a general decision engine; every
    decision is recorded in `docs/BACKLOG.md` "Sprint 5" and in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gate 1 (2026-10-16), two notes folded into UND-22 AC1 and UND-24 AC6
*   **Order**: UND-18 → UND-19 → UND-20 → UND-21 → UND-22 → UND-23 → UND-24 → UND-25 → UND-26
    (each leaves `understudy` usable)

## Goal

An automation author can describe how a person decides, in the sketch's YAML: what they will
never accept (gates), what they like more or less and how much it matters (weighted scores), what
only a reader of reviews could judge (a Jev Score), and what mood they are in today (inputs).
understudy filters and ranks the rows the app answers, Jev picks the final one from the
shortlist, and the log shows every number behind the pick. When nothing qualifies, the
understudy walks away and the run still succeeds. This is a general use: a filter over JSON rows
that picks the subset worth a closer look - the cinema is the first example.

## Assumptions made for the owner

- **Selection is per argument.** Gates, scores and the final pick apply to the values offered
  for one tool argument (the showing, then the seat); each value is the answer row it came from,
  joined with other servers' rows about the same film by its title.
- **A fact not answered yet holds a value back**, not out: until the ratings server has answered
  for a film, its showings are not offered, and the run says what it is waiting for.
- **Jev's Score is asked once per row per run** and reused, so changing nothing costs nothing.
- **Inputs are set on the command line in this sprint** (`--input mood=romantic --input
  row=1`); the dashboard that sets them with knobs is sprint 6.
- **Sketches without the new sections play exactly as in sprint 4.**
- **Example defaults** are Cypher's proposal (owner OK'd): weights in `[0, 3]`; row
  `order: [E, F, D]` weight 2; centre `range: [0.3, 1]` weight 3; tomato `range: [70, 100]`
  weight 1; audience Score weight 2; mood `fun`; shortlist unbounded. All are one line to change.

---

## STORY-UND-18: A box office worth deciding about
**Points:** 3
**Depends on:** none

**As an** automation author trying out the decision engine,
**I want** the example box office to offer films of several genres, afternoon and evening
showings in screens of different sizes, and a seat map,
**so that** there are real trade-offs between genre, time, row and centreness.

### Acceptance Criteria
1. The box office lists at least five films, each with a title and a genre; at least two are
   horror and at least two are not.
2. Each film has at least one showing before 17:00 and one at 17:00 or later, each with a start
   time `HH:MM` and a screen; there are at least two screens with different row widths.
3. For any showing, the box office answers its seat map: every free seat with its row letter,
   seat number, how many free seats run together from it in that row, and its `centre` from 0
   (an end seat) to 1 (the middle of the row), scaled by the row's width (3 seats off centre:
   about 0.3 in a 10-seat row, about 0.8 in a 30-seat row).
4. Holding two seats from a seat whose free run is at least 2 holds two side-by-side seats, and
   the hold names them (`E7, E8`); paying issues a ticket naming the film, time and seats.
5. Holding from a seat whose run is too short is refused, naming the seat and its run (`E9 has
   only 1 free seat together`); nothing is held.
6. The seat maps include an evening horror showing with central seats free in row E, one with
   only edge seats in E but central seats in F, and one with no seat in E, F or D.

## STORY-UND-19: A ratings service with reviews
**Points:** 2
**Depends on:** UND-18 (it rates those films)

**As an** automation author,
**I want** an in-repo ratings MCP server that answers a made-up tomato score and a few made-up
audience reviews for a film,
**so that** decisions can use facts and opinions the box office does not have, with no key and
no network.

### Acceptance Criteria
1. Asked about a title, it answers `{ "title": "Night Shift", "tomato": 82, "reviews": [ ... ] }`
   with three to five short reviews.
2. It knows every film UND-18 lists. Among them: a horror film at 70 or more, a horror film below
   70, a non-horror film above 90 and a non-horror film at 90 or less; some reviews are
   enthusiastic and some bored. The same title always gets the same answer.
3. An unknown title is a tool error naming it (`no rating for "Xyz"`), not a crash.
4. It runs as a local stdio MCP server like the box office and knows nothing about the box office
   or understudy.

## STORY-UND-20: One sketch plays several MCP servers
**Points:** 5
**Depends on:** none (UND-19 gives it a second server)

**As an** automation author,
**I want** a sketch to name more than one MCP server, in the same `mcpServers` shape as today,
**so that** a box office and a ratings service can be used in one run.

### Acceptance Criteria
1. A sketch can name several servers, inline or by reference to `servers.json`; a one-server
   sketch is written and plays exactly as in sprint 4.
2. The moves on offer are the tools of every server; each move, step log line and watch-page
   decision says which server the tool belongs to, so same-named tools are never confused.
3. Values for a tool's argument may come from any server's last answers (the box office's titles
   feed the ratings server).
4. All local servers are started before the first move and stopped at the end, also on failure
   and Ctrl-C.
5. A server that fails to start or connect refuses the run naming it (`understudy: server
   "ratings" did not start: ...`); servers already started are stopped.
6. `understudy check` validates every server entry and reports a bad one by name and file.

## STORY-UND-21: Gates the understudy never breaks
**Points:** 3
**Depends on:** UND-20 (gates may test facts from any server)

**As an** automation author,
**I want** to write what the person will never accept as gates in `sketch.yaml`,
**so that** a value that fails one is never scored, never shown to Jev and never chosen.

### Acceptance Criteria
1. A gate tests fields of a value's answer row with `is` (a bare value means `is`), `in`,
   `at_least`, `at_most` and `any` (passes if one of several groups passes); `at_least` and
   `at_most` compare numbers as numbers and `HH:MM` as times. The owner's film gate is
   `starts: { at_least: '17:00' }` plus `any: [{ genre: horror, tomato: { at_least: 70 } },
   { tomato: { at_least: 91 } }]`.
2. With that gate, no offered list ever contains an afternoon showing, a horror film under 70 or
   a non-horror film at 90 or less; an evening showing of a non-horror film above 90 is offered.
3. A gate needing a fact no server has answered yet holds the value back, and the run says once
   what it is waiting for (`holding back showing s4 - no "tomato" for "Night Shift" yet`).
4. Each step's log line lists what the gates removed and why (`s2: starts 14:00 < 17:00`).
5. `understudy check` refuses an unknown word, an `in`/`any` that is not a list, or an
   `at_least`/`at_most` that is neither a number nor `HH:MM`, naming the file, the gate and the
   word; nothing runs.

## STORY-UND-22: Weighted scores rank what passes
**Points:** 5
**Depends on:** UND-21

**As an** automation author,
**I want** to score each value on the factors the person cares about, with a weight that says
how much each matters,
**so that** the values that suit them best rise to the top, and I can see why.

### Acceptance Criteria
1. A factor maps one field to 0..1 with `range: [from, to]` (linear, either direction, clamped)
   or `order: [E, F, D]`; its weight shapes the curve as score = position ^ weight. For rows at
   weight 1 the scores are E 1, F 0.67, D 0.33; at weight 2, E 1, F 0.44, D 0.11. Weight 0
   turns the factor off: it scores 1 for every value, so it neither ranks nor drops anything.
2. A value's total is the product of its factor scores. A factor at the bottom of its range
   scores 0, so the total is 0 and the value is dropped.
3. The shortlist is every value with a total above zero, highest first, unless the sketch bounds
   it with `shortlist: { at_most: N }` (the top N) or `{ total: { at_least: X } }`.
4. With the example defaults and UND-18's seats, an edge seat in E (centre 0.4: total
   about 0.003) ranks below a central seat in F (centre 1: total 0.44), and a seat with centre
   0.3 or less is not on the shortlist.
5. Each step's log line holds the score table for the shortlist (each value, each factor's score,
   the total), and the watch page shows the same beside the step.
6. `understudy check` refuses a `range` that is not two numbers or times, an `order` that is not
   a list, or a weight that is not a number of zero or more, naming the file and factor.

## STORY-UND-23: Jev judges what numbers cannot
**Points:** 3
**Depends on:** UND-22

**As an** automation author,
**I want** to declare a Jev Score question in the YAML - what it looks at, the question, its
levels - and use its answer as a factor,
**so that** fuzzy things like how an audience reacted count in the decision, with a weight like
everything else.

### Acceptance Criteria
1. A question can be `type: score` with `looks_at` (a field of the value's rows, e.g. `reviews`),
   `instructions` and two or more `levels`, ordered worst to best.
2. A factor `{ ask: audience, weight: 2 }` uses that question's 0..1 answer for each value;
   with UND-19's reviews, a film with enthusiastic reviews scores higher than one with bored ones.
3. The question is asked once per row per run; later steps reuse the answer (the log says so).
4. The score table shows Jev's answer as its own factor.
5. `understudy check` refuses a factor that asks an unknown question or a non-score question,
   and a score question with fewer than two levels, naming the file.

## STORY-UND-24: The person's mood, and inputs
**Points:** 3
**Depends on:** UND-22, UND-23

**As the** person the understudy stands in for,
**I want** to tell it my mood and adjust how much each preference matters when I start a run,
**so that** the same sketch decides the way I feel today.

### Acceptance Criteria
1. A sketch declares inputs: a choice (`mood: { choose: [fun, serious, dramatic, romantic],
   default: fun }`) and weights within a range (`centre: { weight: [0, 3], default: 3 }`); a
   factor's weight can name an input.
2. `understudy run <sketch> --input mood=romantic --input centre=1` uses those values; the run's
   first log line lists every input's value.
3. The final pick is Jev's Choice among the shortlist, told the mood; with mood `romantic` and
   mood `fun`, the instructions Jev receives differ only in the mood.
4. A shortlist of one is taken without asking Jev (the log says so).
5. An unknown input, a choice not in the list, or a weight outside its range refuses the run
   (`understudy: input "centre" must be between 0 and 3, got 5`); nothing runs.
6. `understudy check` refuses a factor whose weight names an input the sketch does not declare,
   or an input whose default is outside its own range, naming the file and the input.

## STORY-UND-25: Walk away when nothing qualifies
**Points:** 2
**Depends on:** UND-21, UND-22

**As an** automation author,
**I want** the understudy to leave empty-handed - and the run to succeed - when nothing passes the
gates or every total is zero,
**so that** "nothing suitable tonight" is a result I can test for, not a stall.

### Acceptance Criteria
1. A turn can end in a state for leaving, reached when the shortlist for the move the understudy
   needs to make next is empty.
2. Reaching it exits 0; the final line has `"outcome": "walked-away"` and the state.
3. Before the final line, the log has one line saying what each gate and zero-scoring factor
   removed, and stderr says it in a sentence (`understudy: walked away - nothing qualified:
   starts at_least 17:00 removed 5 showings; ...`).
4. No call is made after the shortlist comes up empty.
5. Without a leaving state, an empty shortlist ends as `stalled`, with the same explanation.
6. Values held back for a missing fact never count as removed: it does not walk away while
   waiting for an answer.

## STORY-UND-26: The owner's evening, as an example
**Points:** 3 · **Owner:** Neo (Oracle for the docs)
**Depends on:** UND-18 to UND-25

**As the** owner,
**I want** an example sketch that plays the box office and the ratings server with my evening
written as gates, scores, a Jev Score and inputs, and docs that teach it,
**so that** I can run my evening out, turn the knobs from the command line, and others can write
their own.

### Acceptance Criteria
1. A new example uses the defaults above and `understudy run` on it buys two side-by-side seats
   for an evening showing that passes the film gate, from the shortlist, with the score table in
   the log.
2. Changing one input (`--input centre=0`) visibly changes the score table.
3. Against a box office state where nothing qualifies, it walks away with exit 0.
4. `bobp make test-live` runs the buy and walk-away cases and checks each final `outcome`.
5. `docs/SKETCHES.md` documents several servers, every gate and score word, score questions,
   inputs and the shortlist; `docs/MCP_GUIDE.md` has a "Deciding like a person" walkthrough with
   this example; `docs/USER_GUIDE.md` lists `--input` and the `walked-away` outcome.

---

## Out of Scope
- The steampunk dashboard with knobs and sliders (sprint 6, `docs/BACKLOG.md`).
- Jev choosing weights (it would be writing numbers; maybe later as levels it chooses).
- Scoring a showing by its best seats: picks happen one move at a time.
- Real Rotten Tomatoes or OMDb data, keys or network for ratings.
- Gates and scores on targets other than MCP, or written in code (`hooks.mjs`).
- Loosening a gate when nothing qualifies.

## Open Questions
None. (Size: owner, 2026-10-16, "go big or go home" - all 29 points stay in sprint 5.)
