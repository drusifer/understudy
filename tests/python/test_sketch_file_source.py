import tempfile
import unittest
from pathlib import Path

from src.sketch.sources.file import read_csv, read_rows


class FileSourceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)

    def test_a_csv_has_its_header_row_as_field_names_and_text_values(self):
        path = self.dir / "export.csv"
        path.write_text("﻿Date,Merchant,Amount\n2026-03-01,\"Dunkin', Inc\",-4.50\n2026-03-02,Store,\n", encoding="utf-8")
        self.assertEqual(read_csv(path), [
            {"Date": "2026-03-01", "Merchant": "Dunkin', Inc", "Amount": "-4.50"},
            {"Date": "2026-03-02", "Merchant": "Store", "Amount": ""}])

    def test_the_name_picks_the_format(self):
        (self.dir / "a.csv").write_text("n\n1\n", encoding="utf-8")
        (self.dir / "a.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
        self.assertEqual(read_rows(self.dir / "a.csv"), [{"n": "1"}])
        self.assertEqual(read_rows(self.dir / "a.jsonl"), [{"n": 1}])


if __name__ == "__main__":
    unittest.main()
