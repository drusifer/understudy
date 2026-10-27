import json
import tempfile
import unittest
from pathlib import Path

from src.etl.csv_to_jsonl import convert_csv_to_jsonl


class CsvToJsonlTests(unittest.TestCase):
    def test_normalizes_us_dates_for_sql_but_preserves_the_original_value(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            source = temporary / "amex.csv"
            destination = temporary / "amex.jsonl"
            source.write_text(
                "Date,Amount,Description\n01/02/2026,12.50,Cafe Local\n",
                encoding="utf-8",
            )

            convert_csv_to_jsonl(
                source, destination, "amex", "Date", "Amount", "Description"
            )

            row = json.loads(destination.read_text().splitlines()[0])
            self.assertEqual(row["transaction_date"], "2026-01-02")
            self.assertEqual(row["raw_record"]["Date"], "01/02/2026")

    def test_converts_flat_rows_preserving_quoted_values_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            source = temporary / "input.csv"
            destination = temporary / "output.jsonl"
            source.write_text(
                '\ufeffDate,Amount,Merchant,Notes\n'
                '2026-01-02,12.50,"Cafe, Local","line one\nline two"\n',
                encoding="utf-8",
            )

            count = convert_csv_to_jsonl(
                source, destination, "monarch", "Date", "Amount", "Merchant"
            )

            rows = [json.loads(line) for line in destination.read_text().splitlines()]
            self.assertEqual(count, 1)
            self.assertEqual(rows[0]["source"], "monarch")
            self.assertEqual(rows[0]["source_row_number"], 1)
            self.assertEqual(rows[0]["merchant"], "Cafe, Local")
            self.assertEqual(rows[0]["raw_record"]["Notes"], "line one\nline two")

    def test_rejects_unmapped_columns(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            source = temporary / "input.csv"
            source.write_text("Date,Amount\n2026-01-02,12.50\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Merchant"):
                convert_csv_to_jsonl(
                    source, temporary / "output.jsonl", "amex", "Date", "Amount", "Merchant"
                )


if __name__ == "__main__":
    unittest.main()
