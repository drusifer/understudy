import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jev_double import JevDouble

from src.jev import Chosen
from src.paths import ROOT
from src.sketch.check import check
from src.sketch.cli import main
from src.sketch.loader import load
from src.sketch.sources.capture import CaptureStore
from src.sketch.sources.file import read_jsonl
from src.sketch.stages import LIBRARY
from src.sketch.vocabulary import STAGES

FIXTURES = ROOT / "tests" / "fixtures" / "coffee"
LEVELS = ("much_colder", "colder", "same", "warmer", "much_warmer")


def answer(level: str, spread: dict | None = None) -> Chosen:
    probabilities = {name: 0.0 for name in LEVELS} | (spread or {level: 1.0})
    return Chosen(level, probabilities[level], probabilities)


def double(level="warmer", spread=None, fail=None):
    return JevDouble(choose_fn=lambda state, instructions, options: answer(level, spread), fail=fail)


class CoffeeCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        for item in FIXTURES.iterdir():
            if item.is_file():
                shutil.copy(item, self.dir / item.name)
        self.sketch = self.dir / "coffee_week.yaml"
        self.store = CaptureStore(self.dir / "cache")
        self.out = self.dir / "out"

    def go(self, *flags, jev=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["run", str(self.sketch), "--out", str(self.out), *flags], make_jev=lambda: jev, store=self.store,
                    stdout=stdout, stderr=stderr)
        return code, stdout.getvalue().splitlines(), stderr.getvalue().splitlines()

    def folder(self, lines) -> Path:
        wrote = next(line for line in lines if line.startswith("wrote "))
        return Path(wrote.removeprefix("wrote ")).parent

    def summary(self, lines) -> dict:
        return json.loads((self.folder(lines) / "summary.json").read_text(encoding="utf-8"))


class LibraryTests(unittest.TestCase):
    def test_the_stage_library_and_the_vocabulary_name_the_same_stages(self):
        self.assertEqual(set(LIBRARY) - {"blend"}, set(STAGES))


class CoffeeRunTests(CoffeeCase):
    def test_the_whole_run_writes_the_ingredients_and_counts(self):
        code, lines, err = self.go(jev=double())
        self.assertEqual((code, err), (0, []))
        self.assertEqual([line for line in lines if line.startswith("stage")], [
            "stage weather", "stage weather_change.judge", "stage split_trade", "stage match_orders", "stage to_ingredients",
            "stage write"])
        self.assertEqual(read_jsonl(self.folder(lines) / "ingredients.jsonl"),
                         [{"amount": 32000, "ingredient": "coffee_beans", "unit": "g"}])
        summary = self.summary(lines)
        self.assertEqual(summary["total_drinks"], 1600)
        self.assertEqual(summary["drinks_per_segment"], {"commuters": 560, "night_workers": 240, "others": 160, "students": 480,
                                                         "teens": 160})
        self.assertEqual((summary["mode"], summary["stale"], summary["jev_requests"]), ("live", False, 1))
        self.assertEqual(summary["weather_change_weights"], {"hot": 0.45, "iced": 0.55})

    def test_the_segments_add_up_to_the_total(self):
        _, lines, _ = self.go(jev=double())
        self.assertAlmostEqual(sum(self.summary(lines)["drinks_per_segment"].values()), 1600)

    def test_warm_weather_nudges_students_but_night_workers_stay_on_hot_coffee(self):
        _, lines, _ = self.go(jev=double("much_warmer"))
        shares = self.summary(lines)["shares_per_segment"]
        self.assertEqual(shares["night_workers"]["temp"], {"hot": 1.0})
        self.assertAlmostEqual(shares["students"]["temp"]["iced"], (1 * 0.7 + 0.3 * 0.7) / 1.3, places=5)
        _, lines, _ = self.go(jev=double("much_colder"))
        colder = self.summary(lines)["shares_per_segment"]["students"]["temp"]["iced"]
        self.assertAlmostEqual(colder, (1 * 0.7 + 0.3 * 0.1) / 1.3, places=5)
        self.assertLess(colder, shares["students"]["temp"]["iced"])

    def test_mixed_probabilities_give_their_weighted_average(self):
        _, lines, _ = self.go(jev=double("warmer", {"warmer": 0.5, "colder": 0.5}))
        self.assertEqual(self.summary(lines)["weather_change_weights"], {"hot": 0.6, "iced": 0.4})

    def test_teens_never_get_caffeine(self):
        _, lines, _ = self.go(jev=double())
        for segment, shares in self.summary(lines)["shares_per_segment"].items():
            if segment == "teens":
                self.assertNotIn("high", shares.get("caffeine", {}))

    def test_packs_round_up_to_whole_packs(self):
        text = self.sketch.read_text(encoding="utf-8").replace("coffee_beans: 1000", "coffee_beans: 5000")
        self.sketch.write_text(text, encoding="utf-8")
        _, lines, _ = self.go(jev=double())
        self.assertEqual(read_jsonl(self.folder(lines) / "ingredients.jsonl")[0]["amount"], 35000)

    def test_two_replays_of_a_live_run_are_byte_identical(self):
        self.go(jev=double())
        first = self.go("--replay")[1]
        second = self.go("--replay")[1]
        for name in ("ingredients.jsonl", "summary.json"):
            self.assertEqual((self.folder(first) / name).read_bytes(), (self.folder(second) / name).read_bytes(), name)
        self.assertEqual(self.summary(first)["mode"], "replay")

    def test_the_committed_live_capture_replays_with_no_key_and_no_network(self):
        # tests/fixtures/coffee/replay holds the one real Jev answer (Sprint 19 close): a cold forecast after a mild week
        code, lines, err = self.go(f"--replay={FIXTURES / 'replay'}")
        self.assertEqual((code, err), (0, []))
        summary = self.summary(lines)
        self.assertEqual((summary["mode"], summary["stale"], summary["jev_requests"]), ("replay", False, 0))
        self.assertEqual(summary["weather_change_weights"], {"hot": 0.8925, "iced": 0.1075})
        self.assertEqual(read_jsonl(self.folder(lines) / "ingredients.jsonl"),
                         [{"amount": 32000, "ingredient": "coffee_beans", "unit": "g"}])

    def test_output_lands_in_the_run_folder_and_nowhere_tracked(self):
        _, lines, _ = self.go(jev=double())
        self.assertTrue(str(self.folder(lines)).startswith(str(self.out)))
        tracked = ROOT / "ingredients.jsonl"
        self.assertFalse(tracked.exists())


