import unittest
from datetime import date

from src.sketch.dates import business_days_between, to_cents, to_date


class DateTests(unittest.TestCase):
    def test_both_export_date_styles_are_read_month_first(self):
        self.assertEqual((to_date("2026-02-01"), to_date("02/01/2026"), to_date("12/30/2025")),
                         (date(2026, 2, 1), date(2026, 2, 1), date(2025, 12, 30)))

    def test_no_date_is_none(self):
        self.assertEqual((to_date(""), to_date("not a date"), to_date(None)), (None, None, None))

    def test_amounts_become_cents(self):
        self.assertEqual([to_cents(t) for t in ("-4.50", "$1,200.00", "(4.50)", "30", "", "x")],
                         [-450, 120000, -450, 3000, None, None])

    def test_a_weekend_is_not_a_business_day_gap(self):
        friday, saturday, sunday, monday = date(2026, 3, 6), date(2026, 3, 7), date(2026, 3, 8), date(2026, 3, 9)
        self.assertEqual((business_days_between(friday, monday), business_days_between(saturday, sunday),
                          business_days_between(monday, friday)), (1, 0, 1))

    def test_a_federal_holiday_is_skipped(self):
        # Monday 2026-05-25 is Memorial Day: Friday to the Tuesday after is 1 business day
        self.assertEqual(business_days_between(date(2026, 5, 22), date(2026, 5, 26)), 1)


if __name__ == "__main__":
    unittest.main()
