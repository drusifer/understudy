import asyncio
import unittest
from types import SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import adjacent_runs, prefer_middle, prefer_order, reduce_max, reduce_min, weigh

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
        scored = run(prefer_middle, context(runs=runs), "runs", "seats", "row", "number", "centre_score",
                     {"showing": "19:30", "row": "E"})
        self.assertEqual({r["run"]: round(r["centre_score"], 3) for r in scored}, {"E5-6": 1.0, "E1-2": 0.111, "E9-10": 0.111})


ROWS = [{"run": "A", "row_score": 1.0, "centre_score": 0.2}, {"run": "B", "row_score": 0.5, "centre_score": 1.0},
        {"run": "C", "row_score": 0.0, "centre_score": 0.6}]


class WeighTests(unittest.TestCase):
    def weighed(self, by):
        return {r["run"]: round(r["score"], 3) for r in run(weigh, context(rows=ROWS), "rows", by, "score")}

    def test_each_row_gets_the_weighted_sum_of_its_fields(self):
        self.assertEqual(self.weighed({"row_score": 0.5, "centre_score": 0.5}), {"A": 0.6, "B": 0.75, "C": 0.3})

    def test_the_weights_decide_which_field_matters(self):
        self.assertEqual(self.weighed({"row_score": 1.0, "centre_score": 0.0}), {"A": 1.0, "B": 0.5, "C": 0.0})

    def test_the_rows_keep_their_own_fields(self):
        (row, *_) = run(weigh, context(rows=ROWS), "rows", {"row_score": 1.0}, "score")
        self.assertEqual(row["run"], "A")


class MaxMinTests(unittest.TestCase):
    def kept(self, reducer, field, take=1):
        return [r["run"] for r in run(reducer, context(rows=ROWS), "rows", field, take)]

    def test_max_keeps_the_highest_first_and_min_the_lowest_first(self):
        self.assertEqual(self.kept(reduce_max, "centre_score"), ["B"])
        self.assertEqual(self.kept(reduce_min, "centre_score"), ["A"])

    def test_take_keeps_the_best_n_and_fewer_rows_keep_them_all(self):
        self.assertEqual(self.kept(reduce_max, "centre_score", take=2), ["B", "C"])
        self.assertEqual(self.kept(reduce_max, "row_score", take=10), ["A", "B", "C"])

    def test_they_are_reduce_stages_with_take_defaulting_to_one(self):
        for name in ("reduce.max", "reduce.min"):
            required = [key for key, p in STAGES[name].params.items() if p.required]
            self.assertEqual(required, ["source", "field"])


if __name__ == "__main__":
    unittest.main()
