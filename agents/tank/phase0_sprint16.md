# Sprint 16 Phase 0: SQLMesh and DuckDB Feasibility

**Status:** Documentation-based feasibility review complete; no runtime installation, toolchain edit, CSV access, probe, or commit performed. The end-to-end handoff remains unverified until the owner approves the Python mechanism and the project exposes an approved `bobp make` entry point.

## Recommendation

Proceed with SQLMesh + DuckDB for this local workload, subject to the owner approving the mechanism below. SQLMesh supports a DuckDB gateway and SQL models, and its configuration can read environment variables. A controller can therefore pass each run's database and snapshotted input paths to SQLMesh without changing shared project files: give each SQLMesh subprocess a run-specific environment, keep a fixed project `config.yaml`, and use configured SQLMesh variables in models that read the CSV paths. The usual SQLMesh seed model is for static CSV data bundled with the project, so it is not the right loader for these per-run private snapshots.

For the category handoff, use one process at a time against the run's database. SQLMesh completes and exits after producing candidate merchants; Node opens the same DuckDB file, reads candidates and appends the validated `category_map`, then closes every connection; a new SQLMesh process runs the category/final models. Define the Node-written relation as a SQLMesh external model so SQLMesh knows its schema but does not own or recreate it. This is feasible by the documented APIs, but unprobed here.

DuckDB documents one read/write process at a time; multiple writer threads are supported only inside that writer process. Do not allow a SQLMesh subprocess to overlap Node's writable connection. The design uses a fresh database per run and serial stage transitions, so it avoids concurrent writers. DuckDB's clients share the database file format; matching the Python and Node DuckDB client versions reduces compatibility uncertainty. Consider a run-level lock / explicit stage guard before opening either writer to prevent accidental overlap.

## Proposed pinned stack

| Component | Proposed version | Basis |
|---|---:|---|
| CPython | 3.12.15 | Current installed uv-managed interpreter; SQLMesh's development prerequisites document Python 3.9 through 3.12, and this is the latest 3.12 security release. |
| uv | 0.13.0 | Already available in this environment; use `pyproject.toml` + committed `uv.lock` for deterministic transitive pins. This selects uv as the Python package manager, a mechanism change. |
| SQLMesh | 0.236.3 | Latest stable release found at review time (2026-10-17); package metadata requires Python >=3.9. |
| DuckDB Python | 1.5.6 | Current stable client; SQLMesh 0.236.3 permits DuckDB >=0.10.0 except 0.10.3. Pin exact in the lock. |
| DuckDB Node (`@duckdb/node-api`) | 1.5.6-r.1 | The npm package matching DuckDB core 1.5.6; the un-suffixed npm version does not exist. The local machine is ARM64 and the official client lists Linux ARM64 support. Pin exact in `package.json` / `package-lock.json`. |

SQLMesh and DuckDB release cadence changes quickly. Reconfirm current versions and exact SQLMesh dependency resolution during the approved install; keep all transitives in `uv.lock` and do not upgrade one DuckDB client independently.

## Proposed build interface and files

- `pyproject.toml`: project metadata and exact direct runtime pins `sqlmesh==0.236.3`, `duckdb==1.5.6`.
- `uv.lock`: exact resolved Python dependency set.
- `.python-version`: `3.12.15`.
- `.venv/`: ignored isolated Python environment.
- Add the Node dependency `@duckdb/node-api==1.5.6-r.1` to the existing npm manifest and lockfile.
- Add `install-js` and `install-py`; make existing `install` aggregate both (only aggregate target needs network access).
- Add `test-js` and `test-py`; make existing `test` aggregate both. `test-py` runs SQLMesh model tests against synthetic fixtures, not personal data.
- Keep existing `run` as the front door, with its ETL subcommand invoking `.venv/bin/sqlmesh` as a child process; do not expose a raw SQLMesh command that bypasses `bobp make` for routine tasks.
- Extend `clean` / `distclean` so `build/runs/` stays removable and `.venv/` is removed by `distclean`; add `.venv/` to `.gitignore`. Existing `build/` ignore covers private run artifacts.
- Update `docs/SDLC.md` to describe Node + Python toolchains, uv lock/install, pins, suffixed targets, aggregate gates, and mechanism approval; update README setup only after approval.

## Mechanism changes that need approval

This is a mechanism change under `docs/SDLC.md` §4 and §6: introduce Python as a second language/runtime; adopt uv and `uv.lock` as a second package-management mechanism; add Python manifest, pin, local environment and make targets; add SQLMesh/DuckDB Python dependencies; add a Node DuckDB native client dependency and lockfile change; revise aggregate install/test and clean behavior; add Python setup instructions and update SDLC.

Owner approved the recommended mechanism on 2026-10-17. npm has no published `1.5.6` version of `@duckdb/node-api`; the published `1.5.6-r.1` package carries DuckDB core 1.5.6, so the Node pin uses that exact available package version. Networked setup is authorized through `bobp make install`.

## Verification boundary and risks

- CSV handoff: SQLMesh model variables/config can be supplied per process via environment-variable configuration; the SQL model can use DuckDB's CSV reader on the snapshot paths. SQLMesh's connection config can set that same run's DuckDB database path. It is reasonable, but SQLMesh's exact behavior for an ephemeral per-run DB and changing variables across `plan`/selected-model stages still needs an isolated smoke probe.
- Category handoff: DuckDB's official Node client opens persistent database files and SQLMesh can describe externally managed tables. Correct sequential close/open is the design; append/read interoperability has not been exercised here.
- The build target changes and Python install cannot be probed through the repository's existing Makefile: there is no Python target/environment, and task instructions explicitly withhold approval for adding one. Do not use a raw `uv sync`, pip install, or one-off SQLMesh invocation as a workaround.
- If the approved probe fails, first evaluate a run-scoped category CSV bridge loaded by SQLMesh as the small alternative; do not implement a custom relational operator layer or introduce DuckDB's Quack service for a ~4.7k-row local run.

## Official references reviewed

- [SQLMesh DuckDB connection guide](https://sqlmesh.readthedocs.io/en/stable/guides/connections/)
- [SQLMesh configuration and environment variables](https://sqlmesh.readthedocs.io/en/stable/guides/configuration/)
- [SQLMesh seed models](https://sqlmesh.readthedocs.io/en/stable/concepts/models/seed_models/) — explains why seeds are static project CSVs.
- [SQLMesh external models](https://sqlmesh.readthedocs.io/en/stable/concepts/models/external_models/) — SQLMesh records schema metadata but does not run/manage the external table.
- [SQLMesh 0.236.3 package metadata](https://pypi.org/project/sqlmesh/)
- [SQLMesh 0.236.3 dependency metadata](https://raw.githubusercontent.com/SQLMesh/sqlmesh/v0.236.3/pyproject.toml)
- [DuckDB concurrency](https://duckdb.org/docs/current/connect/concurrency)
- [DuckDB Node Neo client](https://duckdb.org/docs/current/clients/node_neo/overview)
- [DuckDB storage compatibility](https://duckdb.org/docs/current/internals/storage)
- [Python 3.12.15 release](https://www.python.org/downloads/release/python-31215/)
