# Smith — Gate 1 review, Sprint 1 stories (2026-10-15)

rubric STORIES: OUT=S TEST=A FAIL=W SCOPE=A SIZE=W DESIGN=A  → **Needs revision**

## Weak
- **FAIL (UND-1, UND-2)** — Heuristic 9 (help users recover) / 1 (visibility).
  - UND-2 has no failure criterion. Most likely failures: Chromium not installed, page never
    reaches a playable state. FIX: AC saying what the user is told (name what is missing and
    the command that installs it) and that the command exits non-zero with no browser left running.
  - UND-1 has no bound: a part that never reaches the end state (or Jev looping between moves)
    runs forever and burns paid Jev calls. Owner just asked for capped live runs. FIX: a step
    limit with a stated default, overridable on the command line; hitting it exits non-zero
    naming the limit and the last state, and the log still ends with a final line.
- **SIZE** — UND-2, UND-3, UND-4 all depend on UND-1 (the `run` command, the step log) and
  UND-5 on both examples, but no story says so. FIX: a "Depends on" line per story and an order.

## Acceptable, with notes
- **TEST** UND-1 AC3 "records the fallback that was used" — the user cannot tell what a
  fallback is. Say what happens (e.g. the first offered move is sent, or the step is retried
  once then the run stops) so it is a yes/no check. Architect may choose, but the AC must name
  the observable result.
- **SCOPE** Open question 1 can be closed: `TYPESAFE_API_KEY` is set in the owner's environment.
- Owner confirmed all four assumptions and the sprint-1 branch today; mark them confirmed.
- UND-4 AC1: also say the message names where to get a key? Nice-to-have, not required.

## Strong
- Goal + two very different targets read as one argument ("not a card harness renamed").
- UND-3 failure messages carry file, path, bad name and nearest name — excellent error design.

## Re-review (after Cypher's revision)

rubric STORIES: OUT=S TEST=S FAIL=S SCOPE=A SIZE=S DESIGN=A  → **Approved with notes**

- FAIL now S: every story that takes input names what the user is told, the exit code, and
  what is left behind (nothing running, log closed).
- TEST now S: exact messages and numbers (50 steps, 10 s, exit 1/2) are usable as test cases.
- SIZE now S: Depends-on lines and an order where each story leaves the tool usable.
- Note for Morpheus: UND-2 AC5 names `bobp make install-browser` — a new make target, i.e. a
  mechanism change for Tank. Note for Morpheus: keep exit codes consistent across commands
  (0 done, 1 run failed, 2 refused before starting) — Heuristic 4.

# Smith — Gate 2 review, Sprint 1 architecture (2026-10-15)

rubric ARCH: BOUND=S FLOW=S FAIL=S USER=A DECS=S FEAS=S  → **Approved with notes**

- USER (A, not S): three output surfaces are unspecified — fix in the doc before Mouse plans:
  1. `understudy check <dir>` success output (Heuristic 1): say what was checked, e.g.
     `examples/cli: part OK - 6 states, 2 questions, adapter coffee-cli`.
  2. `understudy library` format: one line per name, grouped by kind, `name - doc`.
  3. `run` must print where the log is going on its first stderr line (recard did; Heuristic 1).
- Good: exit codes 0/1/2 everywhere; every failure row names what the user sees; Ctrl-C
  leaves at a safe state (Heuristic 3, user control).
- Vocabulary renames (OBSERVE, changed, quiet, look, phase) match the author's world (H2).
