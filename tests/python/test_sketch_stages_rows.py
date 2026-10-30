import asyncio
import unittest
from types import SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import adjacent_runs, prefer_middle, prefer_order

SEATS = [{"showing": "19:30", "row": "E", "number": n, "free": n in (3, 4, 5, 8, 9)} for n in range(1, 11)] + [
    {"showing": "19:30", "row": "F", "number": n, "free": True} for n in range(1, 7)
] + [{"showing": "21:00", "row": "E", "number": n, "free": True} for n in range(1, 4)]


def context(last=None):
    async def read(name):
        return SEATS

    return SimpleNamespace(read=read, last=last)


def run(stage, *args, **kwargs):
    return asyncio.run(stage(*args, **kwargs))


FREE_E = {"showing": "19:30", "row": "E", "free": True}


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
        params = STAGES["etl.adjacent_runs"].params
        self.assertEqual([name for name, p in params.items() if p.required], ["source", "group", "order", "length"])


class PreferOrderTests(unittest.TestCase):
    def test_the_first_listed_value_weighs_most_and_an_unlisted_one_nothing(self):
        rows = [{"row": "F", "run": "F1-2"}, {"row": "E", "run": "E3-4"}, {"row": "D", "run": "D1-2"}, {"row": "A", "run": "A1-2"}]
        weights = run(prefer_order, context(rows), "row", ["E", "F", "D"], "run", "seat")
        self.assertEqual({r["seat"]: round(r["weight"], 3) for r in weights}, {"F1-2": 0.667, "E3-4": 1.0, "D1-2": 0.333, "A1-2": 0.0})


class PreferMiddleTests(unittest.TestCase):
    def weights(self, runs):
        return {r["seat"]: round(r["weight"], 3)
                for r in run(prefer_middle, context(runs), "seats", "row", "number", "run", "seat", {"showing": "19:30", "row": "E"})}

    def test_a_run_in_the_middle_of_the_row_weighs_most_and_the_ends_least(self):
        runs = [{"row": "E", "first": 5, "last": 6, "run": "E5-6"}, {"row": "E", "first": 1, "last": 2, "run": "E1-2"},
                {"row": "E", "first": 9, "last": 10, "run": "E9-10"}]
        self.assertEqual(self.weights(runs), {"E5-6": 1.0, "E1-2": 0.111, "E9-10": 0.111})


if __name__ == "__main__":
    unittest.main()
