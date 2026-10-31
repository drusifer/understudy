import asyncio
import unittest
from types import SimpleNamespace

from src.sketch.stages_pair import convert, mutual_nearest, pair


def context(**sources):
    async def read(name):
        return sources[name]

    return SimpleNamespace(read=read)


def go(stage, ctx, **kwargs):
    return asyncio.run(stage(ctx, **kwargs))


def row(date, amount, text="", n=0):
    return {"date": date, "amount": amount, "text": text, "n": n}


class ConvertTests(unittest.TestCase):
    def test_dates_and_amounts_are_added_beside_the_text(self):
        rows = [{"Date": "03/05/2026", "Amount": "(4.50)"}, {"Date": "", "Amount": "x"}]
        found = go(convert, context(raw=rows), source="raw", dates={"Date": "date"}, amounts={"Amount": "amount"})
        self.assertEqual(found, [{"Date": "03/05/2026", "Amount": "(4.50)", "date": "2026-03-05", "amount": -4.5},
                                 {"Date": "", "Amount": "x", "date": None, "amount": None}])


class MutualNearestTests(unittest.TestCase):
    def test_two_rows_pair_when_each_is_the_others_nearest(self):
        self.assertEqual(sorted(mutual_nearest([(0, 0, 1), (0, 1, 2), (1, 0, 3), (1, 1, 1)], rounds=1)), [(0, 0, 1), (1, 1, 1)])

    def test_rows_left_over_try_again_in_the_next_round(self):
        edges = [(0, 0, 1), (0, 1, 1), (1, 0, 3)]
        self.assertEqual(mutual_nearest(edges, rounds=1), [(0, 0, 1)])
        self.assertEqual(mutual_nearest(edges, rounds=2), [(0, 0, 1)])  # 1 has only 0, which is taken


class PairTests(unittest.TestCase):
    def pair(self, left, right, **kwargs):
        return go(pair, context(a=left, b=right), source="a", other="b", date="date", amount="amount", **kwargs)

    def test_a_charge_in_both_exports_is_one_paired_record_with_signs_flipped(self):
        found = self.pair([row("2026-03-05", -4.5)], [row("2026-03-05", 4.5)], opposite=True)
        self.assertEqual([(r["match"], r["method"]) for r in found], [("paired", "order")])

    def test_equal_text_pairs_before_file_order(self):
        left = [row("2026-03-05", -4.5, "tea", 1), row("2026-03-05", -4.5, "coffee", 2)]
        right = [row("2026-03-05", 4.5, "COFFEE", 3), row("2026-03-05", 4.5, "tea", 4)]
        found = self.pair(left, right, opposite=True, text="text")
        self.assertEqual([(r["method"], r["source"]["n"], r["other"]["n"]) for r in found],
                         [("exact", 1, 4), ("exact", 2, 3)])

    def test_rows_with_no_partner_stay_single_and_rows_without_a_date_are_invalid(self):
        found = self.pair([row("2026-03-05", -4.5), row(None, -1.0)], [row("2026-04-01", 9.0)], opposite=True)
        self.assertEqual(sorted(r["match"] for r in found), ["invalid_key", "other_only", "source_only"])

    def test_dates_a_business_day_apart_pair_when_the_gap_is_allowed(self):
        friday, monday = row("2026-03-06", -30.0), row("2026-03-09", 30.0)
        self.assertEqual(self.pair([friday], [monday], opposite=True)[0]["match"], "source_only")
        near = self.pair([friday], [monday], opposite=True, within=3)
        self.assertEqual([(r["match"], r["method"]) for r in near], [("paired", "near_date")])

    def test_dates_further_apart_than_allowed_do_not_pair(self):
        found = self.pair([row("2026-03-02", -30.0)], [row("2026-03-09", 30.0)], opposite=True, within=3)
        self.assertEqual(sorted(r["match"] for r in found), ["other_only", "source_only"])


if __name__ == "__main__":
    unittest.main()
