"""UND-96/97: the owner's pins place a merchant in the owner's category, skip Jev for it, and are checked before any request.

What a pin does to the household is tested on its own stages; the three refusals that must come before the first request to
Jev are checked on the sketch's own check states, and once as a whole early-stopping run (`PinCase.run_household`), the
only thing that shows the order.
"""

import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from household_fragment import ORACLE, fragment, run_state
from household_jev import choose
from jev_double import JevDouble
from test_household import LEDGER

from src.play.check import load_checked
from src.play.cli import main
from src.play.fragment import read_stage
from src.play.loader import PlayError
from src.play.sources.capture import CaptureStore

CLOTHING = "Clothing outlets: Family clothing shops"  # a category in the clean list (ISO 18245)
TAXONOMY = [{"category": CLOTHING}, {"category": "Household: Rent"}]
SHOES = {"payee": "shoe  shop", "category": CLOTHING}


class PinCase(unittest.TestCase):
    """A scratch folder and a way to run the household whole with the scripted Jev, noting what it was asked."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.dir = Path(temporary.name)
        self.asked: list[str] = []

    def pins(self, *rows) -> list[str]:
        path = self.dir / "pins.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return ["--with", f"pinned={path}"]

    def reading(self, state, instructions, options):
        if "merchant" in state:
            self.asked.append(state["merchant"][0]["merchant"])
        return choose(state, instructions, options)

    def run_household(self, *extra, name="out"):
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(
            ["run", str(LEDGER), "--out", str(self.dir / name), "--with", f"monarch={ORACLE / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
             *extra],
            make_jev=lambda: JevDouble(choose_fn=self.reading), store=CaptureStore(self.dir / "cache"), stdout=stdout,
            stderr=stderr)
        folders = list((self.dir / name).iterdir()) if (self.dir / name).exists() else []
        return code, stdout.getvalue(), stderr.getvalue(), (folders[0] if folders else None)


class PinnedMerchantTests(unittest.TestCase):
    """A pinned merchant, with nobody else placed (`placements` is empty), so only what the pin does shows."""

    @classmethod
    def setUpClass(cls):
        cls.records, _ = fragment("finished", pins=[SHOES], placements=[])
        cls.asked, _ = fragment("unpinned", pins=[SHOES], placements=[])
        cls.review, _ = fragment("review_list", pins=[SHOES], placements=[])

    def test_a_pinned_merchants_records_are_placed_in_its_category_and_show_they_were_pinned(self):
        shoes = [r for r in self.records if r["payee"] == "Shoe Shop" and r["kind"] == "purchase"]
        self.assertTrue(shoes)
        self.assertEqual({(r["category_status"], r["category_level"], r["category_source"]) for r in shoes},
                         {("placed", CLOTHING, "pin")})  # the pin's spelling ("shoe  shop") still finds the merchant

    def test_a_pinned_merchant_is_never_asked_about_and_not_in_the_review_list(self):
        self.assertNotIn("Shoe Shop", {merchant["payee"] for merchant in self.asked})
        self.assertIn("Store", {merchant["payee"] for merchant in self.asked})  # the others are asked as before
        self.assertNotIn("Shoe Shop", {line["payee"] for line in self.review})


class BadPinTests(PinCase):
    def test_a_category_not_in_use_stops_the_run_before_any_request_naming_the_line_and_the_value(self):
        # the only whole (early-stopping) run here: that the check comes before the first request is what only a run shows
        code, _, err, _ = self.run_household(*self.pins({"payee": "Store", "category": CLOTHING},
                                                        {"payee": "Shoe Shop", "category": "Fun"}))
        self.assertNotEqual(code, 0)
        self.assertIn("line 2", err)
        self.assertIn("'Fun'", err)
        self.assertEqual(self.asked, [])

    def test_the_check_names_the_line_and_the_value_of_a_category_that_is_not_in_the_list(self):
        pins = [{"payee": "Store", "category": CLOTHING}, {"payee": "Shoe Shop", "category": "Fun"}]
        with self.assertRaises(ValueError) as refused:
            run_state("check_pin_categories", pins_file=pins, taxonomy=TAXONOMY)
        self.assertIn("line 2", str(refused.exception))
        self.assertIn("'Fun'", str(refused.exception))

    def test_a_line_without_a_merchant_is_named_by_the_check(self):
        with self.assertRaises(ValueError) as refused:
            run_state("check_pins", pins_file=[{"payee": "", "category": CLOTHING}])
        self.assertIn("line 1 has no payee", str(refused.exception))

    def test_a_pin_file_named_with_a_path_that_does_not_exist_is_refused_naming_it_before_the_run_starts(self):
        missing = self.dir / "nowhere.jsonl"
        values = {"monarch": str(ORACLE / "monarch.csv"), "amex": str(ORACLE / "amex.csv"), "amex_account": "Platinum",
                  "since": "2026-01-01", "pinned": str(missing)}
        with self.assertRaises(PlayError) as refused:
            load_checked(LEDGER, {}, values)
        self.assertIn(str(missing), str(refused.exception.problems))


class NoPinFileTests(PinCase):
    def test_without_a_path_and_without_the_default_file_the_run_has_no_pins_and_says_so(self):
        values = {"monarch": str(ORACLE / "monarch.csv"), "amex": str(ORACLE / "amex.csv"), "amex_account": "Platinum",
                  "since": "2026-01-01"}  # no `pinned`: the default `.understudy/pinned.jsonl`, read from where you run
        said: list[str] = []
        previous = Path.cwd()
        os.chdir(self.dir)
        try:
            import asyncio

            rows = asyncio.run(read_stage(load_checked(LEDGER, {}, values), "pins_file", announce=said.append))
        finally:
            os.chdir(previous)
        self.assertEqual(rows, [])
        self.assertTrue(any("no pins_file:" in line and "so none are used" in line for line in said))


if __name__ == "__main__":
    unittest.main()
