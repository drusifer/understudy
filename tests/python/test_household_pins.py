import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from jev_double import JevDouble
from test_household import LEDGER, ORACLE, category, lines

from src.jev import Chosen
from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

CLOTHING = "Clothing outlets: Family clothing shops"  # a category in the clean list (ISO 18245)


class PinCase(unittest.TestCase):
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
        if "refund" in state:
            original = next(label for label in options if "2026-02-15" in label)
            return Chosen(original, 0.8, {label: 0.8 if label == original else 0.2 for label in options})
        if "merchant" in state:
            merchant = state["merchant"][0]["merchant"]
            self.asked.append(merchant)
            return category(merchant, options)
        raise AssertionError(f"unexpected question: {list(state)}")

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


class PinnedMerchantTests(PinCase):
    def setUp(self):
        super().setUp()
        self.code, self.out, self.err, self.folder = self.run_household(
            *self.pins({"payee": "shoe  shop", "category": CLOTHING}))
        self.records = lines(self.folder / "records.jsonl")

    def test_a_pinned_merchants_records_are_placed_in_its_category_and_show_they_were_pinned(self):
        shoes = [r for r in self.records if r["payee"] == "Shoe Shop" and r["kind"] == "purchase"]
        self.assertEqual(self.code, 0)
        self.assertEqual({(r["category_status"], r["category_level"], r["category_source"]) for r in shoes},
                         {("placed", CLOTHING, "pin")})

    def test_a_pinned_merchant_is_never_asked_about_and_not_in_the_review_list(self):
        self.assertNotIn("Shoe Shop", self.asked)
        self.assertIn("Store", self.asked)  # the others are asked as before
        self.assertNotIn("Shoe Shop", {line["payee"] for line in lines(self.folder / "review.jsonl")})

    def test_the_same_pins_and_files_place_the_same_merchants_the_same_way(self):
        _, _, _, again = self.run_household(*self.pins({"payee": "shoe  shop", "category": CLOTHING}), name="again")
        self.assertEqual((self.folder / "records.jsonl").read_text(encoding="utf-8"),
                         (again / "records.jsonl").read_text(encoding="utf-8"))


class BadPinTests(PinCase):
    def test_a_category_not_in_use_stops_the_run_before_any_request_naming_the_line_and_the_value(self):
        code, _, err, _ = self.run_household(*self.pins({"payee": "Store", "category": CLOTHING},
                                                        {"payee": "Shoe Shop", "category": "Fun"}))
        self.assertNotEqual(code, 0)
        self.assertIn("line 2", err)
        self.assertIn("'Fun'", err)
        self.assertEqual(self.asked, [])

    def test_a_line_without_a_merchant_stops_the_run_before_any_request_naming_the_line(self):
        code, _, err, _ = self.run_household(*self.pins({"payee": "", "category": CLOTHING}))
        self.assertNotEqual(code, 0)
        self.assertIn("line 1 has no payee", err)
        self.assertEqual(self.asked, [])

    def test_a_pin_file_named_with_a_path_that_does_not_exist_stops_the_run_naming_it(self):
        missing = self.dir / "nowhere.jsonl"
        code, _, err, _ = self.run_household("--with", f"pinned={missing}")
        self.assertNotEqual(code, 0)
        self.assertIn(str(missing), err)
        self.assertEqual(self.asked, [])


class NoPinFileTests(PinCase):
    def test_without_a_path_and_without_the_default_file_the_run_has_no_pins_and_says_so(self):
        previous = Path.cwd()
        os.chdir(self.dir)  # the default `.understudy/pinned.jsonl` is read from where you run
        try:
            code, out, _, _ = self.run_household()
        finally:
            os.chdir(previous)
        self.assertEqual(code, 0)
        self.assertIn("no pins_file:", out)
        self.assertIn("so none are used", out)


if __name__ == "__main__":
    unittest.main()
