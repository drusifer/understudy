import asyncio
import unittest
from types import MappingProxyType, SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import (
    allocate,
    complete,
    group,
    keep,
    known,
    note,
    require,
    set_fields,
    share,
    smallest,
    tally,
    top,
    top_two,
    unique,
    without,
)


def context(rows):
    async def read(name):
        return rows

    return SimpleNamespace(read=read, summary={})


def run(stage, ctx, **kwargs):
    return asyncio.run(stage(ctx, **kwargs))


class RequireTests(unittest.TestCase):
    def test_rows_with_every_named_column_pass_through_unchanged(self):
        rows = [{"Category": "Transfer", "Amount": "1"}]
        self.assertEqual(run(require, context(rows), source="rows", columns=["Category"]), rows)

    def test_a_missing_column_stops_the_run_naming_the_source_and_the_column(self):
        with self.assertRaises(ValueError) as stopped:
            run(require, context([{"Amount": "1"}]), source="rows", columns=["Category", "Amount"])
        self.assertEqual(str(stopped.exception), "source 'rows' has no Category column")

    def test_an_empty_source_has_no_columns_to_check(self):
        self.assertEqual(run(require, context([]), source="rows", columns=["Category"]), [])

    def test_it_is_a_map_stage_asking_for_a_source_and_columns(self):
        required = [key for key, p in STAGES["map.require"].params.items() if p.required]
        self.assertEqual(required, ["source", "columns"])


class TallyTests(unittest.TestCase):
    def test_the_count_of_each_value_goes_into_the_summary_and_the_rows_pass_through(self):
        rows = [{"kind": "transfer"}, {"kind": "purchase"}, {"kind": "transfer"}]
        ctx = context(rows)
        self.assertEqual(run(tally, ctx, source="rows", by="kind", into="kinds"), rows)
        self.assertEqual(ctx.summary, {"kinds": {"purchase": 1, "transfer": 2}})

    def test_it_is_a_reduce_stage_asking_for_a_source_a_field_and_a_summary_key(self):
        required = [key for key, p in STAGES["reduce.tally"].params.items() if p.required]
        self.assertEqual(required, ["source", "by", "into"])


class GroupSumsTests(unittest.TestCase):
    ROWS = ({"card": "Checking", "cost": 100.0}, {"card": "checking ", "cost": -30.5},
            {"card": "Checking", "cost": -4.25}, {"card": "Card", "cost": -9.99})
    SUMS = MappingProxyType({"income": {"field": "cost", "where": {"cost": {"gt": 0}}},
                             "expenses": {"field": "cost", "where": {"cost": {"lt": 0}}}, "net": "cost"})

    def test_each_group_gets_its_sums_rounded_to_cents_and_a_sum_can_be_limited_by_a_condition(self):
        found = run(group, context(list(self.ROWS)), source="rows", by="card", sums=dict(self.SUMS))
        self.assertEqual([(r["card"], r["count"], r["income"], r["expenses"], r["net"]) for r in found],
                         [("Checking", 3, 100.0, -34.75, 65.25), ("Card", 1, 0.0, -9.99, -9.99)])
        self.assertIsInstance(found[1]["income"], float)  # 0.0, never the integer 0

    def test_a_group_with_no_matching_rows_sums_to_zero_and_nothing_is_made_for_a_missing_group(self):
        found = run(group, context([]), source="rows", by="card", sums=self.SUMS)
        self.assertEqual(found, [])

    def test_commonest_names_the_value_most_rows_of_the_group_have_the_first_seen_winning_a_tie(self):
        rows = [{"p": "A", "c": "x"}, {"p": "A", "c": "y"}, {"p": "A", "c": "y"}, {"p": "B", "c": "z"}, {"p": "B", "c": "w"},
                {"p": "C"}, {"p": "C", "c": ""}]
        found = run(group, context(rows), source="rows", by="p", commonest={"top_c": "c"})
        self.assertEqual({r["p"]: r["top_c"] for r in found}, {"A": "y", "B": "z", "C": None})

    def test_group_without_sums_is_unchanged(self):
        (row,) = run(group, context([{"card": "A", "cost": 1.0}]), source="rows", by="card")
        self.assertEqual(row, {"key": "a", "card": "A", "count": 1})


