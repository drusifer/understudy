import shutil
import tempfile
import unittest
from pathlib import Path

from src.paths import ROOT
from src.sketch import conditions
from src.sketch.check import check, load_checked
from src.sketch.loader import SketchError, load

FIXTURES = ROOT / "tests" / "fixtures" / "coffee"


class Workspace:
    """A copy of the coffee fixtures that a test can break on purpose."""

    def __init__(self):
        self._directory = tempfile.TemporaryDirectory()
        self.dir = Path(self._directory.name)
        for item in FIXTURES.iterdir():
            if item.is_file():
                shutil.copy(item, self.dir / item.name)
        self.sketch = self.dir / "coffee_week.yaml"

    def edit(self, old: str, new: str, file: str = "coffee_week.yaml") -> "Workspace":
        path = self.dir / file
        text = path.read_text(encoding="utf-8")
        assert old in text, f"{old!r} not in {file}"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return self

    def problems(self) -> list[str]:
        return check(load(self.sketch))

    def close(self):
        self._directory.cleanup()


class CheckTests(unittest.TestCase):
    def workspace(self) -> Workspace:
        space = Workspace()
        self.addCleanup(space.close)
        return space

    def assert_problem(self, problems, *fragments):
        joined = "\n".join(problems)
        for fragment in fragments:
            self.assertIn(fragment, joined)

    def test_the_coffee_sketch_and_its_subsketch_are_clean(self):
        self.assertEqual(check(load(FIXTURES / "coffee_week.yaml")), [])
        self.assertEqual(check(load(FIXTURES / "weather_change.yaml")), [])

    def test_an_unknown_stage_names_the_path_and_the_nearest_stage(self):
        problems = self.workspace().edit("action: split_by_share", "action: split_by_shar").problems()
        self.assert_problem(problems, "machine.states.split_trade.do.etl.action", "etl.split_by_shar", "etl.split_by_share")

    def test_a_leaf_option_that_is_not_declared_names_its_row(self):
        problems = self.workspace().edit("size: large,  weight: 0.5", "size: larg,  weight: 0.5").problems()
        self.assert_problem(problems, "machine.states.match_orders.blend[0].decide.then.drink[0].size", "'larg'", "'large'")

    def test_leaf_weights_must_add_up_to_one(self):
        problems = self.workspace().edit("weight: 0.5 }", "weight: 0.9 }").problems()
        self.assert_problem(problems, "drink", "add up to 1.4, not 1")

    def test_segment_shares_must_add_up_to_one(self):
        problems = self.workspace().edit("share: 0.30", "share: 0.40").problems()
        self.assert_problem(problems, "data.segments", "add up to 1.1, not 1")

    def test_a_missing_source_file_is_refused(self):
        space = self.workspace()
        (space.dir / "last_week_sales.jsonl").unlink()
        self.assert_problem(space.problems(), "sources.sales", "does not exist")

    def test_an_unknown_operator_suggests_the_nearest(self):
        problems = self.workspace().edit("segment: { eq: students }", "segment: { eqq: students }").problems()
        self.assert_problem(problems, "unknown operator 'eqq'", "did you mean 'eq'")

    def test_an_unknown_sink_is_refused(self):
        problems = self.workspace().edit("do: { sink: { name: ingredients } }", "do: { sink: { name: ingredientz } }").problems()
        self.assert_problem(problems, "machine.states.write.do", "ingredientz", "ingredients")

    def test_a_machine_that_never_ends_is_refused(self):
        problems = self.workspace().edit("    done:\n      final: true\n", "    done:\n      then: weather\n").problems()
        self.assert_problem(problems, "no state is final")

    def test_a_decider_that_is_not_a_sketch_state_is_refused(self):
        problems = self.workspace().edit("from: weather", "from: write").problems()
        self.assert_problem(problems, "blend[1].from", "not a state that calls a sketch")

    def test_a_subsketch_that_returns_an_undeclared_outcome_is_refused(self):
        problems = self.workspace().edit("  temp: [hot, iced]\n", "").problems()
        self.assert_problem(problems, "outputs 'temp'", "not a declared outcome")

    def test_a_forbid_that_drops_an_unknown_option_is_refused(self):
        problems = self.workspace().edit("caffeine: { ne: none }", "caffeine: { ne: nonee }").problems()
        self.assert_problem(problems, "forbid[0].drop.caffeine.ne", "'nonee'", "'none'")

    def test_a_jev_source_must_read_other_sources(self):
        problems = self.workspace().edit("{ from: last_week }", "{ from: last_wek }", "weather_change.yaml").problems()
        self.assert_problem(problems, "state.last_week.from", "'last_wek'")

    def test_a_call_to_a_missing_subsketch_is_refused(self):
        space = self.workspace()
        (space.dir / "weather_change.yaml").unlink()
        self.assert_problem(space.problems(), "machine.states.weather.do", "no sketch file")


