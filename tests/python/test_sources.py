import tempfile
import unittest
from pathlib import Path

from src.etl.sources import SourceError, describe, read_page

MONARCH = (
    "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags,Owner,Reviewed,Id\n"
    '2026-01-02,"Cafe, Local",Coffee Shops,Card (...1111),CAFE LOCAL 123,,-12.50,,Me,,m1\n'
    "2026-01-03,Monarch Only,Shopping,Checking (...2222),MONARCH ONLY,,-9.00,,Me,,m2\n"
)
AMEX = (
    "Date,Description,Card Member,Account #,Amount,Extended Details,Appears On Your Statement As\n"
    '01/02/2026,CAFE LOCAL,A PERSON,-11111,12.50,"line one\nline two\nline three",CAFE LOCAL\n'
    "01/04/2026,AMEX ONLY,A PERSON,-11111,3.25,more,AMEX ONLY\n"
)


def write(directory, name, text):
    path = Path(directory) / name
    path.write_text(text, encoding="utf-8")
    return path


class SourceReaderTests(unittest.TestCase):
    def test_describe_counts_rows_and_a_multiline_row_is_one_record(self):
        with tempfile.TemporaryDirectory() as directory:
            amex = write(directory, "amex.csv", AMEX)
            info = describe(amex, "amex")
            self.assertEqual(info["rows"], 2)
            self.assertIn("Extended Details", info["columns"])

    def test_records_carry_source_row_number_normalized_fields_and_every_column(self):
        with tempfile.TemporaryDirectory() as directory:
            monarch = write(directory, "monarch.csv", MONARCH)
            first, second = read_page(monarch, "monarch", 0, 10)
            self.assertEqual(first["source"], "monarch")
            self.assertEqual(first["source_row_number"], 1)
            self.assertEqual(second["source_row_number"], 2)
            self.assertEqual(first["transaction_date"], "2026-01-02")
            self.assertEqual(first["amount"], "-12.50")
            self.assertEqual(first["merchant"], "Cafe, Local")
            self.assertEqual(first["account"], "Card (...1111)")
            self.assertEqual(first["raw_record"]["Original Statement"], "CAFE LOCAL 123")
            self.assertEqual(set(first["raw_record"]), set(MONARCH.splitlines()[0].split(",")))

    def test_amex_dates_are_normalized_but_the_original_text_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            amex = write(directory, "amex.csv", AMEX)
            first, _ = read_page(amex, "amex", 0, 10)
            self.assertEqual(first["transaction_date"], "2026-01-02")
            self.assertEqual(first["raw_record"]["Date"], "01/02/2026")
            self.assertEqual(first["merchant"], "CAFE LOCAL")
            self.assertEqual(first["account"], "-11111")
            self.assertEqual(first["raw_record"]["Extended Details"], "line one\nline two\nline three")

    def test_pages_are_slices_and_a_page_past_the_end_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            monarch = write(directory, "monarch.csv", MONARCH)
            self.assertEqual([r["source_row_number"] for r in read_page(monarch, "monarch", 1, 1)], [2])
            self.assertEqual(read_page(monarch, "monarch", 2, 10), [])

    def test_a_page_is_never_larger_than_one_thousand_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = "".join(f"2026-01-01,Shop {i},Cat,Acct,S,,-1.00,,Me,,id{i}\n" for i in range(1500))
            monarch = write(directory, "monarch.csv", MONARCH.splitlines()[0] + "\n" + rows)
            self.assertEqual(len(read_page(monarch, "monarch", 0, 5000)), 1000)

    def test_a_missing_file_is_named(self):
        with self.assertRaises(SourceError) as caught:
            describe(Path("/nonexistent/monarch.csv"), "monarch")
        self.assertIn("Monarch CSV cannot be read", str(caught.exception))
        self.assertIn("/nonexistent/monarch.csv", str(caught.exception))

    def test_a_missing_column_names_the_file_and_the_column(self):
        with tempfile.TemporaryDirectory() as directory:
            broken = write(directory, "amex.csv", "Date,Description\n01/02/2026,X\n")
            with self.assertRaises(SourceError) as caught:
                describe(broken, "amex")
            message = str(caught.exception)
            self.assertIn("amex.csv", message)
            self.assertIn("amount", message)

    def test_an_unknown_source_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write(directory, "x.csv", MONARCH)
            with self.assertRaises(SourceError):
                describe(path, "chase")


if __name__ == "__main__":
    unittest.main()
