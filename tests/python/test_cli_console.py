"""UND-80: the command line keeps its promises: one plain line for every failure, help that teaches, and a way to see runs."""

import contextlib
import io
import json
import socket
import tempfile
import unittest
from pathlib import Path

from src.dashboard.view import list_runs
from src.paths import ROOT
from src.play.cli import main

PLAIN = "name: plain\ndescription: x\nmachine: { initial: only, states: { only: { final: true } } }\n"
COFFEE = ROOT / "tests" / "fixtures" / "coffee"


def run_cli(*argv) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


class DashboardFailureTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / "sketches").mkdir()
        (self.root / "sketches" / "plain.yaml").write_text(PLAIN)

    def test_a_busy_port_is_one_plain_line_and_exit_2_not_a_traceback(self):
        with socket.socket() as taken:
            taken.bind(("0.0.0.0", 0))
            taken.listen()
            port = taken.getsockname()[1]
            code, out, err = run_cli("dashboard", str(self.root / "runs"), "--port", str(port),
                                     "--plays", str(self.root / "sketches"))
        self.assertEqual(code, 2)
        self.assertEqual(err.strip().splitlines(), [f"understudy: port {port} is already in use; choose another with --port"])
        self.assertNotIn("Traceback", err + out)

    def test_a_runs_path_that_is_a_file_is_refused_in_one_line(self):
        (self.root / "runs").write_text("not a folder")
        code, _, err = run_cli("dashboard", str(self.root / "runs"), "--plays", str(self.root / "sketches"))
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), f"understudy: {self.root / 'runs'} is not a folder of runs")

    def test_a_sketches_path_that_is_not_a_folder_or_is_empty_is_refused_in_one_line(self):
        (self.root / "empty").mkdir()
        for sketches, words in ((self.root / "nope", "is not a folder"), (self.root / "empty", "no sketches found")):
            code, _, err = run_cli("dashboard", str(self.root / "runs"), "--plays", str(sketches))
            self.assertEqual(code, 2)
            self.assertEqual(len(err.strip().splitlines()), 1)
            self.assertIn(words, err)


class HelpTest(unittest.TestCase):
    def test_help_describes_every_command_with_an_example(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as caught:
            main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        text = out.getvalue()
        for command in ("run", "check", "dashboard", "runs"):
            self.assertRegex(text, rf"\n\s+{command}\s+\S+", f"{command} has no description")
        self.assertIn("examples:", text.lower())
        self.assertIn("understudy run", text)
        self.assertIn("understudy dashboard", text)

    def test_each_command_has_its_own_help_with_its_options_described(self):
        for command, option in (("run", "--replay"), ("check", "--with"), ("dashboard", "--plays"), ("runs", "folder")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                main([command, "--help"])
            self.assertIn(option, out.getvalue(), command)


class RunEndsWithTheRunIdTest(unittest.TestCase):
    def test_a_finished_run_says_its_id_and_how_to_watch_it(self):
        with tempfile.TemporaryDirectory() as folder:
            code, out, _ = run_cli("run", str(COFFEE / "coffee_week.yaml"), f"--replay={COFFEE / 'replay'}", "--out", folder)
            (run,) = [each for each in Path(folder).iterdir() if each.is_dir()]
        self.assertEqual(code, 0)
        self.assertIn(f"run: {run.name}", out)
        self.assertIn(f"watch it: understudy dashboard {folder}", out)


class RunsCommandTest(unittest.TestCase):
    def test_runs_lists_the_runs_newest_first_with_their_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, status in (("run-20261030T000000-aaaaaaaa", "complete"), ("run-20261031T000000-bbbbbbbb", "failed")):
                (root / name).mkdir()
                (root / name / "run.json").write_text(json.dumps({"status": status, "play": "coffee_week"}))
                (root / name / "events.jsonl").write_text(json.dumps({"event": "run_started", "at": "2026-10-31T00:00:00+00:00",
                                                                       "play": "examples/coffee_week.yaml"}) + "\n")
            code, out, _ = run_cli("runs", folder)
            self.assertEqual(code, 0)
            lines = out.strip().splitlines()
            self.assertEqual([each.split()[0] for each in lines], ["run-20261031T000000-bbbbbbbb", "run-20261030T000000-aaaaaaaa"])
            self.assertEqual([each.split()[-1] for each in lines], ["failed", "done"])
            self.assertEqual(len(list_runs(root)), 2)

    def test_runs_with_no_runs_or_no_folder_says_so_and_still_succeeds(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(run_cli("runs", folder)[1].strip(), f"no runs in {folder}")
            self.assertEqual(run_cli("runs", str(Path(folder) / "missing"))[:2], (0, f"no runs in {Path(folder) / 'missing'}\n"))


if __name__ == "__main__":
    unittest.main()
