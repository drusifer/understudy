import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.play.stages  # noqa: F401 - importing it registers the stages
from src.play.check import check, load_checked
from src.play.loader import load
from src.play.registry import STAGES, Stage
from src.play.registry import library as registered
from src.play.run import run_sketch
from src.play.sources.capture import CaptureStore
from src.play.sources.reader import Capture

SKETCH = """\
name: seats
stage:
  seats: { kind: file, path: seats.jsonl }
  out: { kind: file, path: out.jsonl, access: write }
scene:
  initial: look
  beats:
    runs:
      do: { map: { action: adjacent_runs } }
      with: { from: seats, group: row, order: number, length: {{ length | default(2) }}, match: { free: true } }
    look:
      do: { map: { action: read_runs } }
      to: write
    write:
      do: { write: out }
      to: done
    done:
      final: true
"""
TAKEN = 6
SEATS = "".join(json.dumps({"row": "E", "number": n, "free": n != TAKEN}) + "\n" for n in range(1, 9))


class StageSourceCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        patcher = patch.dict(STAGES, {"map.read_runs": Stage("map.read_runs", None, {})})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.reads = 0

    def write(self, text=SKETCH) -> Path:
        (self.dir / "seats.jsonl").write_text(SEATS, encoding="utf-8")
        path = self.dir / "seats.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def run_it(self, path, reads=1):
        async def read_runs(context):
            rows = []
            for _ in range(reads):
                rows = await context.read("runs")
            self.reads += 1
            return rows

        library = {**registered(), "map.read_runs": read_runs}
        capture = Capture.live(CaptureStore(self.dir / "cache"))
        result = asyncio.run(run_sketch(load_checked(path), self.dir / "out", library, lambda line: None, capture))
        return [json.loads(line) for line in result.outputs["out"].read_text(encoding="utf-8").splitlines()]


class StageSourceTests(StageSourceCase):
    def test_a_stage_source_is_read_by_name_like_any_other(self):
        runs = self.run_it(self.write())
        self.assertEqual([r["run"] for r in runs], ["E1-2", "E2-3", "E3-4", "E4-5", "E7-8"])

    def test_it_is_computed_once_however_often_it_is_read(self):
        calls = []
        original = STAGES["map.adjacent_runs"].run

        async def counted(*args, **kwargs):
            calls.append(1)
            return await original(*args, **kwargs)

        path = self.write()
        with patch.dict(STAGES, {"map.adjacent_runs": Stage("map.adjacent_runs", counted, STAGES["map.adjacent_runs"].params)}):
            self.run_it(path, reads=3)
        self.assertEqual(len(calls), 1)

    def test_its_with_values_come_from_the_template(self):
        runs = self.run_it(self.write())
        self.assertTrue(all(r["last"] - r["first"] == 1 for r in runs))

    def test_a_beat_that_reads_itself_is_refused(self):
        text = SKETCH.replace("with: { from: seats,", "with: { from: runs,")
        problems = check(load(self.write(text)))
        self.assertTrue(any("scene.beats.runs.with: beat 'runs' reads itself" in p for p in problems), problems)

    def test_an_unknown_action_is_refused_with_the_nearest(self):
        text = SKETCH.replace("action: adjacent_runs", "action: adjacent_run")
        problems = check(load(self.write(text)))
        self.assertTrue(any("unknown action 'map.adjacent_run' (did you mean 'map.adjacent_runs'?)" in p for p in problems), problems)

    def test_a_from_naming_an_unknown_piece_is_refused(self):
        text = SKETCH.replace("from: seats,", "from: seatz,")
        problems = check(load(self.write(text)))
        self.assertTrue(any("scene.beats.runs.with.from: 'seatz' is not a piece (did you mean 'seats'?)" in p for p in problems),
                        problems)

    def test_a_write_without_to_is_refused(self):
        text = SKETCH.replace("do: { map: { action: adjacent_runs } }", "do: { write: out }")
        problems = check(load(self.write(text)))
        self.assertTrue(any("a beat without `to:` is a `map` or `reduce` action" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
