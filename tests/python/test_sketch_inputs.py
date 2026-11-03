"""UND-87: a sketch declares typed inputs; the loader fills defaults and checks limits; the console lists and checks them."""

import io
import tempfile
import unittest
from pathlib import Path

from src.dashboard.runs import Launcher, Refused
from src.paths import ROOT
from src.sketch.cli import main
from src.sketch.inputs import default_text, problems, value_problem
from src.sketch.loader import SketchError, load

HEAD = "name: typed\ndescription: Mood {{ mood }}, weight {{ weight }}, tickets {{ tickets }}, evenings {{ evenings }}.\n"
BODY = "machine: { initial: only, states: { only: { final: true } } }\n"
INPUTS = """inputs:
  mood: { kind: choice, options: [fun, serious], default: fun, label: Mood }
  weight: { kind: range, min: 0, max: 1, step: 0.1, default: 0.3 }
  tickets: { kind: count, min: 1, max: 10, default: 2 }
  evenings: { kind: switch, default: "on" }
"""

MOOD = {"kind": "choice", "options": ["fun", "serious"], "default": "fun"}
WEIGHT = {"kind": "range", "min": 0, "max": 1, "step": 0.1, "default": 0.3}
TICKETS = {"kind": "count", "min": 1, "max": 10, "default": 2}
EVENINGS = {"kind": "switch", "default": "on"}


class RulesTests(unittest.TestCase):
    def test_a_right_declaration_has_no_problem_and_a_default_as_text(self):
        for spec, text in ((MOOD, "fun"), (WEIGHT, "0.3"), (TICKETS, "2"), (EVENINGS, "on")):
            self.assertEqual((problems("x", spec), default_text(spec)), ([], text))

    def test_each_wrong_declaration_is_named(self):
        wrong = {
            "an unknown kind": ({"kind": "dial", "default": "a"}, "unknown kind 'dial'; the kinds are choice, range, count, switch"),
            "a choice with no options": ({"kind": "choice", "options": [], "default": "a"}, "a choice needs at least one option"),
            "a default that is not an option": ({**MOOD, "default": "silly"}, "default 'silly' is not one of fun, serious"),
            "a range whose max is not above its min": ({**WEIGHT, "min": 1, "max": 1, "default": 1}, "max must be above min"),
            "a range with a step of zero": ({**WEIGHT, "step": 0}, "step must be above 0"),
            "a range default outside the limits": ({**WEIGHT, "default": 2}, "default 2 is outside 0 to 1"),
            "a count that is not whole": ({**TICKETS, "default": 2.5}, "default must be a whole number"),
            "a count default outside the limits": ({**TICKETS, "default": 11}, "default 11 is outside 1 to 10"),
            "a switch default that is not on or off": ({"kind": "switch", "default": "maybe"}, "default must be on or off"),
            "no default": ({"kind": "switch"}, "needs a default"),
        }
        for what, (spec, message) in wrong.items():
            found = problems("thing", spec)
            self.assertEqual(len(found), 1, what)
            self.assertEqual(found[0], f"input 'thing': {message}", what)

    def test_a_number_must_be_written_as_plain_digits_so_the_run_gets_the_text_it_was_checked_on(self):
        # Switch, phase 4: 1e2, nan, inf, hex and padded values passed a numeric check and reached the sketch as odd text
        for text in ("1e2", "nan", "inf", "0x5", " 5", "5 ", "+5", chr(0x665), "5_0"):  # 0x665 is an Arabic-Indic digit
            self.assertEqual(value_problem("tickets", TICKETS, text), f"input 'tickets': {text} is not a whole number", text)
            self.assertEqual(value_problem("weight", WEIGHT, text), f"input 'weight': {text} is not a number", text)

    def test_each_kind_accepts_what_is_inside_its_limits_and_refuses_the_rest(self):
        cases = (
            (MOOD, "serious", None), (MOOD, "silly", "silly is not one of fun, serious"),
            (WEIGHT, "0.5", None), (WEIGHT, "0", None), (WEIGHT, "1.0", None), (WEIGHT, "1.1", "1.1 is outside 0 to 1"),
            (WEIGHT, "0.35", "0.35 is not a multiple of 0.1 from 0"), (WEIGHT, "lots", "lots is not a number"),
            (TICKETS, "10", None), (TICKETS, "0", "0 is outside 1 to 10"), (TICKETS, "2.5", "2.5 is not a whole number"),
            (EVENINGS, "off", None), (EVENINGS, "yes", "yes is not on or off"),
        )
        for spec, text, expected in cases:
            found = value_problem("thing", spec, text)
            self.assertEqual(found, None if expected is None else f"input 'thing': {expected}", (spec["kind"], text))


class LoadTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)

    def sketch(self, text: str) -> Path:
        path = self.dir / "typed.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_a_value_left_alone_is_its_default(self):
        sketch = load(self.sketch(HEAD + INPUTS + BODY))
        self.assertEqual(sketch.description, "Mood fun, weight 0.3, tickets 2, evenings on.")
        self.assertEqual(set(sketch.inputs), {"mood", "weight", "tickets", "evenings"})
        self.assertEqual(sketch.variables, {})  # only what the owner gave is recorded as given

    def test_a_value_given_replaces_its_default(self):
        sketch = load(self.sketch(HEAD + INPUTS + BODY), variables={"mood": "serious", "tickets": "4"})
        self.assertEqual(sketch.description, "Mood serious, weight 0.3, tickets 4, evenings on.")

    def test_a_value_outside_its_limits_is_refused_naming_the_input_and_the_limits(self):
        with self.assertRaises(SketchError) as stopped:
            load(self.sketch(HEAD + INPUTS + BODY), variables={"tickets": "40"})
        self.assertIn("input 'tickets': 40 is outside 1 to 10", stopped.exception.problems[0])

    def test_a_wrong_declaration_is_refused_naming_the_input(self):
        wrong = INPUTS.replace("default: fun", "default: silly")
        with self.assertRaises(SketchError) as stopped:
            load(self.sketch(HEAD + wrong + BODY))
        self.assertIn("input 'mood': default 'silly' is not one of fun, serious", stopped.exception.problems[0])

    def test_an_unknown_kind_is_refused_naming_the_input(self):
        wrong = INPUTS.replace("kind: switch", "kind: dial")
        with self.assertRaises(SketchError) as stopped:
            load(self.sketch(HEAD + wrong + BODY))
        self.assertIn("input 'evenings'", stopped.exception.problems[0])

    def test_check_on_the_command_line_says_so_in_one_line(self):
        path = self.sketch(HEAD + INPUTS.replace("max: 10", "max: 0") + BODY)
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["check", str(path)], stdout=stdout, stderr=stderr)
        self.assertEqual(code, 2)
        self.assertIn("input 'tickets': max must be above min", stderr.getvalue())

    def test_a_value_the_sketch_takes_without_declaring_it_is_still_given_as_text(self):
        text = "name: typed\ndescription: Note {{ note }}.\n" + BODY
        self.assertEqual(load(self.sketch(text), variables={"note": "anything at all"}).description, "Note anything at all.")


class EveningTests(unittest.TestCase):
    def test_the_evening_example_declares_its_values_with_defaults_and_loads_without_any(self):
        sketch = load(ROOT / "examples" / "evening" / "evening.yaml")
        self.assertEqual({name: spec["kind"] for name, spec in sketch.inputs.items()},
                         {"mood": "choice", "tomato": "range", "audience": "range", "evenings": "switch", "tickets": "count",
                          "row": "range", "center": "range"})
        self.assertEqual(default_text(sketch.inputs["mood"]), "fun")


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.project = Path(folder.name).resolve()
        self.sketches = self.project / "sketches"
        self.sketches.mkdir()
        self.runs = self.project / "build" / "runs"
        self.runs.mkdir(parents=True)
        self.cache = self.project / ".understudy" / "cache"
        self.cache.mkdir(parents=True)
        (self.sketches / "typed.yaml").write_text(HEAD + INPUTS + BODY, encoding="utf-8")
        self.spawned: list[list[str]] = []

    def launcher(self) -> Launcher:
        class Alive:
            pid = 1
            stderr_tail = ()

            def poll(self):
                return None

        def spawn(argv, **_options):
            self.spawned.append(argv)
            return Alive()
        return Launcher(self.sketches, self.runs, project=self.project, cache=self.cache, spawn=spawn,
                        check=lambda argv: [], find_run=lambda sketch, before: None, settle=0)

    def test_the_list_gives_each_input_in_order_with_its_kind_limits_and_default(self):
        (entry,) = self.launcher().list_sketches()
        self.assertEqual([each["name"] for each in entry["inputs"]], ["mood", "weight", "tickets", "evenings"])
        mood, weight, tickets, evenings = entry["inputs"]
        self.assertEqual((mood["kind"], mood["options"], mood["default"], mood["label"]),
                         ("choice", ["fun", "serious"], "fun", "Mood"))
        self.assertEqual((weight["min"], weight["max"], weight["step"], weight["default"]), (0, 1, 0.1, 0.3))
        self.assertEqual((tickets["kind"], tickets["label"]), ("count", "tickets"))  # a label defaults to the name
        self.assertEqual((evenings["kind"], evenings["default"]), ("switch", "on"))

    def test_the_names_the_sketch_takes_without_declaring_them_stay_in_with(self):
        (self.sketches / "typed.yaml").write_text(HEAD.replace("{{ evenings }}", "{{ evenings }} {{ note }}") + INPUTS + BODY,
                                                  encoding="utf-8")
        (entry,) = self.launcher().list_sketches()
        self.assertEqual(entry["with"], ["note"])

    def test_a_sketch_with_a_wrong_declaration_is_listed_unreadable_naming_the_input(self):
        (self.sketches / "typed.yaml").write_text(HEAD + INPUTS.replace("default: fun", "default: silly") + BODY, encoding="utf-8")
        (entry,) = self.launcher().list_sketches()
        self.assertFalse(entry["ok"])
        self.assertIn("input 'mood'", entry["problem"])

    def test_a_posted_value_outside_its_limits_is_refused_before_anything_starts(self):
        launcher = self.launcher()
        for values, pattern in (({"tickets": "40"}, "input 'tickets': 40 is outside 1 to 10"),
                                ({"mood": "silly"}, "input 'mood': silly is not one of fun, serious"),
                                ({"evenings": "yes"}, "input 'evenings': yes is not on or off")):
            with self.assertRaisesRegex(Refused, pattern) as caught:
                launcher.start("typed.yaml", values)
            self.assertEqual(caught.exception.status, 400)
        self.assertEqual(self.spawned, [])

    def test_a_valid_posted_value_is_passed_to_the_run_as_with(self):
        self.launcher().start("typed.yaml", {"mood": "serious", "weight": "0.5", "tickets": "3", "evenings": "off"})
        (argv,) = self.spawned
        pairs = [argv[i + 1] for i, word in enumerate(argv) if word == "--with"]
        self.assertEqual(sorted(pairs), ["evenings=off", "mood=serious", "tickets=3", "weight=0.5"])


if __name__ == "__main__":
    unittest.main()
