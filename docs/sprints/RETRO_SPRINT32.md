# Sprint 32 Retro: the beat box

Delivered: UND-118 (the runner profiles what flows through a beat), UND-119 (the beat box: gauges, donuts, bars, a pass stepper, Jev and decision bars), UND-120 (the scattered expanders folded into the box and a run header). Three phases; household outputs byte-identical on the real files.

## What went well

* **The owner's answer ("that iteration's data, not the whole list; a bar, pie or gauge") made the design:** one box, charts chosen by the shape of a column, one pass at a time. The earlier question (values or shapes) got a better answer than either option offered.
* **Server and page split cleanly:** the log carries small summaries, `step_details` turns them into per-beat data (so a replay works for free), and `box.js` only draws.
* **Real data caught real things:** the first live look showed the default beat for a finished run was the final beat (nothing to show), single-row pieces read better as labeled values than as one-value gauges, and Jev labels overran their bars.

## What went wrong

* **The log tripled** (1.06 MB to 3.49 MB for the real household run), almost all of it the `iteration` events. The 40-pass window keeps the page fast; the file is still large. Trim `made.columns` on passes, or keep passes only for the latest N per beat, if it matters.
* **A flaky measuring test** again (the contrast test photographing a text the page then redrew; once the pixels were the text's own color, ratio 1.00). Fixed by looking again when the text is redrawn mid-photograph, three clean runs after. Cause: a test that reads pixels races any redraw; each new redraw source (the plan, the rack, the box) adds chances.
* **Scope moved while planning:** I wrote the Sprint 32 story after the owner's answer, with the box inside the old tube panel rather than replacing a separate panel; and the "change the play" request arrived mid-sprint and was queued, not planned (it needs a question first).
* **Process:** the steps went by the rules (Edit/Write, tests first), with one slip: an accidental no-op shell command early on.

## By persona

* **Neo:** `profile.py` and `box.js` are small and tested; the DecisionPanel tests became DecisionBox tests. **Trin:** the byte-identical comparison again; live evening replay checks. **Smith:** the box reads, but a single-row piece as a gauge was wrong (fixed). **Switch:** the log now carries summaries and one row per pass of the owner's data, accepted by decision 45. **Morpheus:** `_owner_of` attributes a Jev answer to its beat by name instead of by which beat was running.

## Backlog

* Trim the iteration events (size). (Neo)
* "A way to change the play": ask the owner what is meant (edit the file, change a beat's `with`, something else) before planning. (Cypher, Smith)
* Step into passes (hold between passes of a repeated beat), now that the box shows one pass at a time. (Cypher)
* Render the rack, plan and box redraws without replacing unchanged elements, which would also end the redraw races in measuring tests. (Neo)
