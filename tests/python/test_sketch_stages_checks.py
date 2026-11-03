import asyncio
import unittest
from types import MappingProxyType, SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import (
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
