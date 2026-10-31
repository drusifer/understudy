import asyncio
import unittest
from types import SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import (
    adjacent_runs,
    expect,
    join,
    prefer_middle,
    prefer_order,
    reduce_max,
    reduce_min,
    unpair,
    weigh,
    where,
)

SEATS = [{"showing": "19:30", "row": "E", "number": n, "free": n in (3, 4, 5, 8, 9)} for n in range(1, 11)] + [
    {"showing": "19:30", "row": "F", "number": n, "free": True} for n in range(1, 7)
] + [{"showing": "21:00", "row": "E", "number": n, "free": True} for n in range(1, 4)]
FREE_E = {"showing": "19:30", "row": "E", "free": True}


def context(**sources):
    """A stage context whose `read` returns the named rows (the seat map is always `seats`)."""
    async def read(name):
        return {"seats": SEATS, **sources}[name]

    return SimpleNamespace(read=read)


def run(stage, *args, **kwargs):
    return asyncio.run(stage(*args, **kwargs))


SHOWINGS = [{"title": "A", "starts": "15:00", "tomato": 95}, {"title": "B", "starts": "19:30", "tomato": 60},
            {"title": "C", "starts": "21:15", "tomato": 80}, {"title": "A", "starts": "20:00", "tomato": 95}]


class WhereTests(unittest.TestCase):
    def kept(self, keep):
        return [(r["title"], r["starts"]) for r in run(where, context(showings=SHOWINGS), "showings", keep)]

    def test_it_keeps_the_rows_that_satisfy_the_condition(self):
        self.assertEqual(self.kept({"tomato": {"ge": 80}}), [("A", "15:00"), ("C", "21:15"), ("A", "20:00")])

    def test_times_are_ordered_as_times_not_as_text(self):
        self.assertEqual(self.kept({"starts": {"ge": "17:00"}}), [("B", "19:30"), ("C", "21:15"), ("A", "20:00")])

    def test_and_or_work_as_everywhere(self):
        keep = {"and": [{"starts": {"ge": "17:00"}}, {"or": [{"title": {"eq": "C"}}, {"tomato": {"lt": 70}}]}]}
        self.assertEqual(self.kept(keep), [("B", "19:30"), ("C", "21:15")])


SCORES = [{"title": "A", "audience": 0.9}, {"title": "C", "audience": 0.4}]


class JoinTests(unittest.TestCase):
    def joined(self):
        return run(join, context(showings=SHOWINGS, scores=SCORES), "showings", "scores", "title")

    def test_a_showing_gets_its_films_fields(self):
        self.assertEqual([(r["title"], r["starts"], r["audience"]) for r in self.joined()],
                         [("A", "15:00", 0.9), ("C", "21:15", 0.4), ("A", "20:00", 0.9)])

    def test_a_showing_with_no_match_is_dropped(self):
        self.assertNotIn("B", [r["title"] for r in self.joined()])

    def test_the_source_rows_own_value_wins_a_clash(self):
        rows = run(join, context(left=[{"k": 1, "v": "mine"}], right=[{"k": 1, "v": "theirs", "w": 2}]), "left", "right", "k")
        self.assertEqual(rows, [{"k": 1, "v": "mine", "w": 2}])


class JoinOnOtherKeyTests(unittest.TestCase):
    def test_the_other_rows_key_may_be_named_differently(self):
        rows = run(join, context(left=[{"showing": "A", "tomato": 90}], right=[{"level": "A", "probability": 0.7}]),
                   "left", "right", "showing", "level")
        self.assertEqual(rows, [{"level": "A", "probability": 0.7, "showing": "A", "tomato": 90}])


class ExpectTests(unittest.TestCase):
    def test_it_averages_your_numbers_by_the_probability_of_each_level(self):
        sketch = SimpleNamespace(data={"values": {"bored": 0.0, "mixed": 0.5, "loved": 1.0}})
        ctx = SimpleNamespace(read=context(p=[{"level": "bored", "probability": 0.1}, {"level": "mixed", "probability": 0.3},
                                              {"level": "loved", "probability": 0.6}]).read, sketch=sketch)
        (row,) = run(expect, ctx, "p", "values", "audience")
        self.assertAlmostEqual(row["audience"], 0.1 * 0.0 + 0.3 * 0.5 + 0.6 * 1.0)


class UnpairTests(unittest.TestCase):
    def test_each_pair_becomes_the_input_row_plus_what_it_output(self):
        pairs = [{"input": {"title": "A"}, "output": [{"audience": 0.9}]},
                 {"input": {"title": "B"}, "output": [{"audience": 0.1}]},
                 {"input": {"title": "C"}, "output": []}]
        self.assertEqual(run(unpair, context(pairs=pairs), "pairs"),
                         [{"title": "A", "audience": 0.9}, {"title": "B", "audience": 0.1}])


