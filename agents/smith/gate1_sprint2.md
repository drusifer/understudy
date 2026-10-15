# Smith — Gate 1 review, Sprint 2 stories (2026-10-15)

rubric STORIES: OUT=S TEST=S FAIL=W SCOPE=S SIZE=S DESIGN=A  → **Needs revision**

## Weak
- **FAIL (UND-6, UND-7)** — Heuristic 1 (visibility) / 3 (user control). Both stories cover "nothing
  at the start" (10 s first move) but not "nothing ever again". A hookless page whose last screen has
  no controls, or an API stuck in a state that offers nothing, would leave the run waiting forever:
  the step cap counts moves, so it never trips. With generic page reading this is the *likely*
  failure, not an edge case. FIX: a criterion in each story - after the first move, if nothing is
  offered for 10 s and the part has not ended, the run exits 1 with outcome `stalled`, naming the
  last state and what the app showed; everything understudy started is stopped.

## Acceptable, with notes
- DESIGN: UND-7 AC2 "at most 10 lines" is a size target the owner implied ("adapter optional");
  fine. How the generic adapter knows the *end* is left to Morpheus - good, but Morpheus must make
  the end observable to the author (it is the part's job to say what "done" looks like).
- UND-6 AC6 (error status → continue): sensible; the step cap bounds a loop of errors.

## Strong
- Log labels by kind + visible text (`button:Pro (paid monthly)`) - logs readable without the HTML (H2).
- No-back-compat stated as a testable criterion (AC5 + UND-8 AC2 grep).

## Re-review
rubric STORIES: OUT=S TEST=S FAIL=S SCOPE=S SIZE=S DESIGN=A → **Approved**. Note for Morpheus:
`stalled` applies to every target (program too) - one rule in the run loop, not per target.

# Smith — Gate 2 review, Sprint 2 architecture (2026-10-15)

rubric ARCH: BOUND=S FLOW=S FAIL=S USER=A DECS=S FEAS=S → **Approved with notes**

- USER (A): the most likely first mistake with a hookless page is forgetting the `showing` end: the
  run plays to the last screen and then "stalls". Make the stall message point at the fix (H9):
  `... - if this is where the part should end, add a showing guard (docs/ADAPTERS.md)`.
- USER: `check` should say when the generic page app is in use: `adapter signup-web (page, generic
  page app)`, so the author knows no hooks of theirs run (H1).
- Good: control ids by role + visible name; unknown target fields refused with the known list
  (catches a leftover `hook` cleanly, without a compat path).