class TopTwoTests(unittest.TestCase):
    READINGS = ({"level": "Coffee", "probability": 0.2}, {"level": "Groceries", "probability": 0.6},
                {"level": "none_of_these", "probability": 0.15}, {"level": "Pets", "probability": 0.05})

    def test_one_row_names_the_best_and_the_runner_up_with_their_values(self):
        (row,) = run(top_two, context(list(self.READINGS)), source="rows", label="level", value="probability")
        self.assertEqual(row, {"level": "Groceries", "probability": 0.6, "runner_up": "Coffee",
                               "runner_up_probability": 0.2})

    def test_with_only_one_row_there_is_no_runner_up(self):
        (row,) = run(top_two, context([{"level": "A", "probability": 1.0}]), source="rows", label="level",
                     value="probability")
        self.assertEqual(row, {"level": "A", "probability": 1.0, "runner_up": None, "runner_up_probability": None})

    def test_no_rows_give_no_row(self):
        self.assertEqual(run(top_two, context([]), source="rows", label="level", value="probability"), [])

    def test_it_is_a_reduce_stage_asking_for_a_source_a_label_and_a_value(self):
        required = [key for key, p in STAGES["reduce.top_two"].params.items() if p.required]
        self.assertEqual(required, ["source", "label", "value"])


class KeepTests(unittest.TestCase):
    def test_each_row_keeps_only_the_named_fields_in_that_order(self):
        rows = [{"b": 2, "a": 1, "c": 3}, {"a": 4, "c": 6}]
        found = run(keep, context(rows), source="rows", fields=["a", "b"])
        self.assertEqual([list(r.items()) for r in found], [[("a", 1), ("b", 2)], [("a", 4), ("b", None)]])


def named(**sources):
    async def read(name):
        return sources[name]

    return SimpleNamespace(read=read, summary={})


class CompleteTests(unittest.TestCase):
    def test_rows_with_a_value_in_every_named_field_pass_through(self):
        rows = [{"payee": "Amazon", "category": "Shopping"}]
        self.assertEqual(run(complete, named(pins=rows), source="pins", fields=["payee", "category"]), rows)

    def test_a_row_missing_a_field_stops_the_run_naming_its_line_and_the_field(self):
        rows = [{"payee": "Amazon", "category": "Shopping"}, {"payee": "  ", "category": "Pets"}]
        with self.assertRaises(ValueError) as stopped:
            run(complete, named(pins=rows), source="pins", fields=["payee", "category"])
        self.assertEqual(str(stopped.exception), "source 'pins' line 2 has no payee")

    def test_a_field_that_is_absent_counts_as_missing(self):
        with self.assertRaises(ValueError) as stopped:
            run(complete, named(pins=[{"payee": "Amazon"}]), source="pins", fields=["payee", "category"])
        self.assertEqual(str(stopped.exception), "source 'pins' line 1 has no category")


class KnownTests(unittest.TestCase):
    IN_USE = ({"Category": "Shopping & Retail: Clothing"}, {"Category": "Taxes"})

    def test_rows_whose_value_is_in_the_other_source_pass_through(self):
        rows = [{"category": "Taxes"}]
        context_ = named(pins=rows, in_use=list(self.IN_USE))
        self.assertEqual(run(known, context_, source="pins", field="category", among="in_use", among_field="Category"), rows)

    def test_an_unknown_value_stops_the_run_naming_the_line_and_the_value(self):
        context_ = named(pins=[{"category": "Taxes"}, {"category": "Fun"}], in_use=list(self.IN_USE))
        with self.assertRaises(ValueError) as stopped:
            run(known, context_, source="pins", field="category", among="in_use", among_field="Category")
        self.assertEqual(str(stopped.exception), "source 'pins' line 2: 'Fun' is not a Category in 'in_use'")


