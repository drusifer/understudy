"""The household sketch: one whole run read by many tests (`LedgerTests`), the rules of its stages on their own stages
(`fragment`), and the few things only a whole run shows (an empty period, a missing column that must stop it before Jev).
"""

import io
import json
import tempfile
import unittest
from pathlib import Path

from household_fragment import decided, fragment, placed_all
from household_jev import choose, first_choice
from jev_double import JevDouble

from src.jev import Chosen
from src.paths import ROOT
from src.play.cli import main
from src.play.sources.capture import CaptureStore

LEDGER = ROOT / "examples" / "household" / "household.yaml"
ORACLE = ROOT / "tests" / "fixtures" / "household"
def no_pins(directory: Path) -> list[str]:
    """`--with` arguments naming an empty pin file, so a run never reads the owner's real pins."""
    pins = directory / "pins.jsonl"
    pins.write_text("", encoding="utf-8")
    return ["--with", f"pinned={pins}"]


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class LedgerTests(unittest.TestCase):
    """The household run once on the fixture exports with the scripted Jev: the happy path, whose outputs many tests read."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        directory = Path(cls.temporary.name)

        stderr = io.StringIO()
        cls.code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={ORACLE / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
             *no_pins(directory)],
            make_jev=lambda: JevDouble(choose_fn=choose), store=CaptureStore(directory / "cache"), stdout=io.StringIO(),
            stderr=stderr)
        cls.stderr = stderr.getvalue()
        (folder,) = (directory / "out").iterdir()
        cls.records = lines(folder / "records.jsonl")
        cls.legs = {leg["record_id"]: leg for leg in lines(folder / "legs.jsonl")}
        cls.folder = folder
        cls.totals = lines(folder / "totals.jsonl")
        cls.summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_it_runs(self):
        self.assertEqual((self.code, self.stderr), (0, ""))

    def test_the_payments_file_and_the_open_balance_are_written_by_the_whole_run(self):
        # the payment rules themselves are tested on their own stages (test_household_payments); this is the wiring
        payments = lines(self.folder / "payments.jsonl")
        self.assertEqual([(p["amount"], p["charges"], p["settled"]) for p in payments], [(500.0, 3, 125.0)])
        self.assertEqual(self.summary["open_balance"], {"scope": "all", "count": 1, "amount": 4.5})
        self.assertIn("settled_by", next(r for r in self.records if r["payee"] == "Store"))

    def test_a_charge_in_both_exports_is_one_record_and_the_period_leaves_out_the_old_row(self):
        self.assertEqual(len(self.records), 12)  # the oracle's count: 13 Monarch rows less 1 before the period, 7 Amex merged in
        self.assertEqual(sum(r["match"] == "paired" for r in self.records), 7)
        self.assertNotIn("Old Shop", {r["payee"] for r in self.records})

    def test_the_card_payment_links_to_the_checking_debit(self):
        self.assertEqual((self.legs["m9"]["partner"], self.legs["m10"]["partner"]), ("m10", "m9"))

    def test_only_the_card_payment_halves_are_link_candidates_the_savings_bank_is_found_by_its_category_not_its_text(self):
        self.assertEqual({leg["payee"] for leg in self.legs.values()}, {"Payment Thank You", "Amex Payment"})

    def test_the_transfers_are_the_linked_payment_and_the_merchant_jev_put_in_household_transfer(self):
        transfers = {r["payee"] for r in self.records if r["kind"] == "transfer"}
        self.assertEqual(transfers, {"Payment Thank You", "Amex Payment", "Ridgewood Savings Bank"})

    def test_a_record_that_is_not_linked_and_not_in_household_transfer_is_never_a_transfer(self):
        venmo = next(r for r in self.records if r["payee"] == "Venmo")  # no group fits, paired by no one
        self.assertEqual(venmo["kind"], "purchase")

    def test_every_record_has_a_kind_and_there_is_no_external_transfer(self):
        kinds = {}
        for record in self.records:
            kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
        self.assertEqual(kinds, {"purchase": 6, "transfer": 3, "refund": 2, "credit": 1})

    def test_the_summary_counts_the_transfers_by_link_by_category_and_by_both(self):
        # the card payment's two halves are linked; the savings bank deposit is in Household: Transfer and has no partner
        self.assertEqual(self.summary["transfer_basis"], {"category": 1, "link": 2, "none": 9})

    def money(self, card=None):
        """Income, expenses and net from the records themselves: money in and out, transfers and invalid rows left out."""
        rows = [r for r in self.records if r["kind"] in ("purchase", "refund", "credit") and card in (None, r["card"])]
        income = round(sum(r["cost"] for r in rows if r["cost"] > 0), 2)
        expenses = round(sum(r["cost"] for r in rows if r["cost"] < 0), 2)
        return income, expenses, round(income + expenses, 2)

    def test_each_account_has_income_expenses_and_net_that_leave_transfers_out(self):
        by_card = {row["card"]: row for row in self.totals if "card" in row}
        self.assertEqual(set(by_card), {r["card"] for r in self.records if r["kind"] in ("purchase", "refund", "credit")})
        for card, row in by_card.items():
            self.assertEqual((row["income"], row["expenses"], row["net"]), self.money(card), card)
        self.assertNotIn("Checking (...2222)", {c for c in by_card if self.money(c) == (0.0, 0.0, 0.0)})

    def test_one_net_spending_figure_covers_every_account_and_is_in_the_summary(self):
        income, expenses, net = self.money()
        self.assertEqual(self.summary["net_spending"], {"scope": "all", "count": 9, "income": income,
                                                        "expenses": expenses, "net": net})
        self.assertEqual(self.totals[-1]["net"], net)

    def test_review_has_one_line_per_merchant_with_records_for_review_biggest_first(self):
        review = lines(self.folder / "review.jsonl")
        asked = [r for r in self.records if r["category_status"] == "review"]
        self.assertEqual(len(review), len({r["payee"] for r in asked}))
        for line in review:
            mine = [r for r in asked if r["payee"] == line["payee"]]
            self.assertEqual((line["count"], line["amount"]), (len(mine), round(sum(r["cost"] for r in mine), 2)))
        self.assertEqual([line["count"] for line in review], sorted((line["count"] for line in review), reverse=True))

    def test_a_review_line_has_jevs_top_two_guesses_and_why_it_is_for_review(self):
        (shoes,) = (line for line in lines(self.folder / "review.jsonl") if line["payee"] == "Shoe Shop")
        self.assertEqual(set(shoes), {"payee", "count", "amount", "top", "top_probability", "runner_up",
                                      "runner_up_probability", "reason"})
        self.assertEqual((shoes["top"], shoes["top_probability"], shoes["reason"]),
                         ("Clothing outlets: Family clothing shops", 0.35, "below_0.7"))
        self.assertTrue(shoes["runner_up"])
        self.assertLessEqual(shoes["runner_up_probability"], shoes["top_probability"])

    def test_jev_is_no_longer_asked_about_payees_and_the_judgments_file_is_gone(self):
        self.assertFalse((self.folder / "judgments.jsonl").exists())

    def test_a_refund_with_one_original_links_by_rule_and_one_with_several_by_jev(self):
        refunds = {r["payee"]: r for r in self.records if r["kind"] == "refund"}
        self.assertEqual(refunds["Shoe Shop"]["link_status"], "single")
        self.assertEqual(refunds["Store"]["link_status"], "chosen")
        original = next(r for r in self.records if r["record_id"] == refunds["Store"]["candidate_record_id"])
        self.assertEqual((original["cost"], original["day"]), (-45.0, "2026-02-15"))

    def test_transfers_are_not_asked_about_and_say_so(self):
        legs = [r for r in self.records if r["kind"] == "transfer"]
        self.assertEqual({r["category_status"] for r in legs}, {"none"})


def run_folder(monarch_text: str, since: str = "2026-01-01", pinned: str | None = None, jev=first_choice) -> tuple[int, dict]:
    """Run the household whole on a changed copy of the fixture's Monarch export and read back its records, summary and
    spending lines. Used by the few tests that need a whole run."""
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        (directory / "monarch.csv").write_text(monarch_text, encoding="utf-8")
        code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={directory / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", f"since={since}",
             *(["--with", f"pinned={pinned}"] if pinned else no_pins(directory))],
            make_jev=lambda: JevDouble(choose_fn=jev), store=CaptureStore(directory / "cache"),
            stdout=io.StringIO(), stderr=io.StringIO())
        (folder,) = (directory / "out").iterdir()
        spending = folder / "spending.jsonl"
        return code, {"records": lines(folder / "records.jsonl"),
                      "summary": json.loads((folder / "summary.json").read_text(encoding="utf-8")),
                      "spending": lines(spending), "spending_text": spending.read_text(encoding="utf-8")}


class TransferBasisTests(unittest.TestCase):
    ORIGINAL = (ORACLE / "monarch.csv").read_text(encoding="utf-8")

    def kinds(self, monarch, *payees, pins=None):
        """The kind of each payee's first record, and the summary, for the export given; every merchant is placed in some
        category unless a pin says otherwise (which category does not matter here)."""
        extra = {"placements": []} if pins else {"decided": placed_all(monarch, transfers=())}  # none in Household: Transfer
        records, summary = fragment("finished", monarch=monarch, pins=pins, **extra)
        return {payee: next(r["kind"] for r in records if r["payee"] == payee) for payee in payees}, summary

    def test_a_label_that_says_transfer_or_card_payment_makes_nothing_a_transfer(self):
        extra = (
            '2026-03-06,Bank Transfer,"Transportation: Transfers",Checking (...2222),BANK TRANSFER,,-300.00,,Me,,m13\n'
            '2026-03-07,Citibank Online,"Food & Dining: Credit Card Payment",Checking (...2222),CITI,,-80.00,,Me,,m14\n'
            '2026-03-09,Savings Move,"Transfer",Checking (...2222),SAVINGS MOVE,,-50.00,,Me,,m16\n')
        kinds, _ = self.kinds(self.ORIGINAL + extra, "Bank Transfer", "Savings Move")
        self.assertEqual(kinds, {"Bank Transfer": "purchase", "Savings Move": "purchase"})  # not in Household: Transfer

    def test_a_payment_whose_category_says_something_misleading_still_links_and_neither_half_counts_as_income(self):
        # the card's payment received is labeled as income, as an earlier categorization did; the link comes from the text
        changed = self.ORIGINAL.replace('Payment Thank You,"Credit Card Payment"', 'Payment Thank You,"Income: Paychecks"')
        self.assertNotEqual(changed, self.ORIGINAL)
        kinds, summary = self.kinds(changed, "Payment Thank You", "Amex Payment")
        self.assertEqual(kinds, {"Payment Thank You": "transfer", "Amex Payment": "transfer"})
        self.assertEqual(summary["transfer_basis"], {"link": 2, "none": 10})

    def test_a_card_payment_received_is_a_transfer_even_when_the_bank_side_is_not_in_the_data(self):
        # the Monarch export starts after the payment left the bank: the card's own text still says it is a payment
        alone = "\n".join(line for line in self.ORIGINAL.splitlines() if not line.endswith(",m9")) + "\n"
        self.assertNotEqual(alone, self.ORIGINAL)
        kinds, summary = self.kinds(alone, "Payment Thank You")
        self.assertEqual(kinds, {"Payment Thank You": "transfer"})
        self.assertEqual(summary["transfer_basis"].get("payment"), 1)

    def test_a_merchant_the_owner_pins_to_household_transfer_makes_its_records_transfers(self):
        kinds, _ = self.kinds(self.ORIGINAL, "Venmo", pins=[{"payee": "Venmo", "category": "Household: Transfer"}])
        self.assertEqual(kinds, {"Venmo": "transfer"})


class SpendingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        placements = decided()
        cls.records, _ = fragment("finished", decided=placements)
        cls.spending, cls.summary = fragment("spend_list", decided=placements)
        _, totals = fragment("spend_total", decided=placements)
        cls.summary = totals

    def expected(self):
        """What the list should say, worked out from the records alone: money out of purchases and refunds by category."""
        totals: dict[str, float] = {}
        for r in self.records:
            if r["kind"] in ("purchase", "refund"):
                name = r.get("category_level") or "unplaced"
                totals[name] = round(totals.get(name, 0.0) + r["cost"], 2)
        return {name: round(-total, 2) for name, total in totals.items()}

    def test_one_line_per_category_with_its_records_amount_and_share_biggest_first(self):
        self.assertEqual({line["category"]: line["amount"] for line in self.spending}, self.expected())
        self.assertEqual([line["amount"] for line in self.spending], sorted((line["amount"] for line in self.spending), reverse=True))
        self.assertEqual(sum(line["count"] for line in self.spending),
                         sum(r["kind"] in ("purchase", "refund") for r in self.records))

    def test_the_list_holds_only_the_tools_categories_and_unplaced_never_the_exports(self):
        names = {line["category"] for line in self.spending}
        placed = {r["category_level"] for r in self.records if r.get("category_level")}
        self.assertEqual(names - placed, {"unplaced"})  # the shoe shop and Venmo are for review
        self.assertNotIn("Shopping & Retail: General", names)  # the export's own word for the Store
        self.assertNotIn("uncategorized", names)

    def test_income_credits_and_transfers_are_not_in_the_list(self):
        self.assertNotIn("Income: Paychecks", {line["category"] for line in self.spending})

    def test_shares_add_to_one_and_the_amounts_add_to_the_summary_total(self):
        self.assertAlmostEqual(sum(line["share"] for line in self.spending), 1.0, delta=0.001)
        self.assertEqual(self.summary["spending_total"]["amount"], round(sum(line["amount"] for line in self.spending), 2))
        self.assertEqual(self.summary["spending_total"]["count"], sum(line["count"] for line in self.spending))

    def test_a_run_with_no_spending_writes_an_empty_file(self):
        # a whole run: that the file is written, and empty, is what only the publishing of a run shows
        code, found = run_folder((ORACLE / "monarch.csv").read_text(encoding="utf-8"), since="2027-01-01")
        self.assertEqual((code, found["spending_text"]), (0, ""))


class NothingForReviewTests(unittest.TestCase):
    def test_when_jev_is_sure_of_every_merchant_the_review_list_is_empty(self):
        def sure(state, instructions, options):
            top = next(iter(options))
            return Chosen(top, 0.95, {name: 0.95 if name == top else 0.05 for name in options})

        review, _ = fragment("review_list", decided=decided(jev=sure))
        self.assertEqual(review, [])


class MissingCategoryTests(unittest.TestCase):
    def test_a_monarch_file_without_a_category_column_stops_before_any_request_to_jev(self):
        # a whole (early-stopping) run: that the check comes before the first request is what only a run shows
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            lines_in = (ORACLE / "monarch.csv").read_text(encoding="utf-8").splitlines()
            header = lines_in[0].split(",")
            keep = [i for i, name in enumerate(header) if name != "Category"]
            import csv
            with (directory / "monarch.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                for row in csv.reader(lines_in):
                    writer.writerow([row[i] for i in keep])
            asked = []

            def reading(state, instructions, options):
                asked.append(state)
                raise AssertionError("Jev must not be asked")

            stderr = io.StringIO()
            code = main(
                ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={directory / 'monarch.csv'}",
                 "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
                 *no_pins(directory)],
                make_jev=lambda: JevDouble(choose_fn=reading), store=CaptureStore(directory / "cache"),
                stdout=io.StringIO(), stderr=stderr)
        self.assertNotEqual(code, 0)
        self.assertIn("has no Category column", stderr.getvalue())
        self.assertEqual(asked, [])


class PathValueTests(unittest.TestCase):
    def test_a_with_value_naming_a_file_relative_to_where_you_run_is_made_absolute(self):
        from src.play.cli import _values
        relative = str(Path(__file__).resolve().relative_to(Path.cwd()))
        self.assertEqual(_values([f"monarch={relative}", "amex_account=Platinum"]),
                         {"monarch": str(Path(__file__).resolve()), "amex_account": "Platinum"})


if __name__ == "__main__":
    unittest.main()
