# Sprint 6 User Stories: The dashboard, with atmosphere

*   **Total Points**: 25 (Tier 1)
*   **Branch**: `sprint-6`
*   **Source**: owner, 2026-10-16: "a steampunk operational dashboard with knobs to set the various
    levels, toggles, and chunky sliders, and then showing the state machine logic ... I want
    understudy to have some atmosphere." Shaped in chat over a clickable mockup the owner approved;
    the brief is `docs/design/DASHBOARD.md`, decisions in `docs/BACKLOG.md` "Sprint 6".
*   **Status**: Approved at Smith Gate 1 (2026-10-16), one note folded into UND-32 AC4
*   **Order**: UND-27 → UND-28 → UND-29 → UND-30 → UND-31 → UND-32 → UND-33 (each leaves `understudy` usable)

## Goal

The person an understudy stands in for can sit at a console instead of a command line: open a
folder of sketches, pick one, set its mood and how much each preference matters with real-looking
dials, faders and switches, press Play, and watch the run happen - the statechart glowing in a
vacuum tube with power flowing by weight, the log printing out on paper. Preferences can be
retuned in place and saved back to the sketch, and a power cycle puts the factory settings back.
It makes the sprint 5 decision engine something you can feel, not just read in YAML.

## Assumptions made for the owner

- **Local and offline, like the watch page**: served by understudy on 127.0.0.1 (or `--host`),
  under an unguessable token path, with every font and file served locally - the mockup's Google
  Fonts become bundled font files (open licences).
- **One run at a time** per dashboard; Play while a run is going is the Stop button.
- **A sketch without inputs** still gets the rack, Play, tube and printer; its control panel says
  it has nothing to tune.
- **The tube draws any sketch's statechart**: states on a circle in the turn's order, final states
  inside; edge labels come from the same labelling the watch page uses (event, guard). The
  "decision edge" is the transition into the state that plays a move.
- **Factory defaults** are the sketch as it was before the dashboard first changed it: the first
  saved edit keeps a copy, and the power cycle puts it back (and removes the copy).
- **Saving keeps the file readable**: comments and layout of `sketch.yaml` are kept; only the
  edited values change. A value the checks would refuse is not saved, and the box says why.

---

## STORY-UND-27: A rack of sketches
**Points:** 3
**Depends on:** none

**As the** owner,
**I want** `understudy dashboard <folder>` to open a console listing every sketch in the folder,
**so that** I can choose what to play without typing paths.

### Acceptance Criteria
1. `understudy dashboard examples` prints `understudy: dashboard at http://127.0.0.1:<port>/d/<token>/`
   and serves the console; the rack lists every directory holding a `sketch.yaml`, by name, with
   its description's first line.
2. A sketch that fails `check` is listed greyed out with its check message; it cannot be played.
3. Picking a sketch shows its controls (UND-28), its statechart (UND-30) and an empty printer.
4. A folder with no sketches, or a path that is not a folder, is refused before anything starts
   (`understudy: examples/cli/app.mjs is not a folder of sketches`), exit 2.
5. `--port`, `--host` work as for `run --watch`; a wrong token path is a 404; Ctrl-C stops it (exit 0).

## STORY-UND-28: Controls from the sketch's inputs
**Points:** 5
**Depends on:** UND-27

**As the** owner,
**I want** each input of the chosen sketch drawn as a physical control - a mood dial, analog
faders, switches with lamps,
**so that** setting up a run feels like operating a machine, and nothing is typed.

### Acceptance Criteria
1. A `choose` input is a pointer dial with its options around it (2-6 options); clicking an option
   turns the pointer to it.
2. A `weight` input is a continuous fader over its range, left = less important, right = more;
   each weight has its own colour; its readout shows the value, `OFF` at 0 and `11` at the top.
3. A new **switch** input (`together: { switch: true, default: true }`) is a toggle with an LED
   lamp; a gate written `together: { at_least: 2, when: together }` applies only while it is on.
   `check` refuses `when:` naming a non-switch input.
4. Controls start at the sketch's defaults; `run --input together=off` works for switches too.
5. Every control is reachable and usable by keyboard and has an accessible name and value.

## STORY-UND-29: Press Play
**Points:** 3
**Depends on:** UND-28