class WithoutTests(unittest.TestCase):
    def test_the_rows_whose_value_is_not_in_the_other_source_are_kept(self):
        rows = [{"key": "a"}, {"key": "b"}, {"key": "c"}]
        found = run(without, named(rows=rows, pins=[{"key": "b"}]), source="rows", among="pins", on="key")
        self.assertEqual(found, [{"key": "a"}, {"key": "c"}])

    def test_the_other_sources_field_may_have_another_name(self):
        found = run(without, named(rows=[{"key": "a"}, {"key": "b"}], pins=[{"merchant": "a"}]), source="rows",
                    among="pins", on="key", among_on="merchant")
        self.assertEqual(found, [{"key": "b"}])


class SetTests(unittest.TestCase):
    def test_every_row_gets_the_named_fields(self):
        found = run(set_fields, context([{"a": 1}, {"a": 2}]), source="rows", fields={"status": "placed", "probability": 1.0})
        self.assertEqual(found, [{"a": 1, "status": "placed", "probability": 1.0},
                                 {"a": 2, "status": "placed", "probability": 1.0}])


class UniqueTests(unittest.TestCase):
    def test_rows_that_do_not_repeat_pass_through_unchanged(self):
        rows = [{"name": "Rent"}, {"name": "Mortgage"}]
        self.assertEqual(run(unique, named(rows=rows), source="rows", field="name"), rows)

    def test_a_repeat_stops_the_run_naming_the_line_and_the_first_line_it_repeats(self):
        rows = [{"name": "Rent"}, {"name": "Mortgage"}, {"name": "rent  "}]  # case, spacing and edges do not make it new
        with self.assertRaises(ValueError) as stopped:
            run(unique, named(rows=rows), source="rows", field="name")
        self.assertEqual(str(stopped.exception), "source 'rows' line 3 repeats 'rent  ' (first on line 1)")

    def test_a_row_that_repeats_a_value_in_another_source_is_named_with_that_source(self):
        context_ = named(rows=[{"name": "Rent"}, {"name": "Taxi-cabs"}], iso=[{"name": "Taxi-cabs"}])
        with self.assertRaises(ValueError) as stopped:
            run(unique, context_, source="rows", field="name", among="iso")
        self.assertEqual(str(stopped.exception), "source 'rows' line 2 repeats 'Taxi-cabs' (also in 'iso')")

    def test_it_is_a_map_stage_asking_for_a_source_and_a_field(self):
        required = [key for key, p in STAGES["map.unique"].params.items() if p.required]
        self.assertEqual(required, ["source", "field"])


class ClassifyScalarTests(unittest.TestCase):
    def test_then_and_otherwise_may_be_numbers_or_booleans_as_well_as_text(self):
        from src.sketch.stages_rows import classify
        rows = [{"n": 5}, {"n": 1}]
        found = run(classify, context(rows), source="rows", into="big", cases=[{"if": {"n": {"gt": 3}}, "then": True}],
                    otherwise=False)
        self.assertEqual([r["big"] for r in found], [True, False])
        found = run(classify, context(rows), source="rows", into="flag", cases=[{"if": {"n": {"gt": 3}}, "then": 1}], otherwise=0)
        self.assertEqual([r["flag"] for r in found], [1, 0])
        self.assertIn("otherwise", STAGES["map.classify"].params)


class WeighMissingTests(unittest.TestCase):
    def test_a_field_a_row_lacks_or_has_as_null_counts_as_zero(self):
        from src.sketch.stages_rows import weigh
        rows = [{"p": 0.6, "q": 0.2}, {"p": 0.6, "q": None}, {"p": 0.6}]
        found = run(weigh, context(rows), source="rows", by={"p": 1, "q": -2}, into="lead")
        self.assertEqual([round(r["lead"], 2) for r in found], [0.2, 0.6, 0.6])


