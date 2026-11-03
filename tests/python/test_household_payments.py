"""UND-99: each card payment is tied to the charges it settled, and the report says what they were for."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from household_jev import choose
from jev_double import JevDouble
from test_household import LEDGER, ORACLE, lines, no_pins

from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore


def run_household(monarch_text: str | None = None, amex_text: str | None = None):
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        monarch, amex = directory / "monarch.csv", directory / "amex.csv"
        monarch.write_text(monarch_text or (ORACLE / "monarch.csv").read_text(encoding="utf-8"), encoding="utf-8")
        amex.write_text(amex_text or (ORACLE / "amex.csv").read_text(encoding="utf-8"), encoding="utf-8")
        code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={monarch}", "--with", f"amex={amex}",
             "--with", "amex_account=Platinum", "--with", "since=2026-01-01", *no_pins(directory)],
            make_jev=lambda: JevDouble(choose_fn=choose), store=CaptureStore(directory / "cache"),
            stdout=io.StringIO(), stderr=io.StringIO())
        (folder,) = (directory / "out").iterdir()
        return (code, lines(folder / "records.jsonl"), lines(folder / "payments.jsonl"),
                json.loads((folder / "summary.json").read_text(encoding="utf-8")))


class PaymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.records, cls.payments, cls.summary = run_household()
        cls.by_payee = {}
        for record in cls.records:
            cls.by_payee.setdefault(record["payee"], []).append(record)

    def test_it_runs(self):
        self.assertEqual(self.code, 0)

    def test_the_card_payment_has_a_line_with_what_it_settled_and_what_is_left(self):
        (payment,) = self.payments
        self.assertEqual((payment["day"], payment["amount"]), ("2026-03-02", 500.0))
        self.assertEqual((payment["charges"], payment["settled"], payment["remainder"]), (3, 125.0, 375.0))
        self.assertEqual(set(payment), {"payment_id", "day", "card", "amount", "charges", "settled", "remainder",
                                        "unexplained", "top"})

    def test_a_payment_with_much_left_over_says_it_is_partly_unexplained(self):
        self.assertTrue(self.payments[0]["unexplained"])  # 375 of 500 has no earlier charge to explain it

    def test_the_largest_categories_of_the_settled_charges_carry_their_amounts_and_shares(self):
        top = self.payments[0]["top"]
        self.assertEqual([entry["amount"] for entry in top], sorted((e["amount"] for e in top), reverse=True))
        self.assertEqual(sum(entry["amount"] for entry in top), 125.0)
        self.assertAlmostEqual(sum(entry["share"] for entry in top), 1.0, places=3)
        store = self.by_payee["Store"][0]["category_level"]
        self.assertEqual(next(e for e in top if e["category"] == store)["amount"], 95.0)
        self.assertIn("unplaced", {entry["category"] for entry in top})  # the shoe shop is for review

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
        amex = "\n".join(line for line in (ORACLE / "amex.csv").read_text(encoding="utf-8").splitlines()
                         if "PAYMENT RECEIVED" not in line) + "\n"
        monarch = "\n".join(line for line in (ORACLE / "monarch.csv").read_text(encoding="utf-8").splitlines()
                            if not line.endswith((",m8", ",m9"))) + "\n"
        code, records, payments, summary = run_household(monarch, amex)
        self.assertEqual((code, payments), (0, []))
        charges = [r for r in records if "settled_by" in r and r["cost"] < 0]
        self.assertTrue(charges)
        self.assertTrue(all(r["settled_by"] is None for r in charges))
        self.assertEqual(summary["open_balance"]["count"], len(charges))


class CardDatesTests(unittest.TestCase):
    def test_charges_are_ordered_and_cut_off_by_the_cards_own_dates_not_the_banks(self):
        # the bank posted the 03-05 Dunkin' charge on 03-02, the payment's day; the card dated it 03-05, after the payment
        original = (ORACLE / "monarch.csv").read_text(encoding="utf-8")
        monarch = original.replace("2026-03-05,Dunkin',\"Food & Dining: Coffee & Cafes\",Platinum Card (...1111),DUNKIN',,-4.50",
                                   "2026-03-02,Dunkin',\"Food & Dining: Coffee & Cafes\",Platinum Card (...1111),DUNKIN',,-4.50")
        self.assertNotEqual(monarch, original)
        _, records, payments, summary = run_household(monarch)
        self.assertEqual(payments[0]["charges"], 3)
        dunkin = next(r for r in records if r["payee"] == "Dunkin'" and "settled_by" in r)
        self.assertIsNone(dunkin["settled_by"])
        self.assertEqual(summary["open_balance"]["count"], 1)
