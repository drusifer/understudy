import tempfile
import unittest
from pathlib import Path

import duckdb

from src.etl.decisions import store


class StoreTests(unittest.TestCase):
    def test_writes_rows_with_the_given_columns_and_replaces_an_earlier_table(self):
        with tempfile.TemporaryDirectory() as directory:
            with duckdb.connect(str(Path(directory) / "run.duckdb")) as connection:
                connection.execute("CREATE SCHEMA etl__dev")
                columns = {"payee_key": "VARCHAR", "probability": "DOUBLE"}
                store(connection, "etl__dev.transfer_judgment", columns, [{"payee_key": "venmo", "probability": 0.05}])
                store(connection, "etl__dev.transfer_judgment", columns,
                      [{"payee_key": "zelle", "probability": 0.04}, {"payee_key": "bank", "probability": 0.9}])
                rows = connection.execute("select payee_key, probability from etl__dev.transfer_judgment order by 1").fetchall()
        self.assertEqual(rows, [("bank", 0.9), ("zelle", 0.04)])

    def test_an_empty_list_still_creates_the_table(self):
        with tempfile.TemporaryDirectory() as directory:
            with duckdb.connect(str(Path(directory) / "run.duckdb")) as connection:
                store(connection, "decisions", {"id": "VARCHAR"}, [])
                self.assertEqual(connection.execute("select count(*) from decisions").fetchone(), (0,))

    def test_nulls_are_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            with duckdb.connect(str(Path(directory) / "run.duckdb")) as connection:
                store(connection, "decisions", {"id": "VARCHAR", "confidence": "DOUBLE"}, [{"id": "a", "confidence": None}])
                self.assertEqual(connection.execute("select confidence from decisions").fetchone(), (None,))


if __name__ == "__main__":
    unittest.main()