class SmallestTests(unittest.TestCase):
    def test_each_row_gets_the_smallest_of_the_named_fields(self):
        rows = [{"a": 0.9, "b": 0.5}, {"a": 0.3, "b": 0.8}]
        found = run(smallest, context(rows), source="rows", fields=["a", "b"], into="least")
        self.assertEqual([r["least"] for r in found], [0.5, 0.3])
        self.assertEqual(found[0]["a"], 0.9)  # the rows keep their fields

    def test_a_field_the_row_lacks_is_left_out_and_a_row_with_none_gets_null(self):
        found = run(smallest, context([{"a": 0.4}, {"c": 1}]), source="rows", fields=["a", "b"], into="least")
        self.assertEqual([r["least"] for r in found], [0.4, None])

    def test_it_is_a_map_stage_asking_for_a_source_fields_and_a_name(self):
        required = [key for key, p in STAGES["map.smallest"].params.items() if p.required]
        self.assertEqual(required, ["source", "fields", "into"])


class ShareTests(unittest.TestCase):
    def test_each_row_gets_its_share_of_the_fields_total(self):
        found = run(share, context([{"a": 1.0}, {"a": 3.0}]), source="rows", field="a", into="share")
        self.assertEqual([r["share"] for r in found], [0.25, 0.75])

    def test_shares_are_rounded_to_four_places_and_the_rows_keep_their_fields(self):
        found = run(share, context([{"a": 1.0, "n": "x"}, {"a": 2.0, "n": "y"}]), source="rows", field="a", into="share")
        self.assertEqual(found, [{"a": 1.0, "n": "x", "share": 0.3333}, {"a": 2.0, "n": "y", "share": 0.6667}])

    def test_a_total_of_zero_gives_every_row_a_share_of_zero(self):
        found = run(share, context([{"a": 0.0}, {"a": 0.0}]), source="rows", field="a", into="share")
        self.assertEqual([r["share"] for r in found], [0.0, 0.0])

    def test_it_is_a_map_stage_asking_for_a_source_a_field_and_a_name(self):
        required = [key for key, p in STAGES["map.share"].params.items() if p.required]
        self.assertEqual(required, ["source", "field", "into"])


class NoteTests(unittest.TestCase):
    def test_the_first_row_goes_into_the_summary_without_its_grouping_key_and_the_rows_pass_through(self):
        rows = [{"key": "all", "scope": "all", "count": 5, "net": -4.5}]
        ctx = context(rows)
        self.assertEqual(run(note, ctx, source="rows", into="net_spending"), rows)
        self.assertEqual(ctx.summary, {"net_spending": {"scope": "all", "count": 5, "net": -4.5}})

    def test_a_source_with_no_rows_leaves_the_summary_alone(self):
        ctx = context([])
        run(note, ctx, source="rows", into="net_spending")
        self.assertEqual(ctx.summary, {})


if __name__ == "__main__":
    unittest.main()


def sources(**named):
    async def read(name):
        return named[name]

    return SimpleNamespace(read=read, summary={})


def charge(day, amount, name="c"):
    return {"day": day, "amount": amount, "name": name}


ALLOC = {"source": "charges", "payments": "payments", "amount": "amount", "day": "day", "id": "payment_id", "into": "settled_by"}


