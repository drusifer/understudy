import itertools
import unittest

from src.sketch.blend import EmptyResultError, Opinion, Policy, blend, forbid, marginals
from src.sketch.conditions import holds
from src.sketch.decide import decide_input, leaf_rows, weight_of

TREE = {
    "if": {"segment": {"eq": "students"}},
    "then": {"drink": [
        {"temp": "iced", "size": "large", "weight": 0.5},
        {"temp": "iced", "size": "medium", "weight": 0.2},
        {"temp": "hot", "size": "medium", "weight": 0.3},
    ]},
    "else": {
        "if": {"segment": {"eq": "night_workers"}},
        "then": {"drink": [{"temp": "hot", "size": "large", "caffeine": "high", "weight": 1.0}]},
        "else": {"drink": [
            {"temp": "hot", "size": "medium", "weight": 0.6},
            {"temp": "iced", "size": "medium", "weight": 0.4},
        ]},
    },
}
UNDER_18 = [{"when": {"age_max": {"le": 17}}, "drop": {"caffeine": {"ne": "none"}}}]


class ConditionTests(unittest.TestCase):
    def test_comparisons(self):
        row = {"age": 17, "job": "nurse", "temp": 85, "merchant": "Blue Bottle Coffee", "tags": ["vegan", "iced"]}
        for condition, expected in (
            ({"job": {"eq": "nurse"}}, True),
            ({"job": {"ne": "nurse"}}, False),
            ({"age": {"lt": 18}}, True),
            ({"age": {"le": 17}}, True),
            ({"age": {"gt": 17}}, False),
            ({"age": {"ge": 17}}, True),
            ({"job": {"in": ["nurse", "driver"]}}, True),
            ({"job": {"not_in": ["nurse", "driver"]}}, False),
            ({"merchant": {"has": "Coffee"}}, True),
            ({"merchant": {"has": "tea"}}, False),
            ({"tags": {"has": "vegan"}}, True),
            ({"tags": {"has": "meat"}}, False),
        ):
            with self.subTest(condition=condition):
                self.assertEqual(holds(condition, row), expected)

    def test_a_slice_includes_its_start_and_excludes_its_stop(self):
        band = {"temp": {"in": ["80:90"]}}
        self.assertTrue(holds(band, {"temp": 80}))
        self.assertTrue(holds(band, {"temp": 89.9}))
        self.assertFalse(holds(band, {"temp": 90}))
        self.assertFalse(holds(band, {"temp": 79.9}))
        self.assertFalse(holds({"temp": {"in": ["80:90"]}}, {"temp": "warm"}))
        self.assertTrue(holds({"temp": {"not_in": ["80:90"]}}, {"temp": 90}))

    def test_and_or_not_and_several_fields(self):
        row = {"genre": "horror", "tomato": 75}
        self.assertTrue(holds({"genre": {"eq": "horror"}, "tomato": {"ge": 70}}, row))
        self.assertFalse(holds({"genre": {"eq": "horror"}, "tomato": {"ge": 80}}, row))
        gate = {"or": [{"genre": {"eq": "horror"}, "tomato": {"ge": 80}}, {"tomato": {"gt": 90}}]}
        self.assertFalse(holds(gate, row))
        self.assertTrue(holds(gate, {**row, "tomato": 91}))
        self.assertTrue(holds({"not": {"genre": {"eq": "comedy"}}}, row))
        self.assertTrue(holds({"and": [{"tomato": {"ge": 70}}, {"tomato": {"lt": 80}}]}, row))

    def test_a_field_the_row_lacks_never_matches(self):
        for operator in ("eq", "ne", "lt", "in", "not_in", "has"):
            with self.subTest(operator=operator):
                self.assertFalse(holds({"missing": {operator: ["x"] if "in" in operator else 1}}, {"other": 1}))


class DecideTests(unittest.TestCase):
    def test_the_leaf_a_row_reaches_is_used_as_written(self):
        rows = leaf_rows(TREE, {"segment": "students"})
        self.assertEqual([r["weight"] for r in rows], [0.5, 0.2, 0.3])
        self.assertEqual(leaf_rows(TREE, {"segment": "night_workers"})[0]["caffeine"], "high")
        self.assertEqual(len(leaf_rows(TREE, {"segment": "others"})), 2)

    def test_no_branch_and_no_else_is_no_opinion(self):
        tree = {"if": {"segment": {"eq": "students"}}, "then": {"drink": [{"temp": "hot", "weight": 1}]}}
        self.assertEqual(leaf_rows(tree, {"segment": "teens"}), [])

    def test_weights_are_numbers_or_if_then_else(self):
        night = {"if": {"segment": {"eq": "night_workers"}}, "then": 0, "else": 0.3}
        self.assertEqual(weight_of(0.8, {}), 0.8)
        self.assertEqual(weight_of(night, {"segment": "night_workers"}), 0)
        self.assertEqual(weight_of(night, {"segment": "students"}), 0.3)
        self.assertEqual(weight_of({"if": {"a": {"eq": 1}}, "then": 5}, {"a": 2}), 0)
        nested = {"if": {"a": {"eq": 1}}, "then": {"if": {"b": {"eq": 1}}, "then": 7, "else": 3}, "else": 1}
        self.assertEqual(weight_of(nested, {"a": 1, "b": 1}), 7)
        self.assertEqual(weight_of(nested, {"a": 1, "b": 2}), 3)


