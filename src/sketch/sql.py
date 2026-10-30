"""Stage SQL runs on DuckDB, in the run's own database (`run.duckdb`), so a run can be inspected afterwards."""

import json
from decimal import Decimal
from pathlib import Path

import duckdb


def _plain(value):
    return float(value) if isinstance(value, Decimal) else value


def query(directory: Path, sql: str, tables: dict[str, list[dict]]) -> list[dict]:
    """Load each named table from its rows, run the SQL, and return its rows as dicts (None values dropped)."""
    with duckdb.connect(str(directory / "run.duckdb")) as connection:
        for name, rows in tables.items():
            staged = directory / f".{name}.jsonl"
            staged.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            connection.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_json_auto('{staged}')")
            staged.unlink()
        cursor = connection.execute(sql)
        names = [column[0] for column in cursor.description]
        rows = [dict(zip(names, (_plain(v) for v in row), strict=True)) for row in cursor.fetchall()]
    return [{k: v for k, v in row.items() if v is not None} for row in rows]
