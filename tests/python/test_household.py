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
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01"],
            make_jev=lambda: JevDouble(choose_fn=reading), store=CaptureStore(directory / "cache"), stdout=io.StringIO(),
            stderr=stderr)
        cls.stderr = stderr.getvalue()
        (folder,) = (directory / "out").iterdir()
        cls.records = lines(folder / "records.jsonl")
        cls.legs = {leg["record_id"]: leg for leg in lines(folder / "legs.jsonl")}
        cls.folder = folder
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

    def test_venmo_and_the_savings_bank_are_unpaired_transfer_candidates_kept_as_evidence(self):
        unpaired = {leg["payee"] for leg in self.legs.values() if leg["partner"] is None}
        self.assertEqual(unpaired, {"Venmo", "Ridgewood Savings Bank"})

    def test_the_exports_category_decides_which_records_are_transfers(self):
        transfers = {r["payee"] for r in self.records if r["kind"] == "transfer"}
        self.assertEqual(transfers, {"Payment Thank You", "Amex Payment", "Ridgewood Savings Bank"})

    def test_a_record_whose_category_is_not_transfer_or_card_payment_is_never_a_transfer(self):
        venmo = next(r for r in self.records if r["payee"] == "Venmo")  # "Transportation: Transfers", paired by no one
        self.assertEqual(venmo["kind"], "purchase")

    def test_every_record_has_a_kind_and_there_is_no_external_transfer(self):
        kinds = {}
        for record in self.records:
            kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
        self.assertEqual(kinds, {"purchase": 6, "transfer": 3, "refund": 2, "credit": 1})

    def test_the_summary_counts_the_records_whose_kind_the_category_changed(self):
        # the savings bank deposit is a transfer by category with no partner; every other record agrees with the pairing
        self.assertEqual(self.summary["kind_changed_by_category"], {"no": 11, "yes": 1})

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
                 "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01"],
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
