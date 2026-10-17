# Sprint 11 Story + Architecture (Tier 2): Light and dark

*   **Total Points**: 5 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-11` (cut from `sprint-10`, which awaits merge - this sprint builds on it)
*   **Source**: owner, 2026-10-16: "make sure all themes have light and dark mode versions"; the
    mode follows the device by default, with a LIGHT / DARK / AUTO switch remembered per browser
    ("yup"). Recorded in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gates 1 and 2 (2026-10-16)

## STORY-UND-38: Every theme in light and dark
**Points:** 5

**As the** owner,
**I want** each theme - steampunk, professional, starship - in a light and a dark version that
follows my device's setting unless I choose,
**so that** the console is comfortable in a bright room and at night, whichever look I pick.

### Acceptance Criteria
1. The header has a **MODE** switch: **AUTO** (the default), **LIGHT**, **DARK**. AUTO follows the
   device's light/dark setting and changes with it while the page is open; LIGHT and DARK fix it.
   The choice is remembered in that browser, like the theme; `?mode=light` / `?mode=dark` /
   `?mode=auto` on the link wins, and an unknown value is ignored.
2. Six looks: **steampunk dark** (today's console) and **light** (parchment and polished brass;
   the tube and the Nixie readouts stay dark glass, as devices); **professional light** (today's)
   and **dark** (charcoal panels, light text, the same blue accent lightened); **starship dark**
   (today's) and **light** (the same coloured elbow bars and pills on a pale grey screen, dark
   readout text).
3. Switching mode restyles at once, keeps the theme, keeps a run going, and the tube redraws in the
   mode's colours.
4. Each of the six fits one 1600x960 screen and a 390px-wide phone without sideways scrolling; the
   weight colours stay distinct; the page's main text and its background differ in each.

## Architecture (Morpheus)

- **Mode = a second attribute** (ADR-0032): `<html data-theme=... data-mode="light|dark">`, set by
  the script from `modeOf(query, stored, systemIsDark)` (pure, unit-tested) and a `matchMedia`
  listener while AUTO. Each theme's default stays as it is; the other mode is an override block
  under `:root[data-theme="X"][data-mode="Y"]`.
- **Colours as variables**: `theme-professional.css` and `theme-starship.css` are rewritten so every
  colour comes from a few custom properties (surface, line, ink, muted, accent...); their other
  mode only redefines those. Steampunk light is a new `theme-steampunk-light.css` overriding
  `page.css`'s surfaces (its hard-coded brass and wood stay in `page.css`).
- The script's tube colours already come from CSS variables (ADR-0029); each mode sets its own.
- Tests: `modeOf` unit; browser: every theme x mode applies, light and dark backgrounds differ,
  fits 1600x960 and 390px, AUTO follows an emulated dark/light device, `?mode=` wins, remembered
  across a reload.
- Docs: USER_GUIDE (mode switch), DASHBOARD design table (six looks), screenshots.

## Out of Scope
- Per-sketch modes; a scheduled (time-of-day) mode; the watch page.

rubric STORIES: OUT=S TEST=A FAIL=A SCOPE=A SIZE=A DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=A
