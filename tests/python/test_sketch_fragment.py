"""UND-102: compute one stage of a sketch from written rows, without the machine, sinks or a run folder."""

import asyncio
import tempfile
import unittest
from pathlib import Path

import src.play.stages  # noqa: F401 - importing it registers the stages
from src.jev import Chosen, JevError
from src.play.fragment import Fragment, read_stage
from src.play.loader import load

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


JEV_SKETCH = """\
name: j
sources:
  pick:
    kind: jev
    question: choice
    instructions: Choose one.
    criteria: { a: first, b: second }
    state: {}
machine: { initial: x, states: { x: { final: true } } }
"""


class FragmentCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        (self.dir / "sketch.yaml").write_text(SKETCH, encoding="utf-8")
        self.sketch = load(self.dir / "sketch.yaml")

    def write_jev_sketch(self):
        (self.dir / "jev.yaml").write_text(JEV_SKETCH, encoding="utf-8")


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

    def test_what_a_source_announces_is_handed_to_the_test(self):
        said: list[str] = []
        sketch = load(self.dir / "sketch.yaml", variables={})
        (self.dir / "optional.yaml").write_text(
            "name: o\nsources:\n  extra:\n    kind: file\n    path: nothing.jsonl\n    optional: pinned\n"
            "machine: { initial: x, states: { x: { final: true } } }\n", encoding="utf-8")
        optional = load(self.dir / "optional.yaml", variables={})
        self.assertEqual(run(read_stage(optional, "extra", announce=said.append)), [])
        self.assertTrue(said and "so none are used" in said[0])
        self.assertTrue(sketch)

    def test_a_jev_source_is_answered_by_the_jev_given(self):
        self.write_jev_sketch()
        asked = []

        class Jev:
            async def choose(self, *, state, instructions, options):
                asked.append(list(options))
                return Chosen("b", 0.9, {"a": 0.1, "b": 0.9})

        rows = run(read_stage(load(self.dir / "jev.yaml"), "pick", jev=Jev()))
        self.assertEqual(asked, [["a", "b"]])
        self.assertEqual({row["level"]: row["probability"] for row in rows}, {"a": 0.1, "b": 0.9})

    def test_several_reads_in_one_session_share_what_was_computed_and_ask_jev_once(self):
        self.write_jev_sketch()
        asked = []

        class Jev:
            async def choose(self, *, state, instructions, options):
                asked.append(1)
                return Chosen("a", 0.8, {"a": 0.8, "b": 0.2})

        async def twice():
            with Fragment(load(self.dir / "jev.yaml"), jev=Jev()) as fragment:
                return await fragment.read("pick"), await fragment.read("pick")

        first, second = run(twice())
        self.assertEqual((len(asked), first), (1, second))

    def test_a_session_that_reads_a_name_the_sketch_lacks_says_so(self):
        with Fragment(self.sketch) as fragment, self.assertRaises(KeyError):
            run(fragment.read("nobody"))

    def test_a_jev_source_with_no_jev_says_so_and_asks_nothing(self):
        self.write_jev_sketch()
        with self.assertRaises(JevError):
            run(read_stage(load(self.dir / "jev.yaml"), "pick"))

    def test_nothing_is_written_beside_the_sketch(self):
        run(read_stage(self.sketch, "named", stubs={"people": PEOPLE}))
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["sketch.yaml"])

    def test_two_reads_do_not_share_results(self):
        run(read_stage(self.sketch, "adults", stubs={"people": PEOPLE}))
        again = run(read_stage(self.sketch, "adults", stubs={"people": [{"name": "Ed", "age": 50, "team": "z"}]}))
        self.assertEqual([r["name"] for r in again], ["Ed"])
