# Sprint 10 Story + Architecture (Tier 2): A schema for sketch.yaml

*   **Total Points**: 3 (Tier 2 - story and architecture in one document)
*   **Branch**: `sprint-10`
*   **Source**: owner, 2026-10-16: asked how the YAML syntax is documented; the reference is
    complete but editors give no help while typing - "add the schema validation". Recorded in
    `agents/CHAT.md`.
*   **Status**: Approved at Smith Gates 1 and 2 (2026-10-16)

## STORY-UND-37: The editor knows the sketch format
**Points:** 3

**As an** automation author,
**I want** my editor to complete `sketch.yaml` keys and underline mistakes as I type,
**so that** I find a typo before running `check`, and see what each key means without opening the docs.

### Acceptance Criteria
1. `schema/sketch.schema.json` (JSON Schema draft-07) describes `sketch.yaml`: every top-level key,
   each target kind with only its own fields, MCP server entries, `calls`, `values` (lists or
   `{ input: }`), `decide` (gates, scores, shortlist, `when:`, `{ input: }` bounds), the four input
   kinds, `pick`, `player`, `questions` (choice / noul / score) and `turn` (flat states, `on`,
   `invoke`, guards, tags, `type: final`). Each key carries a one-line description from
   `docs/SKETCHES.md`.
2. Every example's `sketch.yaml` starts with a `# yaml-language-server: $schema=...` line, so an
   editor with the YAML language server (VS Code's YAML extension, Neovim, JetBrains) validates and
   completes it with no setup. `docs/SKETCHES.md` says how to add the line to your own sketch.
3. The schema accepts every example, and rejects - with the path of the mistake - an unknown top-level
   key, an unknown target kind, a field of another target kind, an input with two kinds, a question
   of an unknown type, and a misspelt state key (e.g. `invok:`).
4. The schema stays in step with `check`: a test fails if the schema's top-level keys, target
   kinds and fields, input kinds or question types differ from the ones `check` knows.
5. `understudy check` is unchanged: it stays the full check (names, states, prose rules, files),
   with its own messages; the schema is the editor's quick, structural half.

## Architecture (Morpheus)

- **The schema is a file, not code** (ADR-0031): hand-written JSON Schema draft-07 (the version the
  YAML language server supports best) in `schema/sketch.schema.json`, beside the sources it
  describes. `check` does not load it - its own checks say more (nearest names, file paths, prose rules).
- **Kept honest by tests**: `ajv` (dev dependency, routine via SDLC §4) validates every
  `examples/*/sketch.yaml` and a set of broken ones; `sketch.mjs` and `inputs.mjs` export the lists
  they check against (`KEYS`, `TARGET_FIELDS`, `QUESTION_TYPES`, input `KINDS`) and a test compares
  them with the schema.
- **Turn states** list the XState keys a flat turn uses (`description`, `tags`, `type`, `on`,
  `after`, `always`, `entry`, `exit`, `invoke`, `meta`); others are flagged.
- Docs: SKETCHES ("Editor help"), README link.

## Out of Scope
- `check` running the schema; schema-driven completion in the dashboard's bay.
- Publishing the schema to a schema store.

rubric STORIES: OUT=S TEST=S FAIL=A SCOPE=A SIZE=A DESIGN=A · rubric ARCH: BOUND=S FLOW=A FAIL=A USER=A DECS=A FEAS=A
