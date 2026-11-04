"""UND-99: each card payment is tied to the charges it settled, and the report says what they were for.

These are tests of the household's rules, so they compute the sketch's own stages from the fixture exports (`fragment`), with
Jev's placements written in; no whole run is needed. The sinks and the summary file of a whole run are checked once, in
`test_household.LedgerTests`.
"""

import unittest

from household_fragment import ORACLE, fragment, placed, without_lines

CATEGORIES = placed({"store": "Retail outlets: Bakeries", "dunkin'": "Retail outlets: Bakeries"})  # the shoe shop is for review
MONARCH = (ORACLE / "monarch.csv").read_text(encoding="utf-8")


class PaymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payments, _ = fragment("payments", categories=CATEGORIES)
        cls.records, _ = fragment("final_records", categories=CATEGORIES)
        _, cls.summary = fragment("open_balance_noted", categories=CATEGORIES)
        cls.by_payee = {}
        for record in cls.records:
            cls.by_payee.setdefault(record["payee"], []).append(record)

    def test_the_card_payment_has_a_line_with_what_it_settled_and_what_is_left(self):
        (payment,) = self.payments
        self.assertEqual((payment["day"], payment["amount"]), ("2026-03-02", 500.0))
        self.assertEqual((payment["charges"], payment["settled"], payment["remainder"]), (3, 125.0, 375.0))
        self.assertEqual(set(payment), {"payment_id", "day", "card", "amount", "charges", "settled", "remainder",
                                        "unexplained", "top"})

    def test_a_payment_with_much_left_over_says_it_is_partly_unexplained(self):
        self.assertTrue(self.payments[0]["unexplained"])  # 375 of 500 has no earlier charge to explain it

    def test_a_payment_that_explains_nearly_all_of_itself_is_not_flagged(self):
        small = MONARCH.replace("500.00,,Me,,m8", "126.00,,Me,,m8").replace("-500.00,,Me,,m9", "-126.00,,Me,,m9")
        amex = (ORACLE / "amex.csv").read_text(encoding="utf-8").replace("-500.00", "-126.00")
        payments, _ = fragment("payments", monarch=small, amex=amex, categories=CATEGORIES)
        self.assertEqual((payments[0]["settled"], payments[0]["remainder"], payments[0]["unexplained"]), (125.0, 1.0, False))

    def test_the_largest_categories_of_the_settled_charges_carry_their_amounts_and_shares(self):
        top = self.payments[0]["top"]
        self.assertEqual([entry["amount"] for entry in top], sorted((e["amount"] for e in top), reverse=True))
        self.assertEqual(sum(entry["amount"] for entry in top), 125.0)
        self.assertAlmostEqual(sum(entry["share"] for entry in top), 1.0, places=3)
        self.assertEqual(next(e for e in top if e["category"] == "Retail outlets: Bakeries")["amount"], 95.0)
        self.assertIn("unplaced", {entry["category"] for entry in top})  # the shoe shop is for review

    def test_at_most_five_categories_are_listed_for_a_payment(self):
        names = [f"shop {n}" for n in range(7)]
        monarch = MONARCH + "".join(
            f"2026-02-{10 + n},{name.title()},\"Cat\",Platinum Card (...1111),{name.upper()},,-{n + 1}.00,,Me,,x{n}\n"
            for n, name in enumerate(names))
        amex = (ORACLE / "amex.csv").read_text(encoding="utf-8") + "".join(
            f"02/{10 + n}/2026,{name.upper()},A PERSON,-11111,{n + 1}.00,,{name.upper()},z{n},Cat\n" for n, name in enumerate(names))
        levels = {name: f"Group: Name {n}" for n, name in enumerate(names)}
        categories = placed({**levels, "store": "Retail outlets: Bakeries"})
        payments, _ = fragment("payments", monarch=monarch, amex=amex, categories=categories)
        self.assertLessEqual(len(payments[0]["top"]), 5)

    def test_each_charge_says_which_payment_settled_it_or_that_it_is_still_open(self):
        payment_id = self.payments[0]["payment_id"]
        settled = {r["payee"] for r in self.records if r.get("settled_by") == payment_id}
        self.assertEqual(settled, {"Store", "Shoe Shop"})
        dunkin = next(r for r in self.by_payee["Dunkin'"] if "settled_by" in r)  # in the card's export, dated after the payment
        self.assertIsNone(dunkin["settled_by"])

    def test_a_record_outside_the_card_export_has_no_settled_by(self):
        self.assertTrue(all("settled_by" not in r for r in self.by_payee["Employer"]))

    def test_the_summary_gives_the_open_balance_as_a_count_and_an_amount(self):
        self.assertEqual(self.summary["open_balance"], {"scope": "all", "count": 1, "amount": 4.5})

    def test_settled_plus_open_is_every_charge_of_the_card_export_to_the_cent(self):
        charges = [r for r in self.records if "settled_by" in r and r["cost"] < 0]
        settled = sum(-r["cost"] for r in charges if r["settled_by"])
        opened = sum(-r["cost"] for r in charges if not r["settled_by"])
        self.assertEqual(round(settled + opened, 2), 129.5)
        self.assertEqual(round(settled, 2), self.payments[0]["settled"])


class NoPaymentTests(unittest.TestCase):
    def test_a_card_with_no_payments_leaves_every_charge_open_and_writes_no_payment_lines(self):
        amex = without_lines((ORACLE / "amex.csv").read_text(encoding="utf-8"), containing=("PAYMENT RECEIVED",))
        monarch = without_lines(MONARCH, ",m8", ",m9")
        payments, _ = fragment("payments", monarch=monarch, amex=amex, categories=CATEGORIES)
        records, _ = fragment("final_records", monarch=monarch, amex=amex, categories=CATEGORIES)
        _, summary = fragment("open_balance_noted", monarch=monarch, amex=amex, categories=CATEGORIES)
        self.assertEqual(payments, [])
        charges = [r for r in records if "settled_by" in r and r["cost"] < 0]
        self.assertTrue(charges)
        self.assertTrue(all(r["settled_by"] is None for r in charges))
        self.assertEqual(summary["open_balance"]["count"], len(charges))


class CardDatesTests(unittest.TestCase):
    def test_charges_are_ordered_and_cut_off_by_the_cards_own_dates_not_the_banks(self):
        # the bank posted the 03-05 Dunkin' charge on 03-02, the payment's day; the card dated it 03-05, after the payment
        monarch = MONARCH.replace("2026-03-05,Dunkin',\"Food & Dining: Coffee & Cafes\",Platinum Card (...1111),DUNKIN',,-4.50",
                                  "2026-03-02,Dunkin',\"Food & Dining: Coffee & Cafes\",Platinum Card (...1111),DUNKIN',,-4.50")
        self.assertNotEqual(monarch, MONARCH)
        payments, _ = fragment("payments", monarch=monarch, categories=CATEGORIES)
        records, _ = fragment("final_records", monarch=monarch, categories=CATEGORIES)
        _, summary = fragment("open_balance_noted", monarch=monarch, categories=CATEGORIES)
        self.assertEqual(payments[0]["charges"], 3)
        dunkin = next(r for r in records if r["payee"] == "Dunkin'" and "settled_by" in r)
        self.assertIsNone(dunkin["settled_by"])
        self.assertEqual(summary["open_balance"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
