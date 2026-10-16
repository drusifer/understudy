# The dashboard: approved design (sprint 6)

Approved by the owner on 2026-10-16 after seven rounds on a clickable mockup:
https://claude.ai/artifact/KDDBABtgUpn5NbnKT9h1TQ (private to the owner). Its source is kept
here as `dashboard-mockup.dc.html` - a Design Component file (it needs that runtime to play; read
it for markup, colours and behaviour). The run it plays is canned from a real live run.

## What it is

A steampunk operations console for understudy. `understudy dashboard <folder>` opens it on a
folder of sketches; the person picks a sketch, sets its inputs, presses Play and watches the run.
Knobs are set **before** a run, not during it (owner).

## The parts, top to bottom

| Part | Looks like | Does |
|---|---|---|
| Header | riveted brass plate, gear mark, "UNDERSTUDY · OPERATIONS CONSOLE" | status lamp (standing by / on air / dark) and the **POWER** toggle |
| POWER | a brass bat-handle toggle | off dims the console; **off then on resets the sketch to its factory defaults** (owner) |
| Sketch rack | brass tabs, one per sketch in the folder, with its one-line description | picks the sketch |
| Mood dial | an oblong pointer knob on a dark centre, moods spread around it, lit tick marks | rotates to the chosen `choose` input (any count, spread over 150°) |
| Faders | analog brass sliders on a black slot, continuous (no steps); **left = less important, right = more**; each weight its own colour (tomato red, audience violet, row cyan, centre green); Nixie-style readout, `11` at full | set the weight inputs |
| Access panels | a ▸ under each fader and under the mood dial slides down a recessed panel of plain edit boxes | edit the factor's parameters (range from/to, order, question and what it looks at, default weight) and the moods (rename, add up to 6, remove down to 2, default); shows the matching `sketch.yaml` line; **saved to the sketch as you type** (owner) |
| Switches | toggle with an amber LED lamp, ON/OFF | the new **switch** input: turns a gate on or off (`when: <switch>`) |
| Play | a **square** red button lit from within, in a brass frame; a **green glowing READY lamp** beside it (red-orange while running) | starts the run; pressing again stops it |
| State tube | a big round vacuum-tube screen with a glass glint | the sketch's statechart on a circle (finals inside); **every state and edge labelled** (event or guard, plus a short note); the current state glows; energy flows along the edges while running |
| Power ring | arcs around the tube's rim, one per weight in its colour, filled by its value | the decision edge (the move) and a centre orb carry the **blend of the weight colours in the faders' ratio**; shares in % under the orb |
| Printer | tractor-feed paper rising out of a printer roller, dot-matrix type | the run log prints line by line; ends with the score table, where 1.0 prints as `11` |

"11" is only how a perfect 1.0 is shown (owner); the engine rule for it shipped in sprint 5.

## Type and colour

Cinzel (plates, labels), Spectral (prose), VT323 (Nixies, tube labels), DotGothic16 (printer).
Walnut and brass ground (#140e0a, #c9a15a, #8a6630), phosphor amber (#ff9a3c), weight colours
rgb(255,72,56) / rgb(176,98,255) / rgb(56,196,255) / rgb(120,236,70). All self-hosted in the real
page - nothing fetched from the internet (sprint 4 rule).