class CoffeeFailureTests(CoffeeCase):
    def test_a_decider_row_with_an_undeclared_option_is_refused_at_run_time_naming_the_stage(self):
        text = self.sketch.read_text(encoding="utf-8")
        self.sketch.write_text(text, encoding="utf-8")
        weather = self.dir / "weather_change.yaml"
        weather.write_text(weather.read_text(encoding="utf-8").replace("warmer:      { hot: 0.45, iced: 0.55 }",
                                                                       "warmer:      { hot: 0.45, ice: 0.55 }"), encoding="utf-8")
        code, _, err = self.go(jev=double())
        self.assertEqual(code, 1)
        self.assertIn("stage match_orders", err[-1])
        self.assertIn("temp='ice'", err[-1])
        self.assertIn("did you mean 'iced'", err[-1])
        self.assertEqual(list(self.out.glob("*/ingredients.jsonl")), [])

    def test_a_forbid_that_empties_a_segment_fails_the_run_naming_the_rule_and_the_segment(self):
        text = self.sketch.read_text(encoding="utf-8").replace("age_max: { le: 17 }", "age_max: { le: 24 }")
        text = text.replace("{ temp: hot,  size: medium, weight: 0.6 }", "{ temp: hot,  size: medium, caffeine: high, weight: 0.6 }")
        text = text.replace("{ temp: iced, size: medium, weight: 0.4 }", "{ temp: iced, size: medium, caffeine: high, weight: 0.4 }")
        text = text.replace("{ temp: iced, size: large,  weight: 0.5 }", "{ temp: iced, size: large, caffeine: high, weight: 0.5 }")
        text = text.replace("{ temp: iced, size: medium, weight: 0.2 }", "{ temp: iced, size: medium, caffeine: high, weight: 0.2 }")
        text = text.replace("{ temp: hot,  size: medium, weight: 0.3 }", "{ temp: hot,  size: medium, caffeine: high, weight: 0.3 }")
        self.sketch.write_text(text, encoding="utf-8")
        code, _, err = self.go(jev=double())
        self.assertEqual(code, 1)
        self.assertRegex(err[-1], r"forbid rule 0 left (students|teens) with no option for 'caffeine'")

    def test_no_key_means_a_live_run_is_refused_before_any_stage(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        from src.jev import TypeSafeJev
        code = main(["run", str(self.sketch), "--out", str(self.out)], make_jev=lambda: TypeSafeJev(environment={}),
                    store=self.store, stdout=stdout, stderr=stderr)
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("TYPESAFE_API_KEY", stderr.getvalue())


class CoffeeSketchesAreClean(unittest.TestCase):
    def test_the_fixture_sketches_pass_the_check(self):
        self.assertEqual(check(load(FIXTURES / "coffee_week.yaml")), [])


if __name__ == "__main__":
    unittest.main()
