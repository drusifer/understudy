"""UND-98: the crosswalk puts the tool's category beside the export's for every merchant, flagged where they differ about
money moving."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from household_jev import choose, first_choice
from jev_double import JevDouble
from test_household import LEDGER, ORACLE, lines, no_pins

from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore


def run_crosswalk(monarch_text: str, jev=first_choice):
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        (directory / "monarch.csv").write_text(monarch_text, encoding="utf-8")
        code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={directory / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
             *no_pins(directory)],
            make_jev=lambda: JevDouble(choose_fn=jev), store=CaptureStore(directory / "cache"),
            stdout=io.StringIO(), stderr=io.StringIO())
        (folder,) = (directory / "out").iterdir()
        return code, lines(folder / "crosswalk.jsonl"), json.loads((folder / "summary.json").read_text(encoding="utf-8"))


ORIGINAL = (ORACLE / "monarch.csv").read_text(encoding="utf-8")


class CrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.rows, cls.summary = run_crosswalk(ORIGINAL, jev=choose)
        cls.by = {row["payee"]: row for row in cls.rows}

    def test_every_merchant_has_a_line_with_its_records_its_money_and_both_categories(self):
        self.assertEqual(self.code, 0)
        for row in self.rows:
            self.assertEqual(set(row), {"payee", "count", "amount", "tool_category", "export_category",
                                        "differs_on_money_moving"})
        self.assertEqual({"Store", "Employer", "Shoe Shop", "Venmo", "Dunkin'", "Ridgewood Savings Bank"} - set(self.by), set())
        store = self.by["Store"]
        self.assertEqual((store["export_category"], store["count"]), ("Shopping & Retail: General", 3))
        self.assertTrue(store["tool_category"])
        self.assertNotIn("Shopping & Retail", store["tool_category"])

    def test_the_lines_run_from_the_most_money_to_the_least(self):
        self.assertEqual(self.rows[0]["payee"], "Employer")  # a 2,000 deposit is the most money in the fixture
        self.assertEqual(self.rows[-1]["payee"], "Dunkin'")  # 11.20 is the least

    def test_a_merchant_both_sides_call_a_transfer_is_not_flagged_and_an_unplaced_one_has_no_tool_category(self):
        bank = self.by["Ridgewood Savings Bank"]
        self.assertEqual((bank["tool_category"], bank["export_category"], bank["differs_on_money_moving"]),
                         ("Household: Transfer", "Transfer", False))
        self.assertIsNone(self.by["Venmo"]["tool_category"])  # no group fits: for review, so no category yet

    def test_the_summary_counts_the_flagged_merchants(self):
        flagged = sum(1 for row in self.rows if row["differs_on_money_moving"])
        self.assertEqual(self.summary["crosswalk_flagged"].get("True", 0), flagged)  # a count by value, so the keys are text
        self.assertEqual(sum(self.summary["crosswalk_flagged"].values()), len(self.rows))


class FlagTests(unittest.TestCase):
    def test_a_merchant_the_label_rule_calls_a_transfer_and_the_tool_does_not_is_flagged(self):
        extra = '2026-03-09,Savings Move,"Transfer",Checking (...2222),SAVINGS MOVE,,-50.00,,Me,,m16\n'
        _, rows, summary = run_crosswalk(ORIGINAL + extra)
        by = {row["payee"]: row for row in rows}
        self.assertTrue(by["Savings Move"]["differs_on_money_moving"])  # the export says Transfer, the tool says purchase
        self.assertGreaterEqual(summary["crosswalk_flagged"]["True"], 1)

    def test_a_merchant_the_tool_calls_a_transfer_and_the_label_rule_does_not_is_flagged(self):
        changed = ORIGINAL.replace('Payment Thank You,"Credit Card Payment"', 'Payment Thank You,"Income: Paychecks"')
        _, rows, _ = run_crosswalk(changed)
        by = {row["payee"]: row for row in rows}
        self.assertTrue(by["Payment Thank You"]["differs_on_money_moving"])  # linked, so a transfer, whatever the label says
        self.assertFalse(by["Amex Payment"]["differs_on_money_moving"])


if __name__ == "__main__":
    unittest.main()
