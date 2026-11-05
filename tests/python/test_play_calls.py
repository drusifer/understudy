"""UND-107: the stage is a play's interface. Running a play means providing its stage: from the command line (props and
file paths with --with, written files in the run folder) or from a call (its `with:` binds props and pieces, and what the
called play writes is the call beat's result, never a file)."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from src.play.check import check
from src.play.cli import main
from src.play.loader import load
from src.play.sources.capture import CaptureStore

CALLER = """\
name: caller
stage:
  words: { kind: file, path: words.jsonl }
  lengths: { kind: file, path: lengths.jsonl }
  out: { kind: file, path: out.jsonl, access: write }
scene:
  initial: write
  beats:
    measured:
      do: { play: measure.yaml }
      each: words
      with: { known: lengths, unit: letters }
    write:
      do: { write: out }
      with: { from: measured }
      to: done
    done: { final: true }
"""
CALLED = """\
name: measure
stage:
  known: { kind: file }
  length: { kind: file, path: length.jsonl, access: write }
scene:
  initial: give
  beats:
    found:
      do: { map: { action: where } }
      with: { from: known, keep: { word: { eq: "{{ word }}" } } }
    labeled:
      do: { map: { action: set } }
      with: { from: found, fields: { unit: "{{ unit }}" } }
    give:
      do: { write: length }
      with: { from: labeled }
      to: done
    done: { final: true }
"""


class CallCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        lines = lambda rows: "".join(json.dumps(row) + "\n" for row in rows)  # noqa: E731
        (self.dir / "words.jsonl").write_text(lines([{"word": "cat"}, {"word": "horse"}]), encoding="utf-8")
        (self.dir / "lengths.jsonl").write_text(lines([{"word": "cat", "n": 3}, {"word": "horse", "n": 5}]), encoding="utf-8")
        self.write(CALLER, CALLED)

    def write(self, caller: str, called: str) -> None:
        (self.dir / "caller.yaml").write_text(caller, encoding="utf-8")
        (self.dir / "measure.yaml").write_text(called, encoding="utf-8")

    def go(self, command: str, play: str = "caller.yaml", *extra: str):
        stdout, stderr = io.StringIO(), io.StringIO()
        out = ["--out", str(self.dir / "runs")] if command == "run" else []
        code = main([command, str(self.dir / play), *out, *extra], store=CaptureStore(self.dir / "cache"),
                    stdout=stdout, stderr=stderr)
        return code, stdout.getvalue(), stderr.getvalue()


class BindingTests(CallCase):
    def test_a_call_binds_a_piece_and_a_prop_and_gets_back_what_the_play_wrote_with_the_row_it_was_played_for(self):
        code, _, err = self.go("run")
        self.assertEqual((code, err), (0, ""))
        (folder,) = (self.dir / "runs").iterdir()
        rows = [json.loads(line) for line in (folder / "out.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows, [{"word": "cat", "n": 3, "unit": "letters"}, {"word": "horse", "n": 5, "unit": "letters"}])

    def test_a_called_play_writes_no_file_even_in_a_loop(self):
        self.go("run")
        (folder,) = (self.dir / "runs").iterdir()
        self.assertFalse((folder / "length.jsonl").exists())
        self.assertEqual(sorted(p.name for p in folder.iterdir() if p.suffix == ".jsonl"), ["events.jsonl", "out.jsonl"])

    def test_run_on_its_own_the_called_play_gets_its_file_from_with_and_writes_it(self):
        code, _, err = self.go("run", "measure.yaml", "--with", f"known={self.dir / 'lengths.jsonl'}", "--with", "word=cat",
                               "--with", "unit=letters")
        self.assertEqual((code, err), (0, ""))
        (folder,) = (self.dir / "runs").iterdir()
        self.assertEqual(json.loads((folder / "length.jsonl").read_text(encoding="utf-8")), {"word": "cat", "n": 3, "unit": "letters"})

    def test_run_on_its_own_without_its_file_it_is_refused_naming_how_to_give_it(self):
        code, _, err = self.go("check", "measure.yaml", "--with", "word=cat", "--with", "unit=letters")
        self.assertEqual(code, 2)
        self.assertIn("stage.known: no file given: pass --with known=<file>, or a call binds it", err)


class RefusalTests(CallCase):
    def problems(self):
        return check(load(self.dir / "caller.yaml"))

    def test_the_example_is_clean(self):
        self.assertEqual(self.problems(), [])

    def test_a_call_that_leaves_a_file_unbound_is_refused(self):
        self.write(CALLER.replace("known: lengths, ", ""), CALLED)
        self.assertTrue(any("stage.known: no file given" in p for p in self.problems()), self.problems())

    def test_a_call_that_binds_a_written_file_is_refused(self):
        self.write(CALLER.replace("known: lengths", "known: out"), CALLED)
        self.assertTrue(any("scene.beats.measured.with.known: 'out' is a file the play writes" in p for p in self.problems()),
                        self.problems())

    def test_a_called_play_that_writes_nothing_is_refused(self):
        self.write(CALLER, CALLED.replace("      do: { write: length }\n      with: { from: labeled }\n",
                                          "      do: { map: { action: where } }\n      with: { from: labeled, keep: {} }\n"))
        self.assertTrue(any("play measure.yaml writes no file, so it gives its caller nothing" in p for p in self.problems()),
                        self.problems())

    def test_a_called_play_cannot_read_a_caller_piece_it_was_not_given(self):
        self.write(CALLER, CALLED.replace("from: known,", "from: lengths,"))
        self.assertTrue(any("measure.yaml: scene.beats.found.with.from: 'lengths' is not a piece" in p for p in self.problems()),
                        self.problems())


if __name__ == "__main__":
    unittest.main()
