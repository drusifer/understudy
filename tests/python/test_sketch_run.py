import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.paths import ROOT
from src.sketch.check import load_checked
from src.sketch.cli import main
from src.sketch.registry import STAGES, Stage
from src.sketch.run import run_sketch

BRANCH = ROOT / "tests" / "fixtures" / "machine_branch.yaml"
TEST_STAGES = {name: Stage(name, None, {}) for name in ("test.count", "test.mark", "test.boom")}


def library(count=100, fail_in=None):
    async def counted(context):
        return {"drinks": count}

    async def marked(context):
        if fail_in == context.name:
            raise RuntimeError("boom")
        return [{"took": context.name}]

    async def boom(context):
        raise RuntimeError("boom")

    return {"test.count": counted, "test.mark": marked, "test.boom": boom}


class RunCase(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(STAGES, TEST_STAGES)
        patcher.start()
        self.addCleanup(patcher.stop)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.out = self.dir / "out"

    def sketch(self, edit=None):
        text = BRANCH.read_text(encoding="utf-8")
        for old, new in edit or []:
            assert old in text
            text = text.replace(old, new)
        path = self.dir / "sketch.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def run_it(self, lib, path=None):
        lines: list[str] = []
        sketch = load_checked(path or self.sketch())
        result = asyncio.run(run_sketch(sketch, self.out, lib, lines.append))
        return result, lines

    def only_run_folder(self) -> Path:
        (folder,) = list(self.out.iterdir())
        return folder


class MachineTests(RunCase):
    def test_a_guard_is_taken_only_when_its_condition_holds(self):
        quiet, lines = self.run_it(library(count=100))
        self.assertEqual(lines, ["stage count", "stage quiet", "stage write"])
        self.assertEqual(json.loads(quiet.outputs["report"].read_text(encoding="utf-8")), {"took": "quiet"})
        busy, lines = self.run_it(library(count=900))
        self.assertEqual(lines, ["stage count", "stage busy", "stage write"])
        self.assertEqual(json.loads(busy.outputs["report"].read_text(encoding="utf-8")), {"took": "busy"})

    def test_the_run_folder_records_each_stage_and_the_events(self):
        result, _ = self.run_it(library())
        manifest = json.loads((result.directory / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(manifest["stages"], {"count": "complete", "quiet": "complete", "write": "complete"})
        events = [json.loads(line)["event"] for line in (result.directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[0], "run_started")
        self.assertEqual(events[-1], "run_finished")
        self.assertEqual(events.count("stage_started"), 3)
        summary = json.loads((result.directory / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["mode"], "live")

    def test_a_failed_stage_publishes_nothing_and_says_where_it_stopped(self):
        with self.assertRaisesRegex(RuntimeError, "boom"):
            self.run_it(library(fail_in="quiet"))
        folder = self.only_run_folder()
        manifest = json.loads((folder / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["failed_stage"], "quiet")
        self.assertEqual(manifest["stages"], {"count": "complete"})
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["events.jsonl", "run.json"])

    def test_a_failure_after_the_sink_removes_the_partial_output(self):
        path = self.sketch([("then: done\n    done:", "then: after\n    after:\n      do: test.boom\n      then: done\n    done:")])
        with self.assertRaisesRegex(RuntimeError, "boom"):
            self.run_it(library(), path)
        self.assertEqual(sorted(p.name for p in self.only_run_folder().iterdir()), ["events.jsonl", "run.json"])

    def test_a_final_state_can_name_the_outcome_the_run_ended_in(self):
        path = self.sketch([("    done:\n      final: true", "    done:\n      final: true\n      outcome: all_done")])
        result, _ = self.run_it(library(), path)
        self.assertEqual(result.outcome, "all_done")
        manifest = json.loads((result.directory / "run.json").read_text(encoding="utf-8"))
        self.assertEqual((manifest["status"], manifest["outcome"]), ("complete", "all_done"))
        last = json.loads((result.directory / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(last["outcome"], "all_done")
        self.assertTrue(result.outputs["report"].is_file())

    def test_a_final_state_with_no_outcome_leaves_it_out(self):
        result, _ = self.run_it(library())
        self.assertIsNone(result.outcome)
        self.assertNotIn("outcome", json.loads((result.directory / "run.json").read_text(encoding="utf-8")))

    def test_a_state_with_no_stage_in_the_library_is_named(self):
        with self.assertRaisesRegex(LookupError, "test.mark"):
            self.run_it({"test.count": library()["test.count"]})


class CliTests(RunCase):
    def go(self, *argv, lib=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main([*argv], library=library() if lib is None else lib, stdout=stdout, stderr=stderr)
        return code, stdout.getvalue().splitlines(), stderr.getvalue().splitlines()

    def test_run_prints_a_line_per_stage_and_names_the_output(self):
        code, out, err = self.go("run", str(self.sketch()), "--out", str(self.out))
        self.assertEqual(code, 0)
        self.assertEqual(out[:3], ["stage count", "stage quiet", "stage write"])
        self.assertTrue(out[-1].startswith("wrote ") and out[-1].endswith("report.jsonl"))
        self.assertEqual(err, [])

    def test_the_outcome_is_the_last_line_and_the_exit_is_still_0(self):
        path = self.sketch([("    done:\n      final: true", "    done:\n      final: true\n      outcome: all_done")])
        code, out, err = self.go("run", str(path), "--out", str(self.out))
        self.assertEqual((code, err, out[-1]), (0, [], "outcome: all_done"))

    def test_a_wrong_sketch_is_exit_2_with_a_last_line_saying_what_to_fix(self):
        path = self.sketch([("do: sink.report", "do: sink.reportt")])
        code, out, err = self.go("run", str(path), "--out", str(self.out))
        self.assertEqual(code, 2)
        self.assertEqual(out, [])
        self.assertTrue(err[-1].startswith("understudy: ") and "did you mean 'report'" in err[-1])
        self.assertFalse(self.out.exists())

    def test_a_missing_input_file_is_exit_2_and_nothing_is_created(self):
        path = self.sketch([("sinks:", "sources:\n  numbers: missing.jsonl\n\nsinks:")])
        code, _, err = self.go("run", str(path), "--out", str(self.out))
        self.assertEqual(code, 2)
        self.assertIn("sources.numbers", err[-1])
        self.assertFalse(self.out.exists())

    def test_source_replaces_one_file_for_the_run(self):
        path = self.sketch([("sinks:", "sources:\n  numbers: missing.jsonl\n\nsinks:")])
        real = self.dir / "real.jsonl"
        real.write_text('{"n": 1}\n', encoding="utf-8")
        code, _, err = self.go("run", str(path), "--source", f"numbers.path={real}", "--out", str(self.out))
        self.assertEqual((code, err), (0, []))
        self.assertIn("missing.jsonl", path.read_text(encoding="utf-8"))

    def test_a_failed_stage_is_exit_1_with_one_line_and_no_traceback(self):
        code, out, err = self.go("run", str(self.sketch()), "--out", str(self.out), lib=library(fail_in="quiet"))
        self.assertEqual((code, err), (1, ["understudy: boom"]))
        self.assertEqual(out, ["stage count", "stage quiet"])

    def test_output_in_a_tracked_folder_is_refused_before_starting(self):
        code, out, err = self.go("run", str(self.sketch()), "--out", str(ROOT / "src"))
        self.assertEqual(code, 2)
        self.assertEqual(out, [])
        self.assertIn("cannot write", err[-1])

    def test_check_starts_nothing(self):
        code, out, err = self.go("check", str(self.sketch()))
        self.assertEqual((code, out, err), (0, ["ok: machine_branch"], []))
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
