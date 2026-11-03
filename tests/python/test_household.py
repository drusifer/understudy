import io
import json
import tempfile
import unittest
from pathlib import Path

from jev_double import JevDouble

from src.jev import Chosen
from src.paths import ROOT
from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

LEDGER = ROOT / "examples" / "household" / "household.yaml"
ORACLE = ROOT / "tests" / "fixtures" / "household"
PLACED = {"Store": ("Shopping & Retail: General", 0.9), "Dunkin'": ("Food & Dining: Coffee & Cafes", 0.95),
          "Employer": ("Income: Paychecks", 0.99), "Shoe Shop": ("Shopping & Retail: General", 0.5),
          "Venmo": ("none_of_these", 0.9)}


def category(merchant, options):
    """A scripted Jev for the three category questions: which category in use, which kind of business, which name."""
    if "none_of_these" in options:
        top, sure = PLACED[merchant]
    elif "Utilities" in options:
        top, sure = "Utilities", 0.8
    else:
        top, sure = next(iter(options)), 0.9
    rest = (1 - sure) / max(len(options) - 1, 1)
    return Chosen(top, sure, {name: sure if name == top else rest for name in options})


def no_pins(directory: Path) -> list[str]:
    """`--with` arguments naming an empty pin file, so a run never reads the owner's real pins."""
    pins = directory / "pins.jsonl"
    pins.write_text("", encoding="utf-8")
    return ["--with", f"pinned={pins}"]


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        directory = Path(cls.temporary.name)

        def reading(state, instructions, options):
            if "refund" in state:  # the refund of 45.00 reverses the charge of 45.00 on the 15th
                original = next(label for label in options if "2026-02-15" in label)
                return Chosen(original, 0.8, {label: 0.8 if label == original else 0.2 for label in options})
            if "merchant" in state:
                return category(state["merchant"][0]["merchant"], options)
            raise AssertionError(f"Jev was asked a question the household no longer asks: {list(state)}")

        stderr = io.StringIO()
        cls.code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={ORACLE / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
             *no_pins(directory)],
            make_jev=lambda: JevDouble(choose_fn=reading), store=CaptureStore(directory / "cache"), stdout=io.StringIO(),
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

    def test_a_charge_in_both_exports_is_one_record_and_the_period_leaves_out_the_old_row(self):
        self.assertEqual(len(self.records), 12)  # the oracle's count: 13 Monarch rows less 1 before the period, 7 Amex merged in
        self.assertEqual(sum(r["match"] == "paired" for r in self.records), 7)
        self.assertNotIn("Old Shop", {r["payee"] for r in self.records})

    def test_the_card_payment_links_to_the_checking_debit(self):
        self.assertEqual((self.legs["m9"]["partner"], self.legs["m10"]["partner"]), ("m10", "m9"))

    def test_the_savings_bank_deposit_is_an_unpaired_transfer_candidate_kept_as_evidence(self):
        unpaired = {leg["payee"] for leg in self.legs.values() if leg["partner"] is None}
        self.assertEqual(unpaired, {"Ridgewood Savings Bank"})

    def test_the_exports_category_decides_which_records_are_transfers(self):
        transfers = {r["payee"] for r in self.records if r["kind"] == "transfer"}
        self.assertEqual(transfers, {"Payment Thank You", "Amex Payment", "Ridgewood Savings Bank"})

    def test_a_record_with_no_transfer_label_and_no_link_is_never_a_transfer(self):
        venmo = next(r for r in self.records if r["payee"] == "Venmo")  # "Peer to Peer", paired by no one
        self.assertEqual(venmo["kind"], "purchase")

    def test_every_record_has_a_kind_and_there_is_no_external_transfer(self):
        kinds = {}
        for record in self.records:
            kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
        self.assertEqual(kinds, {"purchase": 6, "transfer": 3, "refund": 2, "credit": 1})

    def test_the_summary_counts_the_transfers_by_label_by_link_and_by_both(self):
        # the card payment's two halves are labeled and linked; the savings bank deposit is labeled and has no partner
        self.assertEqual(self.summary["transfer_basis"], {"both": 2, "label": 1, "none": 9})

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
                         ("Shopping & Retail: General", 0.5, "below_0.7"))
        self.assertTrue(shoes["runner_up"])
        self.assertLess(shoes["runner_up_probability"], shoes["top_probability"])

    def test_jev_is_no_longer_asked_about_payees_and_the_judgments_file_is_gone(self):
        self.assertFalse((self.folder / "judgments.jsonl").exists())

    def test_a_refund_with_one_original_links_by_rule_and_one_with_several_by_jev(self):
        refunds = {r["payee"]: r for r in self.records if r["kind"] == "refund"}
        self.assertEqual(refunds["Shoe Shop"]["link_status"], "single")
        self.assertEqual(refunds["Store"]["link_status"], "chosen")
        original = next(r for r in self.records if r["record_id"] == refunds["Store"]["candidate_record_id"])
        self.assertEqual((original["cost"], original["day"]), (-45.0, "2026-02-15"))

    def test_merchants_are_placed_in_the_categories_in_use_and_an_unsure_one_goes_to_review(self):
        by = {(r["payee"], r["kind"]): r for r in self.records}
        self.assertEqual(by["Store", "purchase"]["category_level"], "Shopping & Retail: General")
        self.assertEqual(by["Dunkin'", "purchase"]["category_level"], "Food & Dining: Coffee & Cafes")
        self.assertEqual(by["Employer", "credit"]["category_status"], "placed")
        shoes = by["Shoe Shop", "purchase"]
        self.assertEqual((shoes["category_status"], shoes.get("category_level")), ("review", None))

    def test_a_merchant_that_fits_no_category_is_named_from_the_mcc_list_by_choosing_a_group_and_a_name(self):
        venmo = next(r for r in self.records if r["payee"] == "Venmo")
        self.assertEqual(venmo["category_status"], "placed")
        self.assertTrue(venmo["category_level"] and venmo["category_level"] != "none_of_these")

    def test_transfers_are_not_asked_about_and_say_so(self):
        legs = [r for r in self.records if r["kind"] == "transfer"]
        self.assertEqual({r["category_status"] for r in legs}, {"none"})


