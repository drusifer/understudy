import shutil
import tempfile
import unittest
from pathlib import Path

from src.paths import ROOT
from src.play import conditions
from src.play.check import check, load_checked
from src.play.loader import PlayError, load

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
        self.assert_problem(problems, "scene.beats.split_trade.do.map.action", "map.split_by_shar", "map.split_by_share")

    def test_a_leaf_option_that_is_not_declared_names_its_row(self):
        problems = self.workspace().edit("size: large,  weight: 0.5", "size: larg,  weight: 0.5").problems()
        self.assert_problem(problems, "scene.beats.match_orders.with.entries[0].decide.then.drink[0].size", "'larg'", "'large'")

    def test_leaf_weights_must_add_up_to_one(self):
        problems = self.workspace().edit("weight: 0.5 }", "weight: 0.9 }").problems()
        self.assert_problem(problems, "drink", "add up to 1.4, not 1")

    def test_segment_shares_must_add_up_to_one(self):
        problems = self.workspace().edit("share: 0.30", "share: 0.40").problems()
        self.assert_problem(problems, "data.segments", "add up to 1.1, not 1")

    def test_a_missing_source_file_is_refused(self):
        space = self.workspace()
        (space.dir / "last_week_sales.jsonl").unlink()
        self.assert_problem(space.problems(), "stage.sales", "does not exist")

    def test_an_unknown_operator_suggests_the_nearest(self):
        problems = self.workspace().edit("segment: { eq: students }", "segment: { eqq: students }").problems()
        self.assert_problem(problems, "unknown operator 'eqq'", "did you mean 'eq'")

    def test_a_write_to_a_file_the_stage_does_not_write_is_refused(self):
        problems = self.workspace().edit("do: { write: ingredients }", "do: { write: ingredientz }").problems()
        self.assert_problem(problems, "scene.beats.write.do.write", "'ingredientz' is not a file the stage writes",
                            "'ingredients'")

    def test_a_write_to_a_file_the_play_reads_is_refused(self):
        problems = self.workspace().edit("do: { write: ingredients }", "do: { write: sales }").problems()
        self.assert_problem(problems, "scene.beats.write.do.write", "'sales' is not a file the stage writes")

    def test_a_beat_that_reads_a_written_file_is_refused(self):
        problems = self.workspace().edit("with: { from: sales,", "with: { from: ingredients,").problems()
        self.assert_problem(problems, "scene.beats.split_trade.with.from",
                            "'ingredients' is a file the play writes (`access: write`); no beat reads it")

    def test_a_beat_that_reads_a_beat_in_the_flow_is_refused(self):
        problems = self.workspace().edit("with: { from: sales,", "with: { from: to_ingredients,").problems()
        self.assert_problem(problems, "scene.beats.split_trade.with.from", "'to_ingredients' is a beat in the scene's flow")

    def test_two_beats_writing_one_file_are_refused(self):
        twice = "      do: { write: ingredients }\n      to: again\n    again:\n      do: { write: ingredients }\n      to: done\n"
        problems = self.workspace().edit("      do: { write: ingredients }\n      to: done\n", twice).problems()
        self.assert_problem(problems, "scene.beats.again.do.write", "'ingredients' is already written by beat 'write'")

    def test_a_scene_that_never_ends_is_refused(self):
        problems = self.workspace().edit("    done:\n      final: true\n", "    done:\n      to: weather\n").problems()
        self.assert_problem(problems, "no beat is final")

    def test_a_decider_that_is_not_a_beat_performing_a_play_is_refused(self):
        problems = self.workspace().edit("from: weather", "from: write").problems()
        self.assert_problem(problems, "entries[1].from", "not a beat that performs a play")

    def test_a_subsketch_that_returns_an_undeclared_outcome_is_refused(self):
        problems = self.workspace().edit("  temp: [hot, iced]\n", "").problems()
        self.assert_problem(problems, "outputs 'temp'", "not a declared outcome")

    def test_a_forbid_that_drops_an_unknown_option_is_refused(self):
        problems = self.workspace().edit("caffeine: { ne: none }", "caffeine: { ne: nonee }").problems()
        self.assert_problem(problems, "forbid[0].drop.caffeine.ne", "'nonee'", "'none'")

    def test_a_jev_beat_must_read_other_pieces(self):
        problems = self.workspace().edit("{ from: last_week }", "{ from: last_wek }", "weather_change.yaml").problems()
        self.assert_problem(problems, "scene.beats.weather_change.with.state.last_week.from", "'last_wek'")

    def test_a_call_to_a_missing_play_is_refused(self):
        space = self.workspace()
        (space.dir / "weather_change.yaml").unlink()
        self.assert_problem(space.problems(), "scene.beats.weather.do.play", "no play file weather_change.yaml")