**As the** owner,
**I want** a big lit Play button and a READY lamp,
**so that** I start the run with the settings I chose and know when the console is ready.

### Acceptance Criteria
1. The READY lamp glows green while a playable sketch is chosen and nothing runs; pressing Play
   starts the sketch with the controls' values as its inputs (the run's start line lists them).
2. While it runs the lamp turns red-orange and the button reads STOP; pressing it stops the run
   as Ctrl-C would (`interrupted`); the controls are locked while running.
3. A run that ends (any outcome) unlocks the controls; the outcome is shown and printed.
4. A run that cannot start (no `TYPESAFE_API_KEY`, a server that will not start) prints why on
   the printer and the lamp stays green; nothing is left running.
5. Each run writes its log under `build/runs/<sketch>/` as `run` does.

## STORY-UND-30: The state tube
**Points:** 5
**Depends on:** UND-29

**As the** owner,
**I want** the statechart in a round vacuum-tube screen, every state and transition labelled,
with power flowing by weight,
**so that** I can see where the understudy is and how hard each preference pulls.

### Acceptance Criteria
1. Every state of the chosen sketch's `turn:` is drawn and named, final states inside the circle;
   every transition is drawn and labelled with its event or guard.
2. During a run the current state glows within one second of each `state` line, and the
   transition just taken carries flowing energy.
3. Around the rim, one arc per weight input in its colour, filled by its value; the decision edge
   and a centre orb take the blend of the weight colours in the faders' ratio, with each weight's
   share in percent.
4. A sketch with no weights shows the tube without the ring or orb.

## STORY-UND-31: The printer
**Points:** 2
**Depends on:** UND-29

**As the** owner,
**I want** the run log to print out line by line on tractor-feed paper,
**so that** I can read what happened as it happens.

### Acceptance Criteria
1. Each step prints one line (step, move, arguments, confidence); held values, removals and Jev
   Score answers print as indented lines; the final line prints the outcome.
2. A step with a score table prints the table; a factor at 1.0 prints as `11`.
3. Paper feeds up as lines are added; the newest line is always visible; earlier lines can be
   scrolled back to.

## STORY-UND-32: Access panels, saved, with a factory reset
**Points:** 5
**Depends on:** UND-28

**As the** owner,
**I want** to slide down a panel under each fader and under the mood dial to edit its settings,
saved to the sketch, and to get the factory settings back by turning the power off and on,
**so that** I can retune my preferences without opening YAML - and undo it all at once.

### Acceptance Criteria
1. Under a fader: its factor's range (from, to) or order, its Score question and `looks_at`, and
   its input's default; under the mood dial: the moods (rename, add up to 6, remove down to 2)
   and the default. Each panel shows the matching `sketch.yaml` line.
2. An edit is saved to the sketch's `sketch.yaml` within a second; the file keeps its comments
   and layout; `understudy check` on it passes.
3. An edit the checks refuse (from = to, an empty mood, a default outside the range) is not saved;
   the box is marked and says why.
4. POWER off stops a run that is going (as STOP does), dims the console and disables every
   control but POWER; POWER on restores every edited sketch to the copy kept before its first
   edit, removes the copy, and reloads the controls at the factory defaults.
5. Edits are refused while a run is going.

## STORY-UND-33: Atmosphere, documented and tested
**Points:** 2 · **Owner:** Trin (tests), Oracle (docs)
**Depends on:** UND-27 to UND-32

**As an** author of sketches,
**I want** the dashboard documented and covered by browser tests,
**so that** I know how my inputs will look and the console keeps working.

### Acceptance Criteria
1. `docs/USER_GUIDE.md` has "The dashboard" with a screenshot; `docs/SKETCHES.md` documents
   switch inputs and `when:`.
2. `bobp make test-browser` drives the dashboard with a Jev double: pick `evening`, move a fader,
   flip a switch, press Play, see the tube highlight move and the printer print the ticket.
3. The evening example gains a `together` switch.

---

## Out of Scope
- Changing inputs during a run (owner: knobs before the run).
- Running several sketches at once, or from another person's browser at the same time.
- Editing anything but the factor parameters, inputs and moods (no turn or gate editing).
- Sound effects.

## Open Questions
None — every choice above was the owner's or is stated as an assumption.
