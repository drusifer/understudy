import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.sketch.check import check, load_checked
from src.sketch.cli import main
from src.sketch.loader import SketchError, load
from src.sketch.run import run_sketch
from src.sketch.vocabulary import STAGES

PARENT = """\
name: parent
outcomes:
  a: [x]
machine:
  initial: first
  states:
    first:
      do: sketch.child
      with: { seats: {{ tickets | default(2) }} }
      then: second
    second:
      do: sketch.child
      with: { seats: 9 }
      then: done
    done:
      final: true
"""
CHILD = """\
name: child
data:
  seats: {{ seats | default(1) }}
machine:
  initial: look
  states:
    look:
      do: test.look
      then: done
    done:
      final: true
      outputs: [a]
"""


class TemplateCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        patcher = patch.dict(STAGES, {"test.look": {}})
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, parent=PARENT, child=CHILD) -> Path:
        (self.dir / "child.yaml").write_text(child, encoding="utf-8")
        path = self.dir / "parent.yaml"
        path.write_text(parent, encoding="utf-8")
        return path

    def run_it(self, path, **variables):
        seen = []

        async def look(context):
            seen.append(context.sketch.data["seats"])
            return [{"a": "x", "weight": 1}]

        sketch = load_checked(path, variables=variables)
        asyncio.run(run_sketch(sketch, self.dir / "out", {"test.look": look}, lambda line: None))
        return seen


class RenderTests(TemplateCase):
    def test_a_variable_with_a_default_needs_no_value(self):
        self.assertEqual(self.run_it(self.write()), [2, 9])

    def test_a_given_value_replaces_the_default_and_is_typed_by_yaml(self):
        seen = self.run_it(self.write(), tickets="3")
        self.assertEqual(seen, [3, 9])
        self.assertIsInstance(seen[0], int)

    def test_a_variable_with_no_default_and_no_value_is_named(self):
        path = self.write(PARENT.replace("tickets | default(2)", "tickets"))
        with self.assertRaisesRegex(SketchError, "needs a value for 'tickets': pass --with tickets=<value>"):
            load(path)

    def test_a_template_syntax_error_names_the_line(self):
        path = self.write(PARENT.replace("{{ tickets | default(2) }}", "{{ tickets"))
        with self.assertRaisesRegex(SketchError, "parent.yaml: line \\d+"):
            load(path)

    def test_plain_yaml_with_no_template_is_unchanged(self):
        path = self.write(PARENT.replace("{{ tickets | default(2) }}", "2"))
        self.assertEqual(load(path).machine["states"]["first"]["with"], {"seats": 2})


class ComposeTests(TemplateCase):
    def test_one_sketch_can_be_called_twice_with_different_values(self):
        self.assertEqual(self.run_it(self.write(), tickets="4"), [4, 9])

    def test_a_child_sees_only_what_its_call_passes(self):
        parent = PARENT.replace("outcomes:", "data: { party: {{ tickets | default(2) }} }\noutcomes:")
        parent = parent.replace("      with: { seats: {{ tickets | default(2) }} }\n", "").replace("      with: { seats: 9 }\n", "")
        child = CHILD.replace("seats | default(1)", "tickets | default(1)")
        self.assertEqual(self.run_it(self.write(parent, child), tickets="4"), [1, 1])


class NameTests(TemplateCase):
    def test_a_with_name_no_file_uses_is_refused_with_the_nearest(self):
        sketch = load(self.write(), variables={"tikets": "3"})
        problems = check(sketch)
        self.assertTrue(any("--with tikets: the file does not use it (did you mean 'tickets'?); it uses: tickets" in p
                            for p in problems), problems)

    def test_a_call_that_passes_a_name_the_child_does_not_use_is_refused(self):
        path = self.write(PARENT.replace("{ seats: 9 }", "{ seatz: 9 }"))
        problems = check(load(path))
        self.assertTrue(any("with seatz: the file does not use it (did you mean 'seats'?)" in p for p in problems), problems)

    def test_the_command_line_flag_is_with(self):
        path = self.write()
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["check", str(path), "--with", "tickets=3"], stdout=stdout, stderr=stderr)
        self.assertEqual((code, stdout.getvalue(), stderr.getvalue()), (0, "ok: parent\n", ""))
        code = main(["check", str(path), "--with", "tikets=3"], stdout=io.StringIO(), stderr=stderr)
        self.assertEqual(code, 2)
        self.assertIn("did you mean 'tickets'", stderr.getvalue())


EACH_PARENT = """\
name: parent
sources:
  films: films.jsonl
sinks:
  pairs: pairs.jsonl
machine:
  initial: score
  states:
    score:
      do: sketch.child
      each: films
      then: write
    write:
      do: sink.pairs
      then: done
    done:
      final: true
"""
EACH_CHILD = """\
name: child
data:
  title: "{{ title }}"
machine:
  initial: look
  states:
    look:
      do: test.look
      then: done
    done:
      final: true
      outputs: [audience]
"""


class EachTests(TemplateCase):
    def write_each(self, parent=EACH_PARENT) -> Path:
        (self.dir / "films.jsonl").write_text('{"title": "It Follows"}\n{"title": "Hereditary"}\n', encoding="utf-8")
        return self.write(parent, EACH_CHILD)

    def run_each(self, path):
        seen = []

        async def look(context):
            seen.append(context.sketch.data["title"])
            return [{"audience": "loved", "weight": 1}]

        sketch = load_checked(path)
        result = asyncio.run(run_sketch(sketch, self.dir / "out", {"test.look": look}, lambda line: None))
        lines = result.outputs["pairs"].read_text(encoding="utf-8").splitlines()
        return seen, [json.loads(line) for line in lines]

    def test_a_sketch_runs_once_per_row_and_the_result_pairs_each_row_with_its_output(self):
        seen, pairs = self.run_each(self.write_each())
        self.assertEqual(seen, ["It Follows", "Hereditary"])
        self.assertEqual(pairs, [
            {"input": {"title": "It Follows"}, "output": [{"audience": "loved", "weight": 1}]},
            {"input": {"title": "Hereditary"}, "output": [{"audience": "loved", "weight": 1}]},
        ])

    def test_each_must_name_a_source(self):
        path = self.write_each(EACH_PARENT.replace("each: films", "each: filsm"))
        self.assertTrue(any("'filsm' is not a source (did you mean 'films'?)" in p for p in check(load(path))))

    def test_each_repeats_only_a_sketch(self):
        path = self.write_each(EACH_PARENT.replace("do: sketch.child\n      each", "do: test.look\n      each"))
        self.assertTrue(any("`each` repeats a sketch" in p for p in check(load(path))))


if __name__ == "__main__":
    unittest.main()
