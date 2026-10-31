import asyncio
import unittest
from types import SimpleNamespace

from src.sketch.stages_pair import convert, link, mutual_nearest, pair


def context(**sources):
    async def read(name):
        return sources[name]

    return SimpleNamespace(read=read)


def go(stage, ctx, **kwargs):
    return asyncio.run(stage(ctx, **kwargs))


def row(date, amount, text="", n=0, account="card"):
    return {"date": date, "amount": amount, "text": text, "n": n, "account": account}


class ConvertTests(unittest.TestCase):
    def test_dates_and_amounts_are_added_beside_the_text(self):
        rows = [{"Date": "03/05/2026", "Amount": "(4.50)"}, {"Date": "", "Amount": "x"}]
        found = go(convert, context(raw=rows), source="raw", dates={"Date": "date"}, amounts={"Amount": "amount"})
        self.assertEqual(found, [{"Date": "03/05/2026", "Amount": "(4.50)", "date": "2026-03-05", "amount": -4.5},
                                 {"Date": "", "Amount": "x", "date": None, "amount": None}])

    def test_negate_flips_the_sign_of_the_amounts(self):
        found = go(convert, context(raw=[{"Amount": "4.50"}]), source="raw", amounts={"Amount": "amount"}, negate=True)
        self.assertEqual(found[0]["amount"], -4.5)


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

    def test_a_charge_in_both_exports_is_one_flat_record_with_both_rows_fields(self):
        found = self.pair([row("2026-03-05", -4.5, n=1)], [row("2026-03-05", -4.5, n=2)])
        self.assertEqual([(r["match"], r["method"], r["n"], r["other_n"]) for r in found], [("paired", "order", 1, 2)])

    def test_equal_text_pairs_before_file_order(self):
        left = [row("2026-03-05", -4.5, "tea", 1), row("2026-03-05", -4.5, "coffee", 2)]
        right = [row("2026-03-05", -4.5, "COFFEE", 3), row("2026-03-05", -4.5, "tea", 4)]
        found = self.pair(left, right, text="text")
        self.assertEqual([(r["method"], r["n"], r["other_n"]) for r in found], [("exact", 1, 4), ("exact", 2, 3)])

    def test_rows_with_no_partner_stay_single_and_rows_without_a_date_are_invalid(self):
        found = self.pair([row("2026-03-05", -4.5), row(None, -1.0)], [row("2026-04-01", -9.0)])
        self.assertEqual(sorted(r["match"] for r in found), ["invalid_key", "other_only", "source_only"])

    def test_only_the_rows_that_satisfy_only_are_paired(self):
        left = [row("2026-03-05", -4.5, n=1, account="card"), row("2026-03-05", -4.5, n=2, account="checking")]
        found = self.pair(left, [row("2026-03-05", -4.5, n=3)], only={"account": {"eq": "checking"}})
        self.assertEqual({(r["match"], r["n"]) for r in found if "n" in r}, {("paired", 2), ("source_only", 1)})

    def test_dates_a_business_day_apart_pair_when_the_gap_is_allowed(self):
        friday, monday = row("2026-03-06", -30.0), row("2026-03-09", -30.0)
        self.assertEqual(self.pair([friday], [monday])[0]["match"], "source_only")
        near = self.pair([friday], [monday], within=3)
        self.assertEqual([(r["match"], r["method"]) for r in near], [("paired", "near_date")])

    def test_dates_further_apart_than_allowed_do_not_pair(self):
        found = self.pair([row("2026-03-02", -30.0)], [row("2026-03-09", -30.0)], within=3)
        self.assertEqual(sorted(r["match"] for r in found), ["other_only", "source_only"])


def leg(ident, date, amount, account):
    return {"id": ident, "date": date, "amount": amount, "account": account}


class LinkTests(unittest.TestCase):
    def link(self, rows, **kwargs):
        found = go(link, context(rows=rows), source="rows", date="date", amount="amount", apart="account", id="id", **kwargs)
        return {r["id"]: (r["partner"], r["gap"]) for r in found}

    def test_a_card_payment_links_to_the_checking_debit_across_a_weekend(self):
        found = self.link([leg("a1", "2026-03-06", 500.0, "card"), leg("m1", "2026-03-09", -500.0, "checking")])
        self.assertEqual(found, {"a1": ("m1", 1), "m1": ("a1", 1)})

    def test_two_payments_of_one_amount_each_get_their_own_partner(self):
        rows = [leg("a1", "2026-03-02", 100.0, "card"), leg("a2", "2026-03-04", 100.0, "card"),
                leg("m1", "2026-03-02", -100.0, "bank"), leg("m2", "2026-03-04", -100.0, "bank")]
        found = self.link(rows)
        self.assertEqual((found["a1"][0], found["a2"][0]), ("m1", "m2"))

    def test_the_same_account_or_too_far_apart_does_not_link(self):
        rows = [leg("x1", "2026-03-02", 50.0, "card"), leg("x2", "2026-03-02", -50.0, "card"),
                leg("y1", "2026-03-02", 70.0, "card"), leg("y2", "2026-03-20", -70.0, "bank")]
        self.assertEqual(set(self.link(rows).values()), {(None, None)})


if __name__ == "__main__":
    unittest.main()
