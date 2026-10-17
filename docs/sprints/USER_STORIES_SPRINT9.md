# Sprint 9 Story + Architecture (Tier 2): Themes

*   **Total Points**: 5 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-9`
*   **Source**: owner, 2026-10-16: "css themes - make one professional theme and another that is
    startrek next gen themed like the screens on the enterprise". Recorded in `agents/CHAT.md`.
*   **Status**: Approved at Smith Gates 1 and 2 (2026-10-16)

## STORY-UND-36: Choose the console's theme
**Points:** 5

**As the** owner,
**I want** to switch the dashboard between the steampunk console, a plain professional look and a
starship look like the Enterprise-D's computer screens,
**so that** I can show it to people who want something sober, or have fun with it.

### Acceptance Criteria
1. The header has a **THEME** switch with three choices: **STEAMPUNK** (today's console, the
   default), **PROFESSIONAL** and **STARSHIP**. Choosing one restyles the whole page at once, with
   no reload, and a run in progress keeps going.
2. The choice is remembered in that browser: reload the page and the same theme comes back. A link
   with `?theme=starship` (or `professional`, `steampunk`) opens in that theme; an unknown name is
   ignored and the remembered or default theme is used.
3. **PROFESSIONAL**: light background, dark text, one blue accent, a plain sans-serif system font;
   flat panels with thin borders, no glows, textures or animations; the tube is a flat diagram on a
   white disc; the printer is a plain log with monospace text. Text meets WCAG AA contrast (4.5:1).
4. **STARSHIP**: black background; panels framed by thick rounded "elbow" bars in the familiar
   orange / lilac / peach / blue palette; pill-shaped buttons; condensed upper-case lettering;
   the tube is a black display with thin coloured lines; the printer is a readout of coloured text
   on black. Original styling only - no logos, insignia or copied artwork.
5. Every control works the same in every theme (dial, faders, stepper, switches, PLAY/STOP, POWER,
   the rack, the drawers, REMOVE / REFIT and the bay); the weight colours stay distinct from each
   other within each theme.
6. All three themes fit one 1600x960 screen, as today.

## Architecture (Morpheus)

- **Theme = an attribute and a stylesheet** (ADR-0029): `<html data-theme="steampunk|professional|starship">`.
  `page.css` keeps the layout and the steampunk look (the default); `theme-professional.css` and
  `theme-starship.css` override it under `[data-theme=...]`. All three are always loaded (small,
  local files), so a switch is instant.
- **Colours drawn by script** (the tube's states, edges, labels, weight colours) move into CSS
  custom properties (`--tube-*`, `--weight-1..4`) read with `getComputedStyle` at draw time; the
  tube and controls redraw on a theme change. No colour stays hard-coded in `page.mjs`.
- **The switch**: a three-way segmented control in the header; `?theme=` wins, else
  `localStorage` (read and written in try/catch - a blocked store means the default), else
  steampunk. A pure `themeOf(query, stored)` is unit-tested.
- **Fonts**: professional uses the system UI font stack (nothing new); starship uses **Antonio**
  from `@fontsource/antonio` (OFL), served locally like the other fonts - a routine dependency
  through SDLC §4.
- Docs: USER_GUIDE (themes), DASHBOARD design note (a section per theme); screenshots.
- Tests: `themeOf` unit test; a browser test switches each theme, checks the page restyles (body
  background), every control still works (Play runs), the choice survives a reload, `?theme=`
  wins, and the console fits 1600x960.

## Out of Scope
- Theme editing, more than three themes, or per-sketch themes.
- A dark professional theme; sounds.
- The watch page (`understudy watch`) - it keeps its own look.

rubric STORIES: OUT=S TEST=A FAIL=A SCOPE=S SIZE=A DESIGN=A · rubric ARCH: BOUND=A FLOW=A FAIL=A USER=A DECS=A FEAS=A
