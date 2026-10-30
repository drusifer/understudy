import asyncio
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import duckdb

from src.sketch.stages_table import store, table

ROWS = [{"id": "a", "amount": 1.5}, {"id": "b", "amount": 2.0}]
COLUMNS = {"id": "VARCHAR", "amount": "DOUBLE"}


def context(directory, **sources):
    async def read(name):
        return sources[name]

    return SimpleNamespace(directory=Path(directory), read=read)


class TableTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = directory.name

    def test_stored_rows_are_read_back_in_the_order_asked(self):
        ctx = context(self.directory, answers=ROWS)
        asyncio.run(store(ctx, "answers", "main.answers", COLUMNS))
        self.assertEqual(asyncio.run(table(ctx, "main.answers", order="amount DESC")), ROWS[::-1])

    def test_storing_again_replaces_the_table_and_no_rows_leave_it_empty(self):
        ctx = context(self.directory, answers=ROWS, nothing=[])
        asyncio.run(store(ctx, "answers", "main.answers", COLUMNS))
        asyncio.run(store(ctx, "nothing", "main.answers", COLUMNS))
        self.assertEqual(asyncio.run(table(ctx, "main.answers")), [])

    def test_dates_and_decimals_come_back_as_json_values(self):
        with duckdb.connect(str(Path(self.directory) / "run.duckdb")) as connection:
            connection.execute("CREATE TABLE made AS SELECT DATE '2026-03-01' AS day, 4.50::DECIMAL(18, 2) AS cost")
        self.assertEqual(asyncio.run(table(context(self.directory), "made")), [{"day": date(2026, 3, 1).isoformat(), "cost": 4.5}])


if __name__ == "__main__":
    unittest.main()
