"""UND-102: compute one stage of a sketch from written rows, without the machine, sinks or a run folder."""

import asyncio
import tempfile
import unittest
from pathlib import Path

import src.sketch.stages  # noqa: F401 - importing it registers the stages
from src.sketch.fragment import read_stage
from src.sketch.loader import load

SKETCH = """\
name: fragments
sources:
  people: people.jsonl
  adults:
    kind: stage
    do: { map: { action: where } }
    with: { source: people, keep: { age: { ge: 18 } } }
  named:
    kind: stage
    do: { map: { action: format } }
    with: { source: adults, template: "{name} ({age})", into: label }
  counted:
    kind: stage
    do: { reduce: { action: tally } }
    with: { source: people, by: team, into: per_team }
sinks:
  out: out.jsonl
machine:
  initial: only
  states:
    only: { do: { sink: { name: out } }, with: { source: named }, then: done }
    done: { final: true }
"""
PEOPLE = [{"name": "Ann", "age": 30, "team": "a"}, {"name": "Bo", "age": 12, "team": "a"}, {"name": "Cy", "age": 18, "team": "b"}]


def run(coroutine):
    return asyncio.run(coroutine)


class FragmentCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        (self.dir / "sketch.yaml").write_text(SKETCH, encoding="utf-8")
        self.sketch = load(self.dir / "sketch.yaml")


class ReadStageTests(FragmentCase):
    def test_a_stage_is_computed_from_rows_written_for_its_file_source_and_no_file_is_read(self):
        self.assertFalse((self.dir / "people.jsonl").exists())
        rows = run(read_stage(self.sketch, "adults", stubs={"people": PEOPLE}))
        self.assertEqual([r["name"] for r in rows], ["Ann", "Cy"])

    def test_a_stage_that_reads_another_stage_gets_that_stages_result(self):
        rows = run(read_stage(self.sketch, "named", stubs={"people": PEOPLE}))
        self.assertEqual([r["label"] for r in rows], ["Ann (30)", "Cy (18)"])

    def test_a_stage_can_be_stood_in_for_so_the_ones_behind_it_are_not_run(self):
        rows = run(read_stage(self.sketch, "named", stubs={"adults": [{"name": "Zed", "age": 99}]}))
        self.assertEqual([r["label"] for r in rows], ["Zed (99)"])  # `people` was never needed, so it needs no stub

    def test_what_a_stage_notes_in_the_summary_is_handed_back_to_the_test(self):
        summary: dict = {}
        run(read_stage(self.sketch, "counted", stubs={"people": PEOPLE}, summary=summary))
        self.assertEqual(summary, {"per_team": {"a": 2, "b": 1}})

    def test_a_file_source_with_no_stub_is_read_from_its_file_as_a_run_would(self):
        (self.dir / "people.jsonl").write_text('{"name": "Di", "age": 40, "team": "c"}\n', encoding="utf-8")
        self.assertEqual([r["name"] for r in run(read_stage(self.sketch, "adults"))], ["Di"])

    def test_a_source_that_is_not_in_the_sketch_is_refused_by_name(self):
        with self.assertRaises(KeyError):
            run(read_stage(self.sketch, "nobody", stubs={"people": PEOPLE}))

    def test_a_stub_for_a_source_that_is_not_in_the_sketch_is_refused_by_name(self):
        with self.assertRaises(KeyError):
            run(read_stage(self.sketch, "adults", stubs={"people": PEOPLE, "ghosts": []}))

    def test_nothing_is_written_beside_the_sketch(self):
        run(read_stage(self.sketch, "named", stubs={"people": PEOPLE}))
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["sketch.yaml"])

    def test_two_reads_do_not_share_results(self):
        run(read_stage(self.sketch, "adults", stubs={"people": PEOPLE}))
        again = run(read_stage(self.sketch, "adults", stubs={"people": [{"name": "Ed", "age": 50, "team": "z"}]}))
        self.assertEqual([r["name"] for r in again], ["Ed"])
