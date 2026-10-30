"""Stages over the run's database (`run.duckdb` in the run folder): read a table as rows, store rows as a table.

SQL models write the tables they compute; `store` is how a sketch hands rows (Jev's answers, say) back to them.
"""

import duckdb

from src.etl.decisions import store as write_table
from src.sketch.registry import Source, stage
from src.sketch.sql import plain

DATABASE = "run.duckdb"


@stage("map.table")
async def table(context, name: str, order: str | None = None) -> list[dict]:
    """The rows of table `name` in the run's database, in `order` (a column list) when one is given."""
    sql = f"SELECT * FROM {name}" + (f" ORDER BY {order}" if order else "")
    with duckdb.connect(str(context.directory / DATABASE), read_only=True) as connection:
        cursor = connection.execute(sql)
        names = [column[0] for column in cursor.description]
        return [{n: plain(v) for n, v in zip(names, row, strict=True)} for row in cursor.fetchall()]


@stage("map.store")
async def store(context, source: Source, table: str, columns: dict) -> list[dict]:
    """Replace table `table` in the run's database with the rows of `source`; `columns` maps each column to its DuckDB type."""
    rows = await context.read(source)
    with duckdb.connect(str(context.directory / DATABASE)) as connection:
        write_table(connection, table, columns, rows)
    return rows
