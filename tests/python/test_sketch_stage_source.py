import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.sketch.stages  # noqa: F401 - importing it registers the stages
from src.sketch.check import check, load_checked
from src.sketch.loader import load
from src.sketch.registry import STAGES, Stage
from src.sketch.registry import library as registered
from src.sketch.run import run_sketch
from src.sketch.sources.capture import CaptureStore
from src.sketch.sources.reader import Capture

SKETCH = """\
name: seats
sources:
  seats: seats.jsonl
  runs:
    kind: stage
    do: { etl: { action: adjacent_runs } }
    with: { source: seats, group: row, order: number, length: {{ length | default(2) }}, match: { free: true } }
sinks:
  out: out.jsonl
machine:
  initial: look
  states:
    look:
      do: { etl: { action: read_runs } }
      then: write
    write:
      do: { sink: { name: out } }
      then: done
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
        patcher = patch.dict(STAGES, {"etl.read_runs": Stage("etl.read_runs", None, {})})
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

        library = {**registered(), "etl.read_runs": read_runs}
        capture = Capture.live(CaptureStore(self.dir / "cache"))
        result = asyncio.run(run_sketch(load_checked(path), self.dir / "out", library, lambda line: None, capture))
        return [json.loads(line) for line in result.outputs["out"].read_text(encoding="utf-8").splitlines()]


class StageSourceTests(StageSourceCase):
    def test_a_stage_source_is_read_by_name_like_any_other(self):
        runs = self.run_it(self.write())
        self.assertEqual([r["run"] for r in runs], ["E1-2", "E2-3", "E3-4", "E4-5", "E7-8"])

    def test_it_is_computed_once_however_often_it_is_read(self):
        calls = []
        original = STAGES["etl.adjacent_runs"].run

        async def counted(*args, **kwargs):
            calls.append(1)
            return await original(*args, **kwargs)

        path = self.write()
        with patch.dict(STAGES, {"etl.adjacent_runs": Stage("etl.adjacent_runs", counted, STAGES["etl.adjacent_runs"].params)}):
            self.run_it(path, reads=3)
        self.assertEqual(len(calls), 1)

    def test_its_with_values_come_from_the_template(self):
        runs = self.run_it(self.write())
        self.assertTrue(all(r["last"] - r["first"] == 1 for r in runs))

    def test_a_stage_source_that_reads_itself_is_refused(self):
        text = SKETCH.replace("with: { source: seats,", "with: { source: runs,")
        problems = check(load(self.write(text)))
        self.assertTrue(any("source 'runs' reads itself" in p for p in problems), problems)

    def test_an_unknown_action_is_refused_with_the_nearest(self):
        text = SKETCH.replace("action: adjacent_runs", "action: adjacent_run")
        problems = check(load(self.write(text)))
        self.assertTrue(any("unknown stage 'etl.adjacent_run' (did you mean 'etl.adjacent_runs'?)" in p for p in problems), problems)

    def test_a_source_param_naming_an_unknown_source_is_refused(self):
        text = SKETCH.replace("source: seats,", "source: seatz,")
        problems = check(load(self.write(text)))
        self.assertTrue(any("'seatz' is not a source (did you mean 'seats'?)" in p for p in problems), problems)

    def test_a_sink_or_sketch_cannot_compute_a_source(self):
        text = SKETCH.replace("do: { etl: { action: adjacent_runs } }", "do: { sink: { name: out } }")
        problems = check(load(self.write(text)))
        self.assertTrue(any("a source is computed by an `etl` or `convert` stage" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
