import json
import tempfile
import unittest
from pathlib import Path

from src.etl.pairing import PairingError, detect_amex_account


def jsonl(directory, name, rows):
    path = Path(directory) / name
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def monarch(row, date, amount, account):
    return {"source": "monarch", "source_row_number": row, "transaction_date": date, "amount": amount,
            "merchant": "M", "account": account, "raw_record": {}}


def amex(row, date, amount):
    return {"source": "amex", "source_row_number": row, "transaction_date": date, "amount": amount,
            "merchant": "A", "account": "-11111", "raw_record": {}}


CARD = "Platinum Card (...1111)"
OTHER = "Checking (...2222)"


class DetectAmexAccountTests(unittest.TestCase):
    def files(self, directory, monarch_rows, amex_rows):
        return jsonl(directory, "m.jsonl", monarch_rows), jsonl(directory, "a.jsonl", amex_rows)

    def test_the_account_with_the_most_sign_flipped_matches_is_the_card(self):
        with tempfile.TemporaryDirectory() as directory:
            m, a = self.files(
                directory,
                [monarch(1, "2026-01-02", "-10.00", CARD), monarch(2, "2026-01-03", "-5.00", CARD),
                 monarch(3, "2026-01-02", "-10.00", OTHER)],
                [amex(1, "2026-01-02", "10.00"), amex(2, "2026-01-03", "5.00")],
            )
            result = detect_amex_account(m, a)
            self.assertEqual(result["account"], CARD)
            self.assertEqual(result["matches"], 2)

    def test_no_matches_anywhere_is_refused_naming_the_accounts_without_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            m, a = self.files(directory, [monarch(1, "2026-01-02", "-1.00", CARD)], [amex(1, "2026-05-05", "9.00")])
            with self.assertRaises(PairingError) as caught:
                detect_amex_account(m, a)
            message = str(caught.exception)
            self.assertIn("could not tell which Monarch account is the Amex card", message)
            self.assertIn("--amex-account", message)
            self.assertIn("Platinum Card (...)", message)
            self.assertNotIn("1111", message)

    def test_a_tie_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            m, a = self.files(
                directory,
                [monarch(1, "2026-01-02", "-10.00", CARD), monarch(2, "2026-01-03", "-5.00", OTHER)],
                [amex(1, "2026-01-02", "10.00"), amex(2, "2026-01-03", "5.00")],
            )
            with self.assertRaises(PairingError) as caught:
                detect_amex_account(m, a)
            self.assertIn("could not tell", str(caught.exception))

    def test_an_override_picks_the_one_account_whose_name_contains_the_text(self):
        with tempfile.TemporaryDirectory() as directory:
            m, a = self.files(directory, [monarch(1, "2026-01-02", "-1.00", CARD), monarch(2, "2026-01-02", "-1.00", OTHER)],
                              [amex(1, "2026-01-02", "1.00")])
            result = detect_amex_account(m, a, override="platinum")
            self.assertEqual(result["account"], CARD)
            self.assertEqual(result["source"], "override")

    def test_an_override_that_matches_nothing_or_two_accounts_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            m, a = self.files(directory, [monarch(1, "2026-01-02", "-1.00", CARD), monarch(2, "2026-01-02", "-1.00", OTHER)],
                              [amex(1, "2026-01-02", "1.00")])
            for text in ("zzz", "("):
                with self.assertRaises(PairingError) as caught:
                    detect_amex_account(m, a, override=text)
                self.assertIn("--amex-account", str(caught.exception))
                self.assertIn("Checking (...)", str(caught.exception))
            with self.assertRaises(PairingError):
                detect_amex_account(m, a, override="(...")

    def test_amounts_with_dollar_signs_and_commas_still_match(self):
        with tempfile.TemporaryDirectory() as directory:
            m, a = self.files(directory, [monarch(1, "2026-01-02", "-1,234.50", CARD)], [amex(1, "2026-01-02", "$1,234.50")])
            self.assertEqual(detect_amex_account(m, a)["account"], CARD)


if __name__ == "__main__":
    unittest.main()