class BlendTests(unittest.TestCase):
    def test_marginals_are_per_dimension_and_ignore_rows_that_do_not_name_it(self):
        rows = [{"temp": "iced", "size": "large", "weight": 0.5}, {"temp": "hot", "size": "medium", "weight": 0.3},
                {"temp": "hot", "caffeine": "high", "weight": 0.2}]
        shares = marginals(rows)
        self.assertAlmostEqual(shares["temp"]["iced"], 0.5)
        self.assertAlmostEqual(shares["temp"]["hot"], 0.5)
        self.assertEqual(shares["caffeine"], {"high": 1.0})
        self.assertAlmostEqual(shares["size"]["large"], 0.5 / 0.8)

    def test_the_blend_is_a_weighted_average_of_the_deciders_naming_the_dimension(self):
        history = Opinion(0.8, [{"temp": "iced", "weight": 0.3}, {"temp": "hot", "weight": 0.7}])
        weather = Opinion(0.3, [{"temp": "iced", "weight": 0.9}, {"temp": "hot", "weight": 0.1}])
        rule = Opinion(0.2, [{"temp": "iced", "weight": 1.0}])
        mixed = blend([history, weather, rule])
        self.assertAlmostEqual(mixed["temp"]["iced"], (0.8 * 0.3 + 0.3 * 0.9 + 0.2 * 1.0) / 1.3)
        self.assertAlmostEqual(sum(mixed["temp"].values()), 1.0)

    def test_a_decider_with_weight_zero_has_no_say_and_a_lone_decider_keeps_its_shares(self):
        tree = Opinion(1, [{"temp": "hot", "size": "large", "weight": 1.0}])
        off = Opinion(0, [{"temp": "iced", "weight": 1.0}])
        self.assertEqual(blend([tree, off]), {"temp": {"hot": 1.0}, "size": {"large": 1.0}})

    def test_a_dimension_only_one_decider_names_is_not_diluted(self):
        tree = Opinion(1, [{"size": "large", "weight": 1.0}])
        weather = Opinion(0.3, [{"temp": "iced", "weight": 1.0}])
        self.assertEqual(blend([tree, weather]), {"size": {"large": 1.0}, "temp": {"iced": 1.0}})


class ForbidTests(unittest.TestCase):
    def test_a_forbidden_option_is_dropped_and_the_rest_renormalised(self):
        dist = {"caffeine": {"none": 0.5, "high": 0.5}}
        self.assertEqual(forbid(dist, UNDER_18, {"age_max": 17}, "teens"), {"caffeine": {"none": 1.0}})

    def test_a_rule_that_does_not_apply_changes_nothing(self):
        dist = {"caffeine": {"none": 0.5, "high": 0.5}}
        self.assertEqual(forbid(dist, UNDER_18, {"age_max": 24}, "students"), dist)

    def test_emptying_a_dimension_fails_naming_the_rule_and_the_row(self):
        with self.assertRaises(EmptyResultError) as caught:
            forbid({"caffeine": {"high": 1.0}}, UNDER_18, {"age_max": 17}, "teens")
        self.assertIn("forbid rule 0", str(caught.exception))
        self.assertIn("teens", str(caught.exception))
        self.assertIn("caffeine", str(caught.exception))

    def test_skip_removes_the_dimension_and_fallback_spreads_over_what_is_allowed(self):
        dist = {"caffeine": {"high": 1.0}, "temp": {"hot": 1.0}}
        skipped = forbid(dist, UNDER_18, {"age_max": 17}, "teens", Policy("skip"))
        self.assertEqual(skipped, {"temp": {"hot": 1.0}})
        allowed = {"caffeine": ("none", "regular", "high")}
        spread = forbid(dist, UNDER_18, {"age_max": 17}, "teens", Policy("fallback", allowed))
        self.assertEqual(spread["caffeine"], {"none": 1.0})

    def test_fallback_fails_when_nothing_is_allowed(self):
        with self.assertRaises(EmptyResultError):
            forbid({"caffeine": {"high": 1.0}}, UNDER_18, {"age_max": 17}, "teens", Policy("fallback", {"caffeine": ("high",)}))


STATE = {
    "blend": [
        {"decide": TREE},
        {"from": "weather", "weight": {"if": {"segment": {"eq": "night_workers"}}, "then": 0, "else": 0.3}},
    ],
    "forbid": UNDER_18,
}
WEATHER = [{"temp": "iced", "weight": 0.7}, {"temp": "hot", "weight": 0.3}]


class DecideInputTests(unittest.TestCase):
    def test_the_weather_nudges_students_but_not_night_workers(self):
        students = decide_input(STATE, {"segment": "students", "age_max": 24}, {"weather": WEATHER})
        night = decide_input(STATE, {"segment": "night_workers", "age_min": 25}, {"weather": WEATHER})
        self.assertAlmostEqual(students["temp"]["iced"], (1 * 0.7 + 0.3 * 0.7) / 1.3)
        self.assertEqual(night["temp"], {"hot": 1.0})
        self.assertEqual(night["caffeine"], {"high": 1.0})

    def test_teens_are_never_given_caffeine_whatever_the_deciders_say(self):
        grid = [0.0, 0.2, 0.5, 1.0]
        for caffeine_weight, none_weight, decider_weight in itertools.product(grid, grid, grid):
            if caffeine_weight + none_weight == 0:
                continue
            tree = {"drink": [{"caffeine": "high", "weight": caffeine_weight}, {"caffeine": "none", "weight": none_weight}]}
            state = {"blend": [{"decide": tree, "weight": decider_weight}, {"decide": tree}], "forbid": UNDER_18,
                     "on_empty": "skip"}
            result = decide_input(state, {"segment": "teens", "age_max": 17}, {})
            self.assertNotIn("high", result.get("caffeine", {}))
            for options in result.values():
                self.assertAlmostEqual(sum(options.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