class AdjacentRunsTests(unittest.TestCase):
    def runs(self, length, **match):
        return run(adjacent_runs, context(), "seats", "row", "number", length, {**FREE_E, **match})

    def test_runs_of_two_in_row_e_are_overlapping_pairs_of_adjacent_free_seats(self):
        self.assertEqual([r["run"] for r in self.runs(2)], ["E3-4", "E4-5", "E8-9"])

    def test_runs_of_three_need_three_in_a_row(self):
        (only,) = self.runs(3)
        self.assertEqual((only["row"], only["first"], only["last"], only["run"]), ("E", 3, 5, "E3-5"))

    def test_no_run_long_enough_gives_no_rows(self):
        self.assertEqual(self.runs(4), [])

    def test_match_picks_the_showing_so_another_showings_seats_do_not_count(self):
        self.assertEqual([r["run"] for r in self.runs(2, showing="21:00")], ["E1-2", "E2-3"])

    def test_it_is_registered_with_a_typed_signature(self):
        params = STAGES["map.adjacent_runs"].params
        self.assertEqual([name for name, p in params.items() if p.required], ["source", "group", "order", "length"])


class PreferOrderTests(unittest.TestCase):
    def test_the_first_listed_value_scores_most_and_an_unlisted_one_nothing(self):
        rows = [{"row": "F", "run": "F1-2"}, {"row": "E", "run": "E3-4"}, {"row": "D", "run": "D1-2"}, {"row": "A", "run": "A1-2"}]
        scored = run(prefer_order, context(runs=rows), "runs", "row", ["E", "F", "D"], "row_score")
        self.assertEqual({r["run"]: round(r["row_score"], 3) for r in scored},
                         {"F1-2": 0.667, "E3-4": 1.0, "D1-2": 0.333, "A1-2": 0.0})

    def test_the_rows_keep_their_own_fields(self):
        (row,) = run(prefer_order, context(runs=[{"row": "E", "run": "E3-4"}]), "runs", "row", ["E"], "row_score")
        self.assertEqual((row["run"], row["row"]), ("E3-4", "E"))


class PreferMiddleTests(unittest.TestCase):
    def test_a_run_in_the_middle_of_the_row_scores_most_and_the_ends_least(self):
        runs = [{"row": "E", "first": 5, "last": 6, "run": "E5-6"}, {"row": "E", "first": 1, "last": 2, "run": "E1-2"},
                {"row": "E", "first": 9, "last": 10, "run": "E9-10"}]
        scored = run(prefer_middle, context(runs=runs), "runs", "seats", "row", "number", "center_score",
                     {"showing": "19:30", "row": "E"})
        self.assertEqual({r["run"]: round(r["center_score"], 3) for r in scored}, {"E5-6": 1.0, "E1-2": 0.111, "E9-10": 0.111})


ROWS = [{"run": "A", "row_score": 1.0, "center_score": 0.2}, {"run": "B", "row_score": 0.5, "center_score": 1.0},
        {"run": "C", "row_score": 0.0, "center_score": 0.6}]


class WeighTests(unittest.TestCase):
    def weighed(self, by):
        return {r["run"]: round(r["score"], 3) for r in run(weigh, context(rows=ROWS), "rows", by, "score")}

    def test_each_row_gets_the_weighted_sum_of_its_fields(self):
        self.assertEqual(self.weighed({"row_score": 0.5, "center_score": 0.5}), {"A": 0.6, "B": 0.75, "C": 0.3})

    def test_the_weights_decide_which_field_matters(self):
        self.assertEqual(self.weighed({"row_score": 1.0, "center_score": 0.0}), {"A": 1.0, "B": 0.5, "C": 0.0})

    def test_the_rows_keep_their_own_fields(self):
        (row, *_) = run(weigh, context(rows=ROWS), "rows", {"row_score": 1.0}, "score")
        self.assertEqual(row["run"], "A")


class MaxMinTests(unittest.TestCase):
    def kept(self, reducer, field, take=1):
        return [r["run"] for r in run(reducer, context(rows=ROWS), "rows", field, take)]

    def test_max_keeps_the_highest_first_and_min_the_lowest_first(self):
        self.assertEqual(self.kept(reduce_max, "center_score"), ["B"])
        self.assertEqual(self.kept(reduce_min, "center_score"), ["A"])

    def test_take_keeps_the_best_n_and_fewer_rows_keep_them_all(self):
        self.assertEqual(self.kept(reduce_max, "center_score", take=2), ["B", "C"])
        self.assertEqual(self.kept(reduce_max, "row_score", take=10), ["A", "B", "C"])

    def test_they_are_reduce_stages_with_take_defaulting_to_one(self):
        for name in ("reduce.max", "reduce.min"):
            required = [key for key, p in STAGES[name].params.items() if p.required]
            self.assertEqual(required, ["source", "field"])