def first_choice(state, instructions, options):
    """A scripted Jev that is sure of the first option, and picks the original a refund reversed."""
    if "refund" in state:
        original = next(label for label in options if "2026-02-15" in label)
        return Chosen(original, 0.9, {label: 0.9 if label == original else 0.1 for label in options})
    top = next(iter(options))
    return Chosen(top, 0.9, {name: 0.9 if name == top else 0.1 for name in options})


def run_with_monarch(monarch_text: str):
    """Run the household on a changed copy of the fixture's Monarch export; returns its records and summary."""
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        (directory / "monarch.csv").write_text(monarch_text, encoding="utf-8")
        code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={directory / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
             *no_pins(directory)],
            make_jev=lambda: JevDouble(choose_fn=first_choice), store=CaptureStore(directory / "cache"),
            stdout=io.StringIO(), stderr=io.StringIO())
        (folder,) = (directory / "out").iterdir()
        return code, lines(folder / "records.jsonl"), json.loads((folder / "summary.json").read_text(encoding="utf-8"))


class TransferBasisTests(unittest.TestCase):
    ORIGINAL = (ORACLE / "monarch.csv").read_text(encoding="utf-8")

    def kinds(self, records, *payees):
        return {payee: next(r["kind"] for r in records if r["payee"] == payee) for payee in payees}

    def test_every_label_form_makes_a_transfer_and_a_lookalike_does_not(self):
        extra = (
            '2026-03-06,Bank Transfer,"Transportation: Transfers",Checking (...2222),BANK TRANSFER,,-300.00,,Me,,m13\n'
            '2026-03-07,Citibank Online,"Food & Dining: Credit Card Payment",Checking (...2222),CITI,,-80.00,,Me,,m14\n'
            '2026-03-08,Gift Shop,"Shopping: Transferware",Checking (...2222),GIFT SHOP,,-12.00,,Me,,m15\n'
            '2026-03-09,Savings Move,"Transfer",Checking (...2222),SAVINGS MOVE,,-50.00,,Me,,m16\n')
        code, records, _ = run_with_monarch(self.ORIGINAL + extra)
        self.assertEqual(code, 0)
        self.assertEqual(self.kinds(records, "Bank Transfer", "Citibank Online", "Gift Shop", "Savings Move"),
                         {"Bank Transfer": "transfer", "Citibank Online": "transfer", "Gift Shop": "purchase",
                          "Savings Move": "transfer"})

    def test_a_record_linked_to_a_record_in_another_account_is_a_transfer_whatever_its_label(self):
        # the card's payment received, labeled as income by an earlier categorization, is linked to the checking debit
        changed = self.ORIGINAL.replace('Payment Thank You,"Credit Card Payment"', 'Payment Thank You,"Income: Paychecks"')
        self.assertNotEqual(changed, self.ORIGINAL)
        code, records, summary = run_with_monarch(changed)
        self.assertEqual(code, 0)
        self.assertEqual(self.kinds(records, "Payment Thank You", "Amex Payment"),
                         {"Payment Thank You": "transfer", "Amex Payment": "transfer"})
        self.assertEqual(summary["transfer_basis"], {"both": 1, "label": 1, "link": 1, "none": 9})


class NothingForReviewTests(unittest.TestCase):
    def test_when_jev_is_sure_of_every_merchant_the_review_file_is_written_and_empty(self):
        def reading(state, instructions, options):
            if "refund" in state:
                original = next(label for label in options if "2026-02-15" in label)
                return Chosen(original, 0.95, {label: 0.95 if label == original else 0.05 for label in options})
            top = next(iter(options))
            return Chosen(top, 0.95, {name: 0.95 if name == top else 0.05 for name in options})

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            code = main(
                ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={ORACLE / 'monarch.csv'}",
                 "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
                 *no_pins(directory)],
                make_jev=lambda: JevDouble(choose_fn=reading), store=CaptureStore(directory / "cache"),
                stdout=io.StringIO(), stderr=io.StringIO())
            (folder,) = (directory / "out").iterdir()
            self.assertEqual(code, 0)
            self.assertEqual((folder / "review.jsonl").read_text(encoding="utf-8"), "")


class MissingCategoryTests(unittest.TestCase):
    def test_a_monarch_file_without_a_category_column_stops_before_any_request_to_jev(self):
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
        from src.sketch.cli import _values
        relative = str(Path(__file__).resolve().relative_to(Path.cwd()))
        self.assertEqual(_values([f"monarch={relative}", "amex_account=Platinum"]),
                         {"monarch": str(Path(__file__).resolve()), "amex_account": "Platinum"})


if __name__ == "__main__":
    unittest.main()