class AllocateTests(unittest.TestCase):
    def settle(self, charges, payments):
        found = run(allocate, sources(charges=charges, payments=payments), **ALLOC)
        return [row["settled_by"] for row in found]

    def test_a_payment_settles_the_oldest_charges_first_and_the_rest_stay_open(self):
        charges = [charge("2025-01-03", 30.0), charge("2025-01-01", 10.0), charge("2025-01-02", 20.0)]
        payments = [{"payment_id": "p1", "day": "2025-01-05", "amount": 30.0}]
        self.assertEqual(self.settle(charges, payments), [None, "p1", "p1"])

    def test_it_stops_before_the_amount_would_be_passed(self):
        charges = [charge("2025-01-01", 10.0), charge("2025-01-02", 25.0), charge("2025-01-03", 5.0)]
        payments = [{"payment_id": "p1", "day": "2025-01-05", "amount": 20.0}]
        self.assertEqual(self.settle(charges, payments), ["p1", None, None])

    def test_a_charge_dated_after_the_payment_is_never_used(self):
        charges = [charge("2025-01-06", 10.0), charge("2025-01-05", 10.0)]
        payments = [{"payment_id": "p1", "day": "2025-01-05", "amount": 100.0}]
        self.assertEqual(self.settle(charges, payments), [None, "p1"])

    def test_a_charge_belongs_to_at_most_one_payment(self):
        charges = [charge("2025-01-01", 10.0), charge("2025-01-02", 10.0), charge("2025-01-03", 10.0)]
        payments = [{"payment_id": "p2", "day": "2025-01-10", "amount": 10.0},
                    {"payment_id": "p1", "day": "2025-01-04", "amount": 20.0}]
        self.assertEqual(self.settle(charges, payments), ["p1", "p1", "p2"])

    def test_a_payment_before_any_charge_settles_nothing(self):
        charges = [charge("2025-02-01", 10.0)]
        payments = [{"payment_id": "p1", "day": "2025-01-01", "amount": 50.0}]
        self.assertEqual(self.settle(charges, payments), [None])

    def test_no_payments_leave_every_charge_open_and_the_rows_keep_their_order_and_fields(self):
        charges = [charge("2025-01-02", 1.0, "b"), charge("2025-01-01", 2.0, "a")]
        found = run(allocate, sources(charges=charges, payments=[]), **ALLOC)
        self.assertEqual([(r["name"], r["settled_by"]) for r in found], [("b", None), ("a", None)])

    def test_sums_are_exact_to_the_cent(self):
        charges = [charge("2025-01-01", 0.1), charge("2025-01-02", 0.2)]
        payments = [{"payment_id": "p1", "day": "2025-01-03", "amount": 0.3}]
        self.assertEqual(self.settle(charges, payments), ["p1", "p1"])

    def test_it_is_a_map_stage_asking_for_the_two_sources_the_fields_and_a_name(self):
        required = [key for key, p in STAGES["map.allocate"].params.items() if p.required]
        self.assertEqual(required, ["source", "payments", "amount", "day", "id", "into"])


class TopTests(unittest.TestCase):
    def test_the_largest_rows_of_each_group_stay_largest_first_in_the_order_groups_first_appear(self):
        rows = [{"g": "a", "v": 1}, {"g": "b", "v": 9}, {"g": "a", "v": 5}, {"g": "a", "v": 3}, {"g": "b", "v": 2}]
        found = run(top, context(rows), source="rows", by="g", field="v", take=2)
        self.assertEqual([(r["g"], r["v"]) for r in found], [("a", 5), ("a", 3), ("b", 9), ("b", 2)])

    def test_take_defaults_to_five_and_a_small_group_keeps_all_its_rows(self):
        rows = [{"g": "a", "v": n} for n in range(7)] + [{"g": "b", "v": 1}]
        found = run(top, context(rows), source="rows", by="g", field="v")
        self.assertEqual([r["v"] for r in found if r["g"] == "a"], [6, 5, 4, 3, 2])
        self.assertEqual(len([r for r in found if r["g"] == "b"]), 1)

    def test_it_is_a_map_stage_asking_for_a_source_a_group_field_and_a_value_field(self):
        required = [key for key, p in STAGES["map.top"].params.items() if p.required]
        self.assertEqual(required, ["source", "by", "field"])
