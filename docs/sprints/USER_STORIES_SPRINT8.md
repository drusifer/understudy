# Sprint 8 Story + Architecture (Tier 2): Behind the printer

*   **Total Points**: 3 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-8`
*   **Source**: owner, 2026-10-16: "removing one of the panels reveals the yaml for the sketch
    allowing the user to edit the sketch and update the panel" - the **printer** comes off; it helps
    to "see the state machine change as the yaml is updated"; "a sticker with a cheat sheet is inside
    the panel"; edits save "same as sliders". Recorded in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gates 1 and 2 (2026-10-16)

## STORY-UND-35: Edit the sketch behind the printer
**Points:** 3

**As the** owner,
**I want** to take the printer off the console and edit the sketch's YAML in the bay behind it,
**so that** I can change the sketch and watch the state tube change as I type.

### Acceptance Criteria
1. The printer has a **REMOVE** button (with screws drawn on the panel). Pressing it swaps the
   printer for the **bay**: the sketch's whole `sketch.yaml` in a monospace edit box, and a **sticker**
   beside it. The bay has a **REFIT PRINTER** button that puts the printer back. Both buttons work
   from the keyboard.
2. Editing saves the way the drawers do: a short pause after typing (about half a second), the text
   is checked as a whole sketch; if it passes, it is written to `sketch.yaml` (the first edit keeps
   the factory copy, so POWER on still restores it) and the tube, the controls and the rack tab
   redraw from the new sketch.
3. If the text does not pass, nothing is written; the tube keeps the last good sketch, and the bay
   shows the problem in one line (the same wording `understudy check` gives, without the file path).
   Fixing the text clears it and saves.
4. While a run plays, the edit box is read-only (and says so); Play uses the saved file.
5. Switching sketches in the rack loads that sketch's YAML into the bay; POWER on, or a save from
   a drawer while the bay is open, reloads the bay with the file's text.
6. The sticker is a cheat sheet that fits beside the edit box without scrolling at 1600x960: the top-level keys
   (`name`, `description`, `target`, `inputs`, `decide`, `questions`, `player`, `turn`), the `turn:`
   shapes (states, `on:` moves, `end`), and the input kinds (`choose`, `weight`, `count`, `switch`),
   each with one short example - taken from `docs/SKETCHES.md`.
7. Nothing else changes: with the printer on, the console looks and works as today; the run log
   prints when the printer is refitted.

## Architecture (Morpheus)

- **Save the whole file** (ADR-0028): `settings.mjs` gets `write({ sketch, text })` beside `edit` -
  the same `refusalOf` check on a copy, the same factory copy, then the text written as given. The
  allow-list (ADR-0024) still governs path edits from the drawers; whole-file writes are a separate,
  deliberate action because the owner asked to edit everything. Server: a `write` POST action;
  `GET` of a sketch's text for the bay. Refused while a run plays (409).
- **Page**: `page.html` a bay section in the printer's grid cell, hidden until REMOVE;
  `page.mjs` a debounced (500 ms) write, then the existing describe-and-redraw path; the last good
  sketch stays drawn on a 422. The edit box is a plain `<textarea>` - no editor library: a
  highlighter would be a new dependency for a nicety the owner did not ask for. A save redraws the
  tube, controls and rack but never the textarea, so the caret and undo history survive. Writes
  are sent one at a time (the next waits for the last), so a later edit never lands first.
- **Sticker**: static HTML in `page.html`, styled as a paper label; no generation.
- **Run log**: the printer keeps receiving lines while removed; refitting shows them.
- Docs: USER_GUIDE (the bay and sticker), DASHBOARD design note.
- Tests: settings unit tests for `write` (passes, refused, factory copy, refused while running);
  a browser test: remove, type a new state, tube shows it; break the YAML, problem shown, file unchanged.

## Out of Scope
- Syntax highlighting, autocomplete, or a code-editor library.
- Editing `hooks.mjs`, served pages or other files in the sketch directory.
- Removing the tube or controls panels.

rubric STORIES: OUT=S TEST=A FAIL=S SCOPE=A SIZE=A DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=S
