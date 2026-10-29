# Sprint 17 Phase 0 spike: findings

*   **Date**: 2026-10-27 · **Authors**: Neo (spike), Morpheus (decision)
*   **Method**: scratch virtualenv outside the repo (`/tmp/spike17`, CPython 3.12, `uv pip install`), synthetic data only, no live Jev call, no owner data. Scratch code is not merged.
*   **Versions tried**: `python-statemachine` 3.2.2, `typesafe-sdk` 0.7.5, `mcp` 2.3.0, `pyyaml` 6.0.3, `iso18245` 1.4.1.

## Q1. Can `python-statemachine`'s YAML express the controller's stages? **Yes, with one gap.**

- It ships a YAML reader (`statemachine.io.load("file.yaml")`) with a JSON Schema (`statechart.schema.json`). YAML is read with safe-load semantics and expressions run in a restricted evaluator ("secure by default"; arbitrary Python needs `trusted=True`).
- Schema: states take `initial`, `final`, `parallel`, `enter`, `exit`, `transitions`, `invoke`, nested `states`, `history`, `donedata`; transitions take `event`, `target`, `cond`, `unless`, `internal`, `on`, `before`, `after`. A `datamodel` section holds data items.
- **Proof 1:** the controller as five stages (`hydrate`, `pair`, `judge`, `output`, `done`) plus a `failed` final state, each with `ok` and `fail` transitions, ran from YAML: four `ok` events reached `done` (terminated), `ok` then `fail` reached `failed` (terminated).
- **Proof 2:** a `turn:`-shaped machine with guards on event data (`cond: "phase == 'asking'"`) routed `asking`, `done` and anything else correctly. Event keyword arguments are visible to guards by name (my first attempt used `_event.data[...]`, which did not match; that was my syntax, not a limit).
- **Gap:** the schema has no `tags`. Our sketch `turn:` marks states `move` and `safe`; the controller does not need them, but the Python port epic will need another way to carry them. `invoke` exists in the schema; it was not exercised here.

## Q2. Does `typesafe-sdk` return per-answer probabilities? **Yes.**

- `ChoiceAnswer` carries `choice`, `confidence` and `probabilities` (a dict of probability per option); `NoulAnswer` carries `noul` (0 to 1). That is what the 0.3 and 0.7 bands and the "top three names by probability" step need.
- Clients: sync `TypeSafeClient`, async `AsyncTypeSafeClient`; several questions go in one `system_one(state=..., questions=...)` call (from the quickstart).
- Errors are typed (`TypeSafeAPIError` and subclasses for bad request, authentication, rate limit with `retry_after_ms`, timeout, connection, response validation). `RetryPolicy(max_retries=2, timeout=30.0, retry on 429/5xx, honours Retry-After)` is built in.
- Not verified: live behaviour and batch size limits (needs the owner's go-ahead and key).

## Q3. Does the official `mcp` Python SDK serve a paged tool over stdio? **Yes.**

- A server with `describe()` and `read_transactions(offset, limit)` (1,000 rows per page, JSONL text) was called by a stdio client: **14,522 rows in 15 pages, 1.16 seconds.**
- **Version note:** `mcp` 2.x renamed `FastMCP` to `MCPServer` (`from mcp.server.mcpserver import MCPServer`) and result fields are snake_case (`structured_content`). Pin the version in `pyproject.toml`.

## Q4. Where does the MCC list come from, and can we use it? **A dependency, `iso18245` (MIT).**

- `iso18245` 1.4.1 (PyPI, MIT, released 2025-09-03) bundles the ISO 18245 code list with network descriptions: **932 codes, ISO 2003 edition, 15 range groups.** 613 of the codes are "Reserved for private use", so about 319 real codes in 14 groups remain (for example "Retail outlets" 58, "Transportation" 19, "Contracted services" 11). Each code has `iso_description` plus Visa, Mastercard, Amex, Stripe and USDA descriptions; for example 5411 is "Groceries and supermarkets".
- That fits the planned two-step choice: a Choice over about 14 groups, then a Choice over at most 58 names.
- The GitHub CSV copies state no licence, and the official ISO text is paid; the package avoids committing a list.
- **Caveat:** the package's MIT licence is verified; the licence of the underlying network descriptions it bundles is not. Offering only `iso_description` and the group names keeps us on the ISO list. Plaid's category CSV is public but states no licence either.

## Decision (task 0.2): the controller is Python

Questions 1 to 3 pass, so per `ARCH_SPRINT17.md` section 7 the ETL controller is written in Python and replaces `src/etl/run.mjs`, `src/etl/categories.mjs`, `src/etl/csv.mjs` and the ETL's use of `src/jev.mjs` outright (owner: no back-compat). The Node-DuckDB handoff disappears: one Python process owns the run database after SQLMesh exits. The SQL models, the stories and the stage contract do not change.

New Python dependencies, added through SDLC section 4 (`uv add`, commit `pyproject.toml` and `uv.lock`): `mcp` (pinned 2.x), `typesafe-sdk`, `python-statemachine[yaml]`, `iso18245`. Because `uv.lock` pins Python packages, Tank's conformance check at closeout covers them; no new make target is needed.

## Left for the owner

- A live Jev probe (a few synthetic merchants, a handful of cents) before Phase 4, if wanted.
- Confirm that deleting Sprint 16's Node ETL code is wanted. It was built, accepted and merged on 2026-10-27; replacing it follows the owner's "Python for all, no back-compat".
