import io
import tempfile
import unittest
from pathlib import Path

from jev_double import JevDouble
from test_household_ledger import LEDGER, ORACLE, OWN, PLACED, category, lines

from src.jev import Chosen
from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

UNFIT = {**PLACED, "Shoe Shop": ("none_of_these", 0.9)}  # two merchants fit no category in use


class NamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        directory = Path(cls.temporary.name)
        cls.asked = []

        def reading(state, instructions, options):
            if "refund" in state:
                original = next(label for label in options if "2026-02-15" in label)
                return Chosen(original, 0.8, {label: 0.8 if label == original else 0.2 for label in options})
            if "merchant" in state:
                merchant = state["merchant"][0]["merchant"]
                cls.asked.append((merchant, sorted(options)))
                if "none_of_these" in options and not any(": " in name for name in options):  # the names given before
                    taken = next(name for name in options if name != "none_of_these")
                    return Chosen(taken, 0.9, {name: 0.9 if name == taken else 0.1 for name in options})
                return category(merchant, options) if "none_of_these" not in options else _place(merchant, options)
            own = OWN[state["payee"][0]["payee"]]
            levels = {"own_account": own, "someone_else": 1 - own}
            return Chosen(max(levels, key=levels.get), 0.9, levels)

        def _place(merchant, options):
            top, sure = UNFIT[merchant]
            return Chosen(top, sure, {name: sure if name == top else (1 - sure) / (len(options) - 1) for name in options})

        stderr = io.StringIO()
        cls.code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={ORACLE / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01"],
            make_jev=lambda: JevDouble(choose_fn=reading), store=CaptureStore(directory / "cache"), stdout=io.StringIO(),
            stderr=stderr)
        cls.stderr = stderr.getvalue()
        (folder,) = (directory / "out").iterdir()
        cls.records = lines(folder / "records.jsonl")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_it_runs(self):
        self.assertEqual((self.code, self.stderr), (0, ""))

    def test_the_second_merchant_is_offered_the_name_the_first_was_given_and_takes_it(self):
        venmo = next(r for r in self.records if r["payee"] == "Venmo")
        shoes = next(r for r in self.records if r["payee"] == "Shoe Shop" and r["kind"] == "purchase")
        self.assertEqual((shoes["category_status"], venmo["category_status"]), ("placed", "placed"))
        self.assertEqual(shoes["category_level"], venmo["category_level"])
        offered_earlier = [options for _, options in self.asked if "none_of_these" in options and len(options) == 2]  # noqa: PLR2004
        self.assertEqual(len(offered_earlier), 1)
        self.assertIn(venmo["category_level"], offered_earlier[0])

    def test_the_mcc_list_is_walked_once_for_the_two_merchants(self):
        kinds = [options for _, options in self.asked if "Utilities" in options]
        self.assertEqual(len(kinds), 1)


if __name__ == "__main__":
    unittest.main()