if __name__ == "__main__":
    unittest.main()


class GroupTests(unittest.TestCase):
    def test_rows_group_by_a_normalized_value_and_collect_a_few_examples(self):
        from src.sketch.stages_rows import group
        rows = [{"merchant": "Dunkin'", "amount": -4.5, "text": "DUNKIN #1"}, {"merchant": " dunkin'  ", "amount": -6.7, "text": ""},
                {"merchant": "Store", "amount": -50.0, "text": "STORE"}]
        found = run(group, context(rows=rows), source="rows", by="merchant", collect={"amounts": "amount", "texts": "text"}, take=1)
        self.assertEqual(found, [
            {"key": "dunkin'", "merchant": "Dunkin'", "count": 2, "amounts": [-4.5], "texts": ["DUNKIN #1"]},
            {"key": "store", "merchant": "Store", "count": 1, "amounts": [-50.0], "texts": ["STORE"]}])


class ClassifyTests(unittest.TestCase):
    CASES = ({"if": {"probability": {"gt": 0.7}}, "then": "external_transfer"},
             {"if": {"probability": {"lt": 0.3}}, "then": "spending"})

    def test_the_first_case_that_holds_names_the_row_and_otherwise_covers_the_rest(self):
        from src.sketch.stages_rows import classify
        rows = [{"probability": p} for p in (0.9, 0.05, 0.5)]
        found = run(classify, context(rows=rows), source="rows", into="decision", cases=self.CASES, otherwise="review")
        self.assertEqual([r["decision"] for r in found], ["external_transfer", "spending", "review"])

    def test_rows_are_numbered_from_one_after_a_prefix(self):
        from src.sketch.stages_rows import number
        found = run(number, context(rows=[{"a": 1}, {"a": 2}]), source="rows", into="id", prefix="m")
        self.assertEqual([r["id"] for r in found], ["m1", "m2"])


class CoalesceTests(unittest.TestCase):
    def test_a_field_takes_the_first_candidate_that_has_a_value(self):
        from src.sketch.stages_rows import coalesce
        rows = [{"Merchant": "Store", "other_Description": "STORE #1"}, {"other_Description": "ATM"}, {"Merchant": ""}]
        found = run(coalesce, context(rows=rows), source="rows", fields={"merchant": ["Merchant", "other_Description"]})
        self.assertEqual([r["merchant"] for r in found], ["Store", "ATM", None])


class CleaningTests(unittest.TestCase):
    def test_replace_removes_the_account_number_and_normalize_makes_a_key(self):
        from src.sketch.stages_rows import normalize, replace
        rows = [{"Account": "Platinum Card (...1111)", "m": "  Dunkin'   DONUTS "}]
        cleaned = run(replace, context(r=rows), source="r", field="Account", pattern=r"\s*\(\.\.\.\d+\)", into="name")
        self.assertEqual(cleaned[0]["name"], "Platinum Card")
        self.assertEqual(run(normalize, context(r=rows), source="r", field="m", into="key")[0]["key"], "dunkin' donuts")

    def test_format_fills_a_template_from_the_row(self):
        from src.sketch.stages_rows import format_text
        rows = context(r=[{"day": "2026-02-15", "cost": 45.0}])
        found = run(format_text, rows, source="r", template="charged_{day}_{cost}", into="label")
        self.assertEqual(found[0]["label"], "charged_2026-02-15_45.0")

    def test_join_can_keep_the_rows_with_no_match(self):
        from src.sketch.stages_rows import join
        found = run(join, context(a=[{"k": 1}, {"k": 2}], b=[{"k": 1, "v": "x"}]), source="a", other="b", on="k", keep_unmatched=True)
        self.assertEqual(found, [{"k": 1, "v": "x"}, {"k": 2}])

    def test_earlier_lists_the_charges_a_refund_could_reverse_most_recent_first(self):
        from src.sketch.stages_rows import earlier
        charges = [{"id": "c1", "m": "s", "d": "2026-02-01", "a": -50.0}, {"id": "c2", "m": "s", "d": "2026-02-15", "a": -45.0},
                   {"id": "c3", "m": "s", "d": "2026-02-20", "a": -10.0}, {"id": "c4", "m": "x", "d": "2026-02-01", "a": -50.0}]
        refunds = [{"id": "r1", "m": "s", "d": "2026-03-12", "a": 45.0}, {"id": "r2", "m": "z", "d": "2026-03-12", "a": 5.0}]
        found = run(earlier, context(r=refunds, c=charges), source="r", other="c", on="m", date="d", amount="a", tie="id")
        self.assertEqual([(f["id"], f.get("candidate_id"), f["candidates"]) for f in found],
                         [("r1", "c2", 2), ("r1", "c1", 2), ("r2", None, 0)])
