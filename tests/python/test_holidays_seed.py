import csv
import unittest
from datetime import date
from pathlib import Path

import holidays

SEED = Path(__file__).resolve().parents[2] / "sqlmesh" / "seeds" / "us_federal_holidays.csv"
FIRST_YEAR, LAST_YEAR = 2024, 2030


class HolidaySeedTests(unittest.TestCase):
    def test_the_seed_is_exactly_what_the_holidays_package_says(self):
        with SEED.open(encoding="utf-8", newline="") as handle:
            seeded = {date.fromisoformat(row["holiday_date"]): row["holiday_name"] for row in csv.DictReader(handle)}
        expected = dict(holidays.US(years=range(FIRST_YEAR, LAST_YEAR + 1), observed=True).items())
        self.assertEqual(seeded, expected)

    def test_the_seed_covers_the_calendar_the_models_build(self):
        with SEED.open(encoding="utf-8", newline="") as handle:
            years = {date.fromisoformat(row["holiday_date"]).year for row in csv.DictReader(handle)}
        self.assertEqual(years, set(range(FIRST_YEAR, LAST_YEAR + 1)))


if __name__ == "__main__":
    unittest.main()
