"""UND-98: the crosswalk puts the tool's category beside the export's for every merchant, flagged where they differ about
money moving.

These test the household's `crosswalk` stage with Jev's placements written in (`decided`); no whole run is needed.
"""

import unittest

from household_fragment import ORACLE, decided, fragment, placed_all, without_lines

ORIGINAL = (ORACLE / "monarch.csv").read_text(encoding="utf-8")


def crosswalk(monarch: str | None = None):
    """The crosswalk lines, by payee, and the summary the stage noted. The fixture's export gets the child sketch's real
    answers; a changed export gets written placements (which category a merchant is in does not matter to these tests)."""
    placements = decided() if monarch is None else placed_all(monarch)
    rows, summary = fragment("crosswalk", monarch=monarch, decided=placements)
    return rows, {row["payee"]: row for row in rows}, summary


class CrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.by, cls.summary = crosswalk()

    def test_every_merchant_has_a_line_with_its_records_its_money_and_both_categories(self):
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

    def test_a_payment_the_run_linked_says_so_instead_of_showing_no_category(self):
        for payee in ("Payment Thank You", "Amex Payment"):
            self.assertEqual(self.by[payee]["tool_category"], "Transfer (linked payment)", payee)

    def test_the_summary_counts_the_flagged_merchants(self):
        flagged = sum(1 for row in self.rows if row["differs_on_money_moving"])
        self.assertEqual(self.summary["crosswalk_flagged"].get("True", 0), flagged)  # a count by value, so the keys are text
        self.assertEqual(sum(self.summary["crosswalk_flagged"].values()), len(self.rows))


class UnpairedPaymentTests(unittest.TestCase):
    def test_a_card_payment_received_with_no_bank_side_says_it_is_a_card_payment(self):
        alone = without_lines(ORIGINAL, ",m9")
        self.assertNotEqual(alone, ORIGINAL)
        _, by, _ = crosswalk(alone)
        self.assertEqual(by["Payment Thank You"]["tool_category"], "Transfer (card payment received)")


class FlagTests(unittest.TestCase):
    def test_a_merchant_the_label_rule_calls_a_transfer_and_the_tool_does_not_is_flagged(self):
        extra = '2026-03-09,Savings Move,"Transfer",Checking (...2222),SAVINGS MOVE,,-50.00,,Me,,m16\n'
        _, by, summary = crosswalk(ORIGINAL + extra)
        self.assertTrue(by["Savings Move"]["differs_on_money_moving"])  # the export says Transfer, the tool says purchase
        self.assertGreaterEqual(summary["crosswalk_flagged"]["True"], 1)

    def test_a_merchant_the_tool_calls_a_transfer_and_the_label_rule_does_not_is_flagged(self):
        changed = ORIGINAL.replace('Payment Thank You,"Credit Card Payment"', 'Payment Thank You,"Income: Paychecks"')
        _, by, _ = crosswalk(changed)
        self.assertTrue(by["Payment Thank You"]["differs_on_money_moving"])  # linked, so a transfer, whatever the label says
        self.assertFalse(by["Amex Payment"]["differs_on_money_moving"])


if __name__ == "__main__":
    unittest.main()
