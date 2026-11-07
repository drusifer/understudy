"""UND-118: a small summary of a list of rows, for the beat box to draw as a gauge, a donut or bars."""

import json
import unittest

from src.play.profile import ITEM_CHARS, ITEM_FIELDS, MAX_COLUMNS, VALUE_CHARS, brief, profile


def column(found, name):
    return next(each for each in found if each["name"] == name)


class ProfileTests(unittest.TestCase):
    def test_an_empty_list_has_no_columns(self):
        self.assertEqual(profile([]), [])

    def test_a_number_column_is_its_range_and_mean(self):
        found = profile([{"amount": 2}, {"amount": 4}, {"amount": 9}])
        self.assertEqual(column(found, "amount"), {"name": "amount", "kind": "number", "rows": 3, "min": 2, "max": 9, "mean": 5})

    def test_a_text_column_is_its_commonest_values_and_how_many_there_are(self):
        rows = [{"kind": "a"}] * 5 + [{"kind": "b"}] * 3 + [{"kind": "c"}] * 2
        found = column(profile(rows), "kind")
        self.assertEqual((found["kind"], found["rows"], found["distinct"]), ("text", 10, 3))
        self.assertEqual(found["top"], [["a", 5], ["b", 3], ["c", 2]])

    def test_only_the_five_commonest_values_are_kept_and_long_ones_are_cut(self):
        rows = [{"payee": f"merchant {number} " + "x" * 80} for number in range(20)]
        found = column(profile(rows), "payee")
        self.assertEqual(found["distinct"], 20)
        self.assertEqual(len(found["top"]), 5)
        self.assertTrue(all(len(value) <= VALUE_CHARS for value, _ in found["top"]))

    def test_booleans_are_text_not_numbers_and_lists_and_dicts_are_other(self):
        found = profile([{"flag": True, "items": [1, 2], "meta": {"a": 1}}, {"flag": False, "items": [], "meta": {}}])
        self.assertEqual(column(found, "flag")["kind"], "text")
        self.assertEqual(column(found, "flag")["top"], [["True", 1], ["False", 1]])
        self.assertEqual(column(found, "items")["kind"], "other")
        self.assertEqual(column(found, "meta")["kind"], "other")

    def test_missing_and_null_values_are_not_counted_and_a_column_of_nothing_is_left_out(self):
        found = profile([{"a": 1, "b": None}, {"a": None}, {"a": 3}])
        self.assertEqual(column(found, "a")["rows"], 2)
        self.assertEqual(column(found, "a")["mean"], 2)
        self.assertEqual([each["name"] for each in found], ["a"])

    def test_a_column_that_mixes_numbers_and_text_is_text(self):
        self.assertEqual(column(profile([{"a": 1}, {"a": "two"}]), "a")["kind"], "text")

    def test_at_most_six_columns_numbers_first_then_text_then_other(self):
        row = {"z_list": [1], "t1": "x", "t2": "y", "n1": 1, "n2": 2, "n3": 3, "n4": 4, "t3": "z", "t4": "w"}
        found = profile([row])
        self.assertEqual(len(found), MAX_COLUMNS)
        self.assertEqual([each["kind"] for each in found], ["number"] * 4 + ["text"] * 2)

    def test_it_is_small_enough_for_a_log_line_and_plain_json(self):
        rows = [{"payee": f"m{number % 50}", "amount": number * 1.5, "memo": "y" * 200} for number in range(2000)]
        text = json.dumps(profile(rows))
        self.assertLess(len(text), 1500)


class ItemTests(unittest.TestCase):
    """One pass of a repeated beat shows its row as a few labeled values."""

    def test_a_row_keeps_its_scalar_values_cut_short_and_shows_a_list_or_dict_by_its_size(self):
        found = brief({"title": "T" * 500, "n": 3, "ok": True, "tags": [1, 2, 3], "meta": {"a": 1}, "none": None})
        self.assertEqual(len(found["title"]), ITEM_CHARS)
        self.assertEqual((found["n"], found["ok"], found["tags"], found["meta"]), (3, True, "3 items", "1 field"))
        self.assertNotIn("none", found)

    def test_a_wide_row_keeps_the_first_dozen_fields(self):
        self.assertEqual(len(brief({f"f{number}": number for number in range(40)})), ITEM_FIELDS)


if __name__ == "__main__":
    unittest.main()
