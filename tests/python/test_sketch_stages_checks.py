import asyncio
import unittest
from types import SimpleNamespace

from src.sketch.registry import STAGES
from src.sketch.stages_rows import require, tally


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


if __name__ == "__main__":
    unittest.main()
