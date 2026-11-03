# Sprint 24 Retro: what the money goes on, typed inputs, and the statechart you can see

Delivered: UND-93 card payments are not spending, UND-94 where the money goes, UND-95 the console shows it, UND-87 typed inputs (declared, then drawn), UND-82 the statechart (laid out, then drawn). 27 points, seven phases, one commit per phase on `sprint-24`; 428 unit tests, 22 browser tests, lint and gitleaks green. Not merged or pushed (owner).

## What went well

* **Gate 1 caught a target that could not be met.** Smith worked UND-93's figure out on the real run before approving and found $153,085 of card payments the labels could not reach; the link between the two halves of a payment did. The story was reworded and the target was met ($20,038 left).
* **The owner's question got an answer:** $403,977 spent across 90 categories, Rent first at $60,807 (15%), then Taxes, Mortgage and medical.
* **The readability check earned its keep twice:** it found the new heading unreadable in two light looks and the dial unreadable in two dark ones (the themes still styled the old console's classes).
* **The layout is tested without a browser:** boxes, labels and arrows never overlap, on the real machines and on generated 40-state machines; the page is about sixty lines of drawing.
* **Switch found a real input hole:** a typed number was checked as a float but passed on as the owner's text (`1e2`, padded, underscores); fixed with a test (SEC-010).

## What went wrong

* **The Edit-only rule slipped again** (Neo): a no-op Python call and an `sed` on a scratch script. Nothing in the repo was edited that way this time, but the habit is still there.
* **A quoted escape was changed by the edit tool** (`٥` became the literal character and tripped lint twice); `chr(0x665)` fixed it.
* **The browser check is slow:** 22 tests take about 104 seconds, so by the owner's rule it is not a release gate; it also flaked once on an old selector (`.stage-lamp`, Steampunk dark) and passed in three repeats.
* **Dead theme CSS** from the old console (`.dial-option`, `.switch`, `.fader`, `.stepper`) collided with new class names; new names avoided it, the dead rules remain.
* **The sprint was larger than first said:** the parity list (diagram, stepping, replay, decision detail, editor) did not fit; Sprint 24 took the diagram and typed inputs and the rest moved to Sprint 25 (told to the owner in the stories).

## By persona

* **Neo:** TDD held in every phase; friction was lint rules (argument counts, magic numbers, loop closures) and one function too long. **Trin:** UAT on the real files and in a real browser each phase; looked at the rendered charts, not just the overlap tests. **Switch:** one finding (SEC-010), one design-gate condition (hostile names) met in Phase 7. **Morpheus:** approved the label-or-link rule and the split of UND-87 and UND-82; noted the layout is simple layering. **Oracle:** ADR-0052 to ADR-0054 and two lessons. **Mouse:** seven phases, each one build task and three gates; sizing held. **Cypher:** the first stories had a target nobody had computed. **Smith:** rejected the right thing at Gate 1; accepted with rough edges for the backlog.

## Backlog (feeds `docs/BACKLOG.md`)

* Remove the dead theme styles for `.dial-option`, `.switch`, `.fader`, `.stepper` and the rest left from the old console. (Neo)
* The spending list's category `Refund` has a negative amount (money back with no original category), and some of the owner's groups read oddly ("Shopping & Retail: Restaurants & Dining"). (Owner, Cypher)
* A few purchases under a card-side label (Depop, Soho Deli, Levy Restaurants) count as transfers until relabeled in Monarch. (Owner)
* The `.stage-lamp` readability check flaked once; measure it with the lamp's glow held still. (Trin)
* The `evening` description still repeats "Values you can set: --with ..." now that the console shows them. (Cypher)
* Sprint 25: step, pause, resume and `run --watch`; replay of a finished run from its log; decision detail; the YAML editor. (Cypher)
