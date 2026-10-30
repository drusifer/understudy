import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jev_double import JevDouble

import src.sketch.stages  # noqa: F401 - importing it registers the stages
from src.jev import Chosen
from src.sketch.blend import shortlist
from src.sketch.check import check, load_checked
from src.sketch.loader import load
from src.sketch.registry import STAGES, Stage
from src.sketch.registry import library as registered
from src.sketch.run import run_sketch
from src.sketch.sources.capture import CaptureStore
from src.sketch.sources.reader import Capture

SKETCH = """\
name: pick
sources:
  showings: showings.jsonl
  ranked:                               # the two best showings, computed by a stage
    kind: stage
    do: { reduce: { action: max } }
    with: { source: showings, field: weight, take: 2 }
  pick:
    kind: jev
    question: choice
    instructions: Choose the showing you would enjoy most.
    options: { from: ranked, key: title }
    state: {}
sinks:
  chosen: chosen.jsonl
outcomes:
  showing: { from: showings, key: title }
machine:
  initial: start
  states:
    start:
      do: { map: { action: start } }
      then: rank
    rank:
      do: { reduce: { action: blend } }
      with:
        entries:
          - decide:
              drink:
                - { showing: Alien, weight: 0.5 }
                - { showing: Brazil, weight: 0.3 }
                - { showing: Cube, weight: 0.2 }
        shortlist: 2
      then: choose
    choose:
      do: { map: { action: choose } }
      then: write
    write:
      do: { sink: { name: chosen } }
      then: done
    done:
      final: true
"""
SHOWINGS = '{"title": "Alien", "weight": 0.5}\n{"title": "Brazil", "weight": 0.3}\n{"title": "Cube", "weight": 0.2}\n'


async def start(context):
    return [{"segment": "evening", "drinks": 1}]


async def choose(context):
    rows = await context.read("pick")
    best = max(rows, key=lambda row: row["probability"])
    return [{"chosen": best["level"], "offered": [row["level"] for row in rows]}]


class CandidateCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        patcher = patch.dict(STAGES, {name: Stage(name, None, {}) for name in ("map.start", "map.choose")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, text=SKETCH, showings=SHOWINGS) -> Path:
        (self.dir / "showings.jsonl").write_text(showings, encoding="utf-8")
        path = self.dir / "pick.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def run_it(self, path, answer="Alien"):
        jev = JevDouble(choose_fn=lambda state, instructions, options: Chosen(
            answer, 0.9, {option: 1.0 if option == answer else 0.0 for option in options}))
        capture = Capture.live(CaptureStore(self.dir / "cache"), jev)
        library = {**registered(), "map.start": start, "map.choose": choose}
        return asyncio.run(run_sketch(load_checked(path), self.dir / "out", library, lambda line: None, capture)), jev


class OptionsFromRowsTests(CandidateCase):
    def test_the_sketch_checks_and_the_options_are_the_values_in_the_file(self):
        self.assertEqual(check(load(self.write())), [])

    def test_a_weighted_row_for_a_title_not_in_the_file_is_refused_with_the_nearest(self):
        path = self.write(SKETCH.replace("showing: Alien", "showing: Alein"))
        with self.assertRaisesRegex(ValueError, r"showing='Alein', not a declared option \(did you mean 'Alien'\?\)"):
            self.run_it(path)

    def test_a_candidate_outcome_must_name_a_source_or_a_state(self):
        path = self.write(SKETCH.replace("from: showings, key: title", "from: showinsg, key: title"))
        problems = check(load(path))
        self.assertTrue(any("'showinsg' is neither a source nor a state (did you mean 'showings'?)" in p for p in problems), problems)


class ShortlistTests(CandidateCase):
    def test_the_best_n_are_kept_and_renormalised(self):
        kept = shortlist({"showing": {"A": 0.5, "B": 0.3, "C": 0.2}}, 2)
        self.assertEqual(list(kept["showing"]), ["A", "B"])
        self.assertAlmostEqual(sum(kept["showing"].values()), 1.0)
        self.assertAlmostEqual(kept["showing"]["A"], 0.5 / 0.8)

    def test_fewer_candidates_than_n_keep_them_all(self):
        self.assertEqual(list(shortlist({"showing": {"A": 0.6, "B": 0.4}}, 5)["showing"]), ["A", "B"])


class JevPickTests(CandidateCase):
    def test_jev_chooses_among_the_shortlist_and_only_those_are_offered(self):
        result, jev = self.run_it(self.write(), answer="Brazil")
        (request,) = jev.requests
        self.assertEqual(list(request[3]), ["Alien", "Brazil"])       # Cube was cut: only the two best are offered
        row = result.outputs["chosen"].read_text(encoding="utf-8")
        self.assertIn('"chosen": "Brazil"', row)

    def test_a_replay_chooses_the_same_with_no_live_call(self):
        path = self.write()
        first, _ = self.run_it(path, answer="Brazil")
        store = CaptureStore(self.dir / "cache")
        library = {**registered(), "map.start": start, "map.choose": choose}
        replay = Capture.replay(store, load(path), None)
        again = asyncio.run(run_sketch(load_checked(path), self.dir / "out2", library, lambda line: None, replay))
        self.assertEqual(again.outputs["chosen"].read_text(encoding="utf-8"), first.outputs["chosen"].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
