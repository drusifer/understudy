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
OWN = {"Venmo": 0.05, "Ridgewood Savings Bank": 0.93}  # the probability the payee is one of the owner's accounts


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
        cls.seen = []

        def reading(state, instructions, options):
            if "refund" in state:  # the refund of 45.00 reverses the charge of 45.00 on the 15th
                original = next(label for label in options if "2026-02-15" in label)
                return Chosen(original, 0.8, {label: 0.8 if label == original else 0.2 for label in options})
            if "merchant" in state:
                return category(state["merchant"][0]["merchant"], options)
            cls.seen.append(state)
            own = OWN[state["payee"][0]["payee"]]
            levels = {"own_account": own, "someone_else": 1 - own}
            return Chosen(max(levels, key=levels.get), 0.9, levels)

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
        cls.judged = {row["payee"]: row for row in lines(folder / "judgments.jsonl")}

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

    def test_venmo_and_the_savings_bank_are_unpaired_transfer_candidates(self):
        unpaired = {leg["payee"] for leg in self.legs.values() if leg["partner"] is None}
        self.assertEqual(unpaired, {"Venmo", "Ridgewood Savings Bank"})

    def test_jev_judges_each_unpaired_payee_and_the_thresholds_decide(self):
        self.assertEqual({payee: row["decision"] for payee, row in self.judged.items()},
                         {"Venmo": "spending", "Ridgewood Savings Bank": "external_transfer"})

    def test_every_record_has_a_kind_and_they_are_the_etls_kinds(self):
        kinds = {}
        for record in self.records:
            kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
        self.assertEqual(kinds, {"purchase": 6, "transfer": 2, "external_transfer": 1, "refund": 2, "credit": 1})

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
        legs = [r for r in self.records if r["kind"] in ("transfer", "external_transfer")]
        self.assertEqual({r["category_status"] for r in legs}, {"none"})

    def test_jev_sees_the_owners_account_names_but_never_their_numbers(self):
        self.assertEqual(len(self.seen), 2)
        shown = json.dumps(self.seen)
        self.assertIn("Platinum Card", shown)
        self.assertNotIn("(...", shown)
        self.assertNotIn("1111", shown)




class PathValueTests(unittest.TestCase):
    def test_a_with_value_naming_a_file_relative_to_where_you_run_is_made_absolute(self):
        from src.sketch.cli import _values
        relative = str(Path(__file__).resolve().relative_to(Path.cwd()))
        self.assertEqual(_values([f"monarch={relative}", "amex_account=Platinum"]),
                         {"monarch": str(Path(__file__).resolve()), "amex_account": "Platinum"})


if __name__ == "__main__":
    unittest.main()