class ShapeTests(unittest.TestCase):
    def test_a_sketch_without_a_machine_is_refused_with_the_file_and_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yaml"
            path.write_text("name: bad\n", encoding="utf-8")
            with self.assertRaises(SketchError) as caught:
                load(path)
            self.assertIn(f"{path}: (top): 'machine' is a required property", str(caught.exception))

    def test_invalid_yaml_is_refused_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yaml"
            path.write_text("name: [unclosed\n", encoding="utf-8")
            with self.assertRaises(SketchError) as caught:
                load(path)
            self.assertIn("is not valid YAML", str(caught.exception))

    def test_a_source_override_replaces_the_file_for_one_load(self):
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory) / "other.jsonl"
            other.write_text('{"drinks": 5}\n', encoding="utf-8")
            sketch = load_checked(FIXTURES / "coffee_week.yaml", {"sales": str(other)})
            self.assertEqual(sketch.sources["sales"].path, other)
        self.assertEqual(load(FIXTURES / "coffee_week.yaml").sources["sales"].path.name, "last_week_sales.jsonl")

    def test_an_override_for_an_undeclared_source_is_refused(self):
        with self.assertRaises(SketchError) as caught:
            load(FIXTURES / "coffee_week.yaml", {"salez": "x.jsonl"})
        self.assertIn("--source names salez", str(caught.exception))


class SliceTests(unittest.TestCase):
    def test_a_slice_stays_text_and_is_a_valid_operand(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "s.yaml"
            path.write_text(
                "name: s\ndata: { band: 70:30 }\nmachine:\n  initial: a\n  states:\n    a: { final: true }\n", encoding="utf-8")
            self.assertEqual(load(path).data["band"], "70:30")
        self.assertEqual(conditions.problems({"temp": {"in": ["80:90"]}}, "if"), [])
        self.assertEqual(conditions.problems({"temp": {"in": ["70:30"]}}, "if"), [])

    def test_a_list_of_values_and_the_other_operators_are_checked(self):
        self.assertEqual(conditions.problems({"job": {"in": ["nurse", "driver"]}}, "if"), [])
        self.assertEqual(conditions.problems({"merchant": {"has": "coffee"}}, "if"), [])
        self.assertEqual(conditions.problems({"or": [{"a": {"eq": 1}}, {"not": {"b": {"gt": 2}}}]}, "if"), [])
        self.assertEqual(conditions.problems({"a": {"eq": 1}, "b": {"lt": 2}}, "if"), [])

    def test_bad_conditions_say_what_is_wrong(self):
        for bad, fragment in (
            ({"age": {"lt": "young"}}, "needs a number"),
            ({"age": {"lt": 1, "gt": 0}}, "exactly one operator"),
            ({"temp": {"in": []}}, "list of values or a slice"),
            ({"temp": {"in": ["80:90", "x"]}}, "not both"),
            ({"and": []}, "needs a list"),
            ("segment = students", "is a mapping"),
        ):
            with self.subTest(bad=bad):
                self.assertTrue(any(fragment in message for _, message in conditions.problems(bad, "if")), bad)


if __name__ == "__main__":
    unittest.main()
