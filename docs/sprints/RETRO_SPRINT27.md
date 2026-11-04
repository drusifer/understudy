# Sprint 27 Retro: the test pyramid

Delivered: UND-101 child sketches load once per file version (-46% per row, outputs identical), UND-102 household rules tested on their own stages (73 tests in about 57 s became 80 in 11.4 s; five whole-sketch runs left of about 53), UND-103 the browser suite cheaper (154.9 s to about 100 s, flake gone), UND-104 the gate fails fast and the strategy is written down. The Python unit suite went from 94.6 s to 29.4 s and the whole gate from 96 to 101 s to 36.3 s.

## What went well

* **Measuring first changed the plan three times:** the profiler's "half the time is the loader" turned out to be 12%; contrast could not be computed in Python (textured themes); and the biggest saving (a 0.5 s server stop poll, about 35 s over both suites) was in no plan.
* **Every moved group was proved by breaking its rule** (eleven rules broken and caught), and the move found two checks the old tests lacked.
* **The gate answers sooner:** a lint error now stops it in 0.16 s, not after 31.8 s.

## What went wrong

* **The browser target was missed:** about 100 s against 90 s, and only two runs were made, not five. The remaining time is about 2 s a page for 37 tests; cutting it means merging tests, which loses isolation.
* **Two plan claims were wrong when written** (the loader's share, contrast in Python) and were corrected in the amendments rather than at Gate 1; the story should have said "measure first" for any figure.
* **Edit-only slipped again** (Neo): empty `python3` heredocs and a `ruff --fix` over all of `tests` that edited two unrelated files (reverted from git, noticed at once).
* **I ran the full gate and the browser suite too often earlier in Sprint 26**, which is where the owner's question started.

## By persona

* **Neo:** fragment tests first held; the lint rules (line length, magic values) still cost reruns. **Trin:** the break-the-rule check is now the proof of a moved test. **Morpheus:** ADR-0060; watch the stand-ins drifting from real output. **Tank:** the Makefile order and the strategy numbers. **Oracle:** two lessons. **Mouse:** five phases, sizes held. **Cypher/Smith:** the targets were measurable and reported as missed where missed.

## Backlog (feeds `docs/BACKLOG.md`)

* Browser suite to 90 s: merge page tests that share a page (replay bar, decision panel, hold buttons) or accept about 100 s; owner to say. (Trin)
* A test that the household's stand-ins (`placed_all`, the Jev double) still have the shape the child sketch really outputs. (Neo)
* The one-time import costs in the slowest unit tests (`dateparser` 1.5 s, the first `check` 1.8 s) could be paid once by a shared import; small. (Neo)
* Earlier: YAML editor, Venmo and Zelle, pin the own-account merchants, per-decider weights in the decision log, make the Monarch Category optional, write open_balance 0 when none.
