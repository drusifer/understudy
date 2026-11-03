"""UND-96: the clean list of categories (ISO 18245 plus the owner's additions) and its checks."""

import json
from pathlib import Path

from test_household_pins import PinCase

from src.paths import ROOT
from src.sketch.mcc import load_mcc

SHIPPED = ROOT / "examples" / "household" / "additions.jsonl"
FAMILY = "Clothing outlets: Family clothing shops"  # an ISO category


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TaxonomyCase(PinCase):
    def additions(self, *rows) -> list[str]:
        path = self.dir / "additions.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return ["--with", f"additions={path}", *self.pins()]

    def taxonomy_of(self, *extra):
        code, _, err, folder = self.run_household(*extra)
        return code, err, (lines(folder / "taxonomy.jsonl") if folder else [])


class ShippedListTests(TaxonomyCase):
    def test_the_list_has_every_iso_group_and_name_and_the_shipped_additions_each_as_group_and_name(self):
        code, err, rows = self.taxonomy_of(*self.pins())
        self.assertEqual((code, err), (0, ""))
        iso = load_mcc()
        self.assertEqual(sum(row["origin"] == "iso" for row in rows), sum(len(names) for names in iso.values()))
        self.assertEqual({row["group"] for row in rows if row["origin"] == "iso"}, set(iso))
        self.assertIn(FAMILY, {row["category"] for row in rows})
        self.assertEqual(sum(row["origin"] == "iso" for row in rows), 280)

    def test_a_starting_file_of_the_owners_additions_ships_with_the_household_sketch(self):
        shipped = lines(SHIPPED)
        self.assertEqual({(row["group"], row["name"]) for row in shipped},
                         {("Household", name) for name in ("Rent", "Mortgage", "Tuition", "Income", "Transfer", "Loan repayment")})
        _, _, rows = self.taxonomy_of(*self.pins())
        owner = {row["category"] for row in rows if row["origin"] == "owner"}
        self.assertEqual(owner, {f"Household: {name}" for name in
                                 ("Rent", "Mortgage", "Tuition", "Income", "Transfer", "Loan repayment")})


class OwnersFileTests(TaxonomyCase):
    def test_the_owners_file_replaces_the_shipped_one(self):
        code, err, rows = self.taxonomy_of(*self.additions({"group": "Pets", "name": "Vet bills"}))
        self.assertEqual((code, err), (0, ""))
        owner = {row["category"] for row in rows if row["origin"] == "owner"}
        self.assertEqual(owner, {"Pets: Vet bills"})

    def test_a_path_that_does_not_exist_stops_the_run_naming_it_before_any_request(self):
        missing = self.dir / "nowhere.jsonl"
        code, _, err, _ = self.run_household("--with", f"additions={missing}")
        self.assertNotEqual(code, 0)
        self.assertIn(str(missing), err)
        self.assertEqual(self.asked, [])

    def test_a_relative_path_that_does_not_exist_is_named_as_typed_and_as_looked_for(self):
        code, _, err, _ = self.run_household("--with", "additions=data/nowhere.jsonl")
        self.assertNotEqual(code, 0)
        self.assertIn("file data/nowhere.jsonl does not exist (looked for ", err)
        self.assertEqual(self.asked, [])

    def test_a_line_without_a_group_or_a_name_stops_the_run_naming_the_line(self):
        for row, field in (({"group": "Pets", "name": ""}, "name"), ({"name": "Vet bills"}, "group")):
            code, _, err, _ = self.run_household(*self.additions({"group": "Pets", "name": "Fish"}, row), name=f"out-{field}")
            self.assertNotEqual(code, 0)
            self.assertIn(f"line 2 has no {field}", err)
            self.assertEqual(self.asked, [])

    def test_a_name_that_repeats_an_iso_name_or_an_earlier_addition_stops_the_run_naming_the_line(self):
        code, _, err, _ = self.run_household(*self.additions({"group": "Household", "name": "Family clothing shops"}))
        self.assertNotEqual(code, 0)
        self.assertIn("line 1 repeats 'Family clothing shops' (also in", err)
        code, _, err, _ = self.run_household(*self.additions({"group": "Household", "name": "Pets"},
                                                              {"group": "Other", "name": "pets "}), name="again")
        self.assertNotEqual(code, 0)
        self.assertIn("line 2 repeats 'pets ' (first on line 1)", err)
        self.assertEqual(self.asked, [])


class PinsAgainstTheListTests(TaxonomyCase):
    def test_a_pin_names_a_category_in_the_clean_list_an_iso_one_or_an_addition(self):
        for category in (FAMILY, "Household: Rent"):
            code, _, err, _ = self.run_household(*self.pins({"payee": "Shoe Shop", "category": category}), name=category[:5])
            self.assertEqual((code, err), (0, ""), category)

    def test_a_category_that_is_only_in_the_export_is_refused_before_any_request(self):
        code, _, err, _ = self.run_household(*self.pins({"payee": "Shoe Shop", "category": "Shopping & Retail: Clothing"}))
        self.assertNotEqual(code, 0)
        self.assertIn("line 1", err)
        self.assertIn("'Shopping & Retail: Clothing'", err)
        self.assertEqual(self.asked, [])
