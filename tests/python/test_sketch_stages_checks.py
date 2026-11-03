import asyncio
import unittest
from types import MappingProxyType, SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import group, keep, note, require, tally, top_two


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