class ShapeTests(unittest.TestCase):
    def load_text(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yaml"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(PlayError) as caught:
                load(path)
            return path, str(caught.exception)

    def test_a_play_without_a_scene_is_refused_with_the_file_and_path(self):
        path, said = self.load_text("name: bad\n")
        self.assertIn(f"{path}: (top): 'scene' is a required property", said)

    def test_every_old_key_is_refused_as_an_unknown_key(self):
        """No back-compat: a file written before plays is refused like any typo (UND-105 AC2)."""
        for old in ("sources: {}", "sinks: {}", "inputs: {}", "machine: { initial: a, states: { a: { final: true } } }"):
            with self.subTest(old=old):
                _, said = self.load_text(f"name: old\n{old}\nscene: {{ initial: a, beats: {{ a: {{ final: true }} }} }}\n")
                self.assertIn(f"'{old.split(':')[0]}' was unexpected", said)
        for beat, word in (("{ do: { map: { action: x } }, then: a }", "then"), ("{ final: true, states: {} }", "states")):
            with self.subTest(beat=beat):
                _, said = self.load_text(f"name: old\nscene: {{ initial: a, beats: {{ a: {{ final: true }}, b: {beat} }} }}\n")
                self.assertIn(f"'{word}' was unexpected", said)
        for do in ("{ sketch: { file: x } }", "{ sink: { name: x } }"):
            with self.subTest(do=do):
                _, said = self.load_text(f"name: old\nscene: {{ initial: a, beats: {{ a: {{ do: {do}, to: b }}, "
                                         "b: { final: true } } }\n")
                self.assertIn("scene.beats.a.do", said)
        _, said = self.load_text("name: old\nstage: { x: { kind: stage } }\nscene: { initial: a, beats: { a: { final: true } } }\n")
        self.assertIn("prop 'x': unknown kind 'stage'", said)

    def test_a_name_on_the_stage_and_in_the_scene_is_refused(self):
        _, said = self.load_text("name: twice\nstage: { a: { kind: file, path: a.jsonl } }\n"
                                 "scene: { initial: a, beats: { a: { final: true } } }\n")
        self.assertIn("scene.beats.a: 'a' is also on the stage", said)

    def test_a_jev_beat_in_the_flow_is_refused(self):
        _, said = self.load_text("name: ask\nscene:\n  initial: a\n  beats:\n"
                                 "    a: { do: { jev: { question: choice } },\n"
                                 "         with: { instructions: x, criteria: { y: y, n: n }, state: {} }, to: b }\n"
                                 "    b: { final: true }\n")
        self.assertIn("scene.beats.a: a Jev beat is performed when another beat reads it", said)

    def test_invalid_yaml_is_refused_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yaml"
            path.write_text("name: [unclosed\n", encoding="utf-8")
            with self.assertRaises(PlayError) as caught:
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
        with self.assertRaises(PlayError) as caught:
            load(FIXTURES / "coffee_week.yaml", {"salez": "x.jsonl"})
        self.assertIn("--source names salez, which is not a file on the play's stage", str(caught.exception))


class SliceTests(unittest.TestCase):
    def test_a_slice_stays_text_and_is_a_valid_operand(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "s.yaml"
            path.write_text(
                "name: s\ndata: { band: 70:30 }\nscene:\n  initial: a\n  beats:\n    a: { final: true }\n", encoding="utf-8")
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
