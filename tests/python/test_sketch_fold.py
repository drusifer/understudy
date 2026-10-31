import io
import json
import tempfile
import unittest
from pathlib import Path

from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

PARENT = """\
name: fold
sources:
  words: words.jsonl
sinks:
  out: out.jsonl
machine:
  initial: walk
  states:
    walk:
      do: { sketch: { file: step } }
      each: words
      reduce: { action: concat, into: seen }
      then: write
    write:
      do: { sink: { name: out } }
      then: done
    done:
      final: true
"""
CHILD = """\
name: step
machine:
  initial: add
  states:
    add:
      do: { map: { action: rows } }
      with:
        rows: [ { word: {{ word | tojson }}, earlier: {{ seen | map(attribute='word') | list | tojson }} } ]
      then: done
    done:
      final: true
      outputs: [word]
"""


class FoldCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        (self.dir / "words.jsonl").write_text("".join(json.dumps({"word": w}) + "\n" for w in ("a", "b", "c")), encoding="utf-8")
        (self.dir / "fold.yaml").write_text(PARENT, encoding="utf-8")
        (self.dir / "step.yaml").write_text(CHILD, encoding="utf-8")

    def go(self, command="run"):
        stdout, stderr = io.StringIO(), io.StringIO()
        extra = ["--out", str(self.dir / "out")] if command == "run" else []
        code = main([command, str(self.dir / "fold.yaml"), *extra], store=CaptureStore(self.dir / "cache"),
                    stdout=stdout, stderr=stderr)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_each_iteration_receives_what_the_earlier_ones_output(self):
        code, out, err = self.go()
        self.assertEqual((code, err), (0, ""))
        (written,) = (self.dir / "out").glob("*/out.jsonl")
        rows = [json.loads(line) for line in written.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(r["word"], r["earlier"]) for r in rows], [("a", []), ("b", ["a"]), ("c", ["a", "b"])])

    def test_the_checker_accepts_a_fold(self):
        self.assertEqual(self.go("check")[0], 0)

    def test_a_child_that_never_uses_the_running_list_is_refused(self):
        unused = CHILD.replace("{{ seen | map(attribute='word') | list | tojson }}", "[]")
        (self.dir / "step.yaml").write_text(unused, encoding="utf-8")
        code, _, err = self.go("check")
        self.assertEqual(code, 2)
        self.assertIn("seen", err)

    def test_reduce_without_each_is_refused(self):
        (self.dir / "fold.yaml").write_text(PARENT.replace("      each: words\n", ""), encoding="utf-8")
        (self.dir / "step.yaml").write_text(CHILD.replace(CHILD[CHILD.index("        rows:"):CHILD.index("      then")],
                                                          "        rows: []\n"), encoding="utf-8")
        code, _, err = self.go("check")
        self.assertEqual(code, 2)
        self.assertIn("each", err)


if __name__ == "__main__":
    unittest.main()
