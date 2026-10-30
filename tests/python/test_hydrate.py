import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.etl.hydrate import hydrate
from src.etl.sources import SourceError

HEADER = "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags,Owner,Reviewed,Id\n"


def monarch_file(directory, count):
    rows = "".join(f"2026-01-01,Shop {i % 7},Cat,Card (...1111),S{i},,-1.00,,Me,,id{i}\n" for i in range(count))
    path = Path(directory) / "monarch.csv"
    path.write_text(HEADER + rows, encoding="utf-8")
    return path


class HydrateTests(unittest.TestCase):
    def test_reads_an_export_into_a_jsonl_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            source = monarch_file(directory, 2500)
            destination = Path(directory) / "inputs" / "monarch.jsonl"
            result = hydrate("monarch", source, destination)
            lines = destination.read_text(encoding="utf-8").splitlines()
            self.assertEqual(result["rows"], 2500)
            self.assertEqual(len(lines), 2500)
            self.assertEqual(json.loads(lines[0])["source_row_number"], 1)
            self.assertEqual(json.loads(lines[-1])["source_row_number"], 2500)
            self.assertEqual(result["sha256"], hashlib.sha256(destination.read_bytes()).hexdigest())

    def test_a_missing_file_stops_before_anything_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "inputs" / "monarch.jsonl"
            with self.assertRaises(SourceError) as caught:
                hydrate("monarch", Path(directory) / "missing.csv", destination)
            self.assertIn("missing.csv", str(caught.exception))
            self.assertFalse(destination.exists())
            self.assertFalse(destination.parent.exists())

    def test_a_missing_column_stops_before_anything_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            broken = Path(directory) / "amex.csv"
            broken.write_text("Date,Description\n01/02/2026,X\n", encoding="utf-8")
            destination = Path(directory) / "inputs" / "amex.jsonl"
            with self.assertRaises(SourceError) as caught:
                hydrate("amex", broken, destination)
            self.assertIn("amount", str(caught.exception))
            self.assertFalse(destination.exists())

    def test_the_snapshot_is_the_same_on_every_run(self):
        with tempfile.TemporaryDirectory() as directory:
            source = monarch_file(directory, 120)
            first = hydrate("monarch", source, Path(directory) / "a.jsonl")
            second = hydrate("monarch", source, Path(directory) / "b.jsonl")
            self.assertEqual(first["sha256"], second["sha256"])


if __name__ == "__main__":
    unittest.main()
