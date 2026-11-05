import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from src.play.check import check
from src.play.loader import load
from src.play.sources.capture import CaptureStore
from src.play.sources.reader import Capture, Sources

SKETCH = """\
name: optional
stage:
  pinned: { kind: file, path: .understudy/pinned.jsonl, optional: true }
scene:
  initial: done
  beats:
    done: { final: true }
"""


class OptionalFileSourceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.path = self.dir / "sketch.yaml"
        self.path.write_text(SKETCH, encoding="utf-8")
        (self.dir / ".understudy").mkdir()
        previous = Path.cwd()
        os.chdir(self.dir)  # a relative path in an optional source is read from where you run, like a `--with` value
        self.addCleanup(os.chdir, previous)

    def read(self, sketch):
        said = []
        sources = Sources(Capture.live(CaptureStore(self.dir / "cache")), "run", said.append)
        return asyncio.run(sources.read(sketch, "pinned")), said

    def test_when_the_value_is_not_given_and_the_default_file_is_missing_the_source_is_empty_and_says_so(self):
        sketch = load(self.path)
        self.assertEqual(check(sketch), [])
        rows, said = self.read(sketch)
        self.assertEqual(rows, [])
        self.assertEqual(said, [f"no pinned: {self.dir / '.understudy' / 'pinned.jsonl'} does not exist, so none are used"])

    def test_when_the_default_file_exists_it_is_read(self):
        (self.dir / ".understudy" / "pinned.jsonl").write_text('{"payee": "Amazon"}\n', encoding="utf-8")
        rows, said = self.read(load(self.path))
        self.assertEqual((rows, said), ([{"payee": "Amazon"}], []))

    def test_when_the_value_is_given_and_the_file_is_missing_check_stops_and_names_the_file(self):
        sketch = load(self.path, variables={"pinned": str(self.dir / "mine.jsonl")})
        (problem,) = check(sketch)
        self.assertIn(f"file {self.dir / 'mine.jsonl'} does not exist", problem)


if __name__ == "__main__":
    unittest.main()
