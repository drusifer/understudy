"""UND-96: the clean list of categories (ISO 18245 plus the owner's additions) and its checks.

The list is the household's `taxonomy` source and the checks are its own check states, so both are tested on their own
(`fragment`, `run_state`); one whole early-stopping run shows that a bad additions file stops the run before the first
request to Jev, which only a run can show.
"""

import asyncio
import json
import unittest
from pathlib import Path

from household_fragment import ORACLE, fragment, run_state
from test_household import LEDGER
from test_household_pins import PinCase

from src.paths import ROOT
from src.sketch.check import load_checked
from src.sketch.fragment import read_stage
from src.sketch.loader import SketchError
from src.sketch.mcc import load_mcc

SHIPPED = ROOT / "examples" / "household" / "additions.jsonl"
FAMILY = "Clothing outlets: Family clothing shops"  # an ISO category
HOUSEHOLD = ("Rent", "Mortgage", "Tuition", "Income", "Transfer", "Loan repayment")


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class ShippedListTests(unittest.TestCase):
    def test_the_list_has_every_iso_group_and_name_and_the_shipped_additions_each_as_group_and_name(self):
        rows, _ = fragment("taxonomy")
        iso = load_mcc()
        self.assertEqual(sum(row["origin"] == "iso" for row in rows), sum(len(names) for names in iso.values()))
        self.assertEqual({row["group"] for row in rows if row["origin"] == "iso"}, set(iso))
        self.assertIn(FAMILY, {row["category"] for row in rows})
        self.assertEqual(sum(row["origin"] == "iso" for row in rows), 280)

    def test_a_starting_file_of_the_owners_additions_ships_with_the_household_sketch(self):
        shipped = lines(SHIPPED)
        self.assertEqual({(row["group"], row["name"]) for row in shipped}, {("Household", name) for name in HOUSEHOLD})
        rows, _ = fragment("taxonomy")
        owner = {row["category"] for row in rows if row["origin"] == "owner"}
        self.assertEqual(owner, {f"Household: {name}" for name in HOUSEHOLD})


class OwnersFileTests(PinCase):
    def sketch_with(self, additions: str):
        values = {"monarch": str(ORACLE / "monarch.csv"), "amex": str(ORACLE / "amex.csv"), "amex_account": "Platinum",
                  "since": "2026-01-01", "pinned": str(self.dir / "pins.jsonl"), "additions": additions}
        (self.dir / "pins.jsonl").write_text("", encoding="utf-8")
        return load_checked(LEDGER, {}, values)

    def additions_file(self, *rows) -> str:
        path = self.dir / "additions.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return str(path)

    def test_the_owners_file_replaces_the_shipped_one(self):
        sketch = self.sketch_with(self.additions_file({"group": "Pets", "name": "Vet bills"}))
        rows = asyncio.run(read_stage(sketch, "taxonomy"))
        self.assertEqual({row["category"] for row in rows if row["origin"] == "owner"}, {"Pets: Vet bills"})

    def test_a_path_that_does_not_exist_is_refused_naming_it_before_the_run_starts(self):
        missing = self.dir / "nowhere.jsonl"
        with self.assertRaises(SketchError) as refused:
            self.sketch_with(str(missing))
        self.assertIn(str(missing), str(refused.exception.problems))

    def test_a_relative_path_that_does_not_exist_is_named_as_typed_and_as_looked_for(self):
        with self.assertRaises(SketchError) as refused:
            self.sketch_with("data/nowhere.jsonl")
        self.assertIn("file data/nowhere.jsonl does not exist (looked for ", str(refused.exception.problems))

    def test_a_line_without_a_group_or_a_name_is_named_by_the_check(self):
        for row, field in (({"group": "Pets", "name": ""}, "name"), ({"name": "Vet bills"}, "group")):
            with self.assertRaises(ValueError) as refused:
                run_state("check_additions", additions_file=[{"group": "Pets", "name": "Fish"}, row])
            self.assertIn(f"line 2 has no {field}", str(refused.exception))

    def test_a_name_that_repeats_an_iso_name_or_an_earlier_addition_is_named_by_the_check(self):
        with self.assertRaises(ValueError) as refused:
            run_state("check_additions_unique", additions_file=[{"group": "Household", "name": "Family clothing shops"}])
        self.assertIn("line 1 repeats 'Family clothing shops' (also in", str(refused.exception))
        with self.assertRaises(ValueError) as refused:
            run_state("check_additions_unique", additions_file=[{"group": "Household", "name": "Pets"},
                                                                {"group": "Other", "name": "pets "}])
        self.assertIn("line 2 repeats 'pets ' (first on line 1)", str(refused.exception))

    def test_a_bad_additions_file_stops_the_whole_run_before_any_request_to_jev(self):
        # the only whole (early-stopping) run here: that the check comes first is what only a run shows
        path = self.additions_file({"group": "Pets", "name": "Fish"}, {"group": "Pets", "name": ""})
        code, _, err, _ = self.run_household("--with", f"additions={path}", *self.pins())
        self.assertNotEqual(code, 0)
        self.assertIn("line 2 has no name", err)
        self.assertEqual(self.asked, [])


class PinsAgainstTheListTests(unittest.TestCase):
    def test_a_pin_names_a_category_in_the_clean_list_an_iso_one_or_an_addition(self):
        for category in (FAMILY, "Household: Rent"):
            run_state("check_pin_categories", pins_file=[{"payee": "Shoe Shop", "category": category}])  # does not raise

    def test_a_category_that_is_only_in_the_export_is_refused_naming_the_line_and_the_category(self):
        with self.assertRaises(ValueError) as refused:
            run_state("check_pin_categories", pins_file=[{"payee": "Shoe Shop", "category": "Shopping & Retail: Clothing"}])
        self.assertIn("line 1", str(refused.exception))
        self.assertIn("'Shopping & Retail: Clothing'", str(refused.exception))


if __name__ == "__main__":
    unittest.main()
