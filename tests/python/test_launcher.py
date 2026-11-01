"""UND-79: the console starts, replays and stops runs, behind one secret, and only what it should."""

import json
import shutil
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from src.dashboard.runs import Launcher, Refused
from src.dashboard.server import serve
from src.paths import ROOT

COFFEE = ROOT / "tests" / "fixtures" / "coffee"
SECRET = "s3cret-for-tests"
PLAIN = """name: plain
description: >
  Reads a file and says hello.
sources:
  data: {{ file }}
machine:
  initial: only
  states:
    only: { final: true }
"""
PARENT = """name: parent
description: calls a child
machine:
  initial: ask
  states:
    ask: { do: { sketch: { file: child } }, then: done }
    done: { final: true }
"""
CHILD = "name: child\ndescription: only called, never run on its own\nmachine: { initial: x, states: { x: { final: true } } }\n"


class LauncherCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.project = Path(self.folder.name).resolve()
        (self.project / "data").mkdir()
        (self.project / "data" / "in.csv").write_text("a\n")
        self.sketches = self.project / "sketches"
        self.sketches.mkdir()
        self.runs = self.project / "build" / "runs"
        self.runs.mkdir(parents=True)
        self.cache = self.project / ".understudy" / "cache"
        self.cache.mkdir(parents=True)
        self.spawned: list[list[str]] = []

    def write(self, name: str, text: str) -> Path:
        path = self.sketches / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def launcher(self, **options) -> Launcher:
        """A launcher over the temporary project; tests that fake the process also skip the wait for the run folder."""
        if "spawn" in options:
            options.setdefault("find_run", lambda sketch, before: None)
            options.setdefault("settle", 0)
        return Launcher(self.sketches, self.runs, project=self.project, cache=self.cache, **options)


class ListTest(LauncherCase):
    def test_the_list_shows_each_sketch_with_its_description_and_the_names_it_takes(self):
        self.write("plain.yaml", PLAIN)
        (entry,) = self.launcher().list_sketches()
        self.assertEqual((entry["file"], entry["name"], entry["ok"]), ("plain.yaml", "plain", True))
        self.assertEqual(entry["description"], "Reads a file and says hello.")
        self.assertEqual(entry["with"], ["file"])

    def test_a_sketch_that_is_only_called_by_another_is_not_offered(self):
        self.write("parent.yaml", PARENT)
        self.write("child.yaml", CHILD)
        self.assertEqual([each["file"] for each in self.launcher().list_sketches()], ["parent.yaml"])

    def test_a_file_that_cannot_be_read_is_listed_greyed_out_with_the_reason(self):
        self.write("broken.yaml", "name: broken\nmachine: [unclosed\n")
        (entry,) = self.launcher().list_sketches()
        self.assertFalse(entry["ok"])
        self.assertTrue(entry["problem"])

    def test_sketches_in_a_subfolder_are_listed_with_their_folder(self):
        self.write("more/plain.yaml", PLAIN)
        self.assertEqual([each["file"] for each in self.launcher().list_sketches()], ["more/plain.yaml"])

    def test_a_folder_with_no_sketches_or_that_is_not_a_folder_is_refused_when_the_launcher_is_made(self):
        with self.assertRaisesRegex(Refused, "no sketches"):
            self.launcher()
        with self.assertRaisesRegex(Refused, "not a folder"):
            Launcher(self.project / "nope", self.runs, project=self.project, cache=self.cache)


class StartRefusalTest(LauncherCase):
    def setUp(self):
        super().setUp()
        self.write("plain.yaml", PLAIN)
        self.launcher_ = self.launcher(spawn=self.fake_spawn)

    def fake_spawn(self, argv, **_options):
        self.spawned.append(argv)
        raise AssertionError("a refused request must not start anything")

    def refused(self, code: int, pattern: str, **request):
        with self.assertRaisesRegex(Refused, pattern) as caught:
            self.launcher_.start(request.pop("sketch", "plain.yaml"), request.pop("values", {"file": "data/in.csv"}), **request)
        self.assertEqual(caught.exception.status, code)
        self.assertEqual(self.spawned, [])

    def test_a_sketch_outside_the_folder_is_refused(self):
        (self.project / "outside.yaml").write_text(PLAIN)
        for sketch in ("../outside.yaml", "/etc/passwd", "sub/../../outside.yaml", "plain.yaml/../../outside.yaml"):
            self.refused(403, "not a sketch in", sketch=sketch)

    def test_a_symlink_that_leaves_the_folder_is_refused(self):
        (self.project / "outside.yaml").write_text(PLAIN)
        (self.sketches / "link.yaml").symlink_to(self.project / "outside.yaml")
        self.refused(403, "not a sketch in", sketch="link.yaml")

    def test_a_name_the_sketch_does_not_take_is_refused_and_the_names_it_takes_are_listed(self):
        self.refused(400, "unknown.*file", values={"file": "data/in.csv", "extra": "x"})

    def test_a_value_naming_a_file_outside_the_project_is_refused(self):
        secret = self.project.parent / "elsewhere.txt"
        secret.write_text("x")
        self.addCleanup(secret.unlink)
        self.refused(400, "outside the project", values={"file": str(secret)})
        self.refused(400, "outside the project", values={"file": "../elsewhere.txt"})
        (self.project / "data" / "out").symlink_to(secret)
        self.refused(400, "outside the project", values={"file": "data/out"})

    def test_a_replay_id_that_is_not_a_captured_run_is_refused(self):
        for replay in ("../../etc", "run-nope", "--out=/tmp/x", "latest;rm"):
            self.refused(400, "no captured run", replay=replay)

    def test_a_value_with_a_line_break_is_refused(self):
        self.refused(400, "single line", values={"file": "data/in.csv\n--out=/tmp/x"})


class StartTest(LauncherCase):
    """These use a fake process so nothing runs; the real one is in `EndToEndTest`."""

    class FakeProcess:
        def __init__(self, argv, **options):
            self.argv, self.options, self.returncode, self.pid, self.killed = argv, options, None, 4242, []
            self.stderr = None

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    def setUp(self):
        super().setUp()
        self.write("plain.yaml", PLAIN)
        self.write("other.yaml", PLAIN.replace("name: plain", "name: other"))
        self.processes: list[StartTest.FakeProcess] = []

        def spawn(argv, **options):
            process = StartTest.FakeProcess(argv, **options)
            self.processes.append(process)
            return process

        self.checks: list[list[str]] = []
        self.launcher_ = self.launcher(spawn=spawn, check=lambda argv: self.checks.append(argv) or [])

    def test_play_checks_first_then_starts_an_argument_list_with_no_shell_in_its_own_session(self):
        result = self.launcher_.start("plain.yaml", {"file": "data/in.csv"})
        self.assertTrue(result["started"])
        self.assertEqual(self.checks[0][self.checks[0].index("check") + 1], str(self.sketches / "plain.yaml"))
        self.assertIn("file=data/in.csv", self.checks[0])
        (process,) = self.processes
        self.assertIn("run", process.argv)
        self.assertEqual(process.argv[process.argv.index("--with") + 1], "file=data/in.csv")
        self.assertEqual(process.argv[process.argv.index("--out") + 1], str(self.runs))
        self.assertTrue(process.options["start_new_session"])
        self.assertIs(process.options.get("shell", False), False)
        self.assertEqual(Path(process.options["cwd"]), self.project)

    def test_a_failing_check_returns_its_lines_and_starts_nothing(self):
        launcher = self.launcher(spawn=lambda *a, **k: self.fail("must not start"),
                                 check=lambda argv: ["understudy: file: cannot be read"])
        with self.assertRaisesRegex(Refused, "cannot be read") as caught:
            launcher.start("plain.yaml", {"file": "data/missing.csv"})
        self.assertEqual(caught.exception.status, 400)

    def test_a_second_play_for_the_same_sketch_is_refused_with_a_409_while_the_first_is_alive(self):
        self.launcher_.start("plain.yaml", {"file": "data/in.csv"})
        with self.assertRaisesRegex(Refused, "already running") as caught:
            self.launcher_.start("plain.yaml", {"file": "data/in.csv"})
        self.assertEqual(caught.exception.status, 409)
        self.processes[0].returncode = 0  # the first one ends: the sketch may be started again
        self.launcher_.start("plain.yaml", {"file": "data/in.csv"})
        self.assertEqual(len(self.processes), 2)

    def test_no_more_than_four_runs_at_once(self):
        for index in range(4):
            self.write(f"s{index}.yaml", PLAIN.replace("name: plain", f"name: s{index}"))
        for index in range(4):
            self.launcher_.start(f"s{index}.yaml", {"file": "data/in.csv"})
        with self.assertRaisesRegex(Refused, "at most 4") as caught:
            self.launcher_.start("plain.yaml", {"file": "data/in.csv"})
        self.assertEqual(caught.exception.status, 409)

    def test_a_replay_runs_from_the_chosen_captured_run_inside_the_cache(self):
        (self.cache / "run-20261030T000000-abcdef12").mkdir()
        self.launcher_.start("plain.yaml", {"file": "data/in.csv"}, replay="run-20261030T000000-abcdef12")
        argv = self.processes[0].argv
        self.assertIn(f"--replay={self.cache / 'run-20261030T000000-abcdef12'}", argv)
        self.assertEqual(self.launcher_.replays(), ["run-20261030T000000-abcdef12"])

    def test_a_process_that_dies_at_once_reports_why_instead_of_starting(self):
        def dies(argv, **options):
            process = StartTest.FakeProcess(argv, **options)
            process.returncode = 1
            process.stderr_tail = ["understudy: Jev needs a TypeSafe key: set TYPESAFE_API_KEY"]
            return process

        launcher = self.launcher(spawn=dies, check=lambda argv: [])
        with self.assertRaisesRegex(Refused, "TYPESAFE_API_KEY") as caught:
            launcher.start("plain.yaml", {"file": "data/in.csv"})
        self.assertEqual(caught.exception.status, 400)


class StopTest(LauncherCase):
    def test_stop_ends_only_a_process_the_console_started_and_marks_its_run_stopped(self):
        self.write("plain.yaml", PLAIN)
        signals: list[tuple[int, int]] = []
        run = self.runs / "run-20261101T100000-aaaaaaaa"
        run.mkdir()
        (run / "run.json").write_text(json.dumps({"status": "running", "stages": {}}))

        class Alive:
            pid, returncode, stderr = 4243, None, None

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                Alive.returncode = -15
                return -15

        launcher = self.launcher(spawn=lambda argv, **o: Alive(), check=lambda argv: [],
                                 kill=lambda pid, sig: signals.append((pid, sig)),
                                 find_run=lambda sketch, before: "run-20261101T100000-aaaaaaaa")
        result = launcher.start("plain.yaml", {"file": "data/in.csv"})
        self.assertEqual(result["run"], "run-20261101T100000-aaaaaaaa")
        launcher.stop("run-20261101T100000-aaaaaaaa")
        self.assertEqual([pid for pid, _ in signals], [4243])
        self.assertEqual(json.loads((run / "run.json").read_text())["status"], "stopped")
        with self.assertRaisesRegex(Refused, "not started by this console") as caught:
            launcher.stop("run-20260101T000000-zzzzzzzz")
        self.assertEqual(caught.exception.status, 404)
        with self.assertRaisesRegex(Refused, "not started by this console"):
            launcher.stop("../../x")


class HttpTest(LauncherCase):
    """The routes: reads stay open; every POST needs the secret, a same-origin request, and a small JSON body."""

    def setUp(self):
        super().setUp()
        self.write("plain.yaml", PLAIN)
        self.started: list[tuple[str, dict]] = []
        launcher = self.launcher(spawn=lambda *a, **k: self.fail("not here"), check=lambda argv: [])
        launcher.start = lambda sketch, values, replay=None: self.started.append((sketch, values)) or {"started": True, "run": None}
        self.server = serve(self.runs, port=0, cache=self.cache, project=self.project, launcher=launcher, secret=SECRET)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def call(self, path: str, body=None, headers: dict | None = None, method: str | None = None) -> tuple[int, dict | str]:
        data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
        request = urllib.request.Request(self.base + path, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                text = response.read().decode()
                return response.status, json.loads(text) if text.startswith(("{", "[")) else text
        except urllib.error.HTTPError as error:
            text = error.read().decode()
            return error.code, json.loads(text) if text.startswith(("{", "[")) else text

    def test_the_sketch_list_is_open_to_read(self):
        status, body = self.call("/api/sketches")
        self.assertEqual((status, body[0]["file"]), (200, "plain.yaml"))

    def test_a_post_without_the_secret_or_with_a_wrong_one_is_401_and_starts_nothing(self):
        began = time.monotonic()
        self.assertEqual(self.call("/api/start", {"sketch": "plain.yaml", "with": {}})[0], 401)
        self.assertEqual(self.call("/api/start", {"sketch": "plain.yaml", "with": {}}, {"X-Understudy-Secret": "wrong"})[0], 401)
        self.assertGreaterEqual(time.monotonic() - began, 1.0)  # a failed guess costs a pause
        self.assertEqual(self.started, [])

    def test_the_right_secret_starts_the_sketch_with_the_values_given(self):
        request = {"sketch": "plain.yaml", "with": {"file": "data/in.csv"}}
        status, body = self.call("/api/start", request, {"X-Understudy-Secret": SECRET})
        self.assertEqual((status, body["started"]), (200, True))
        self.assertEqual(self.started, [("plain.yaml", {"file": "data/in.csv"})])

    def test_a_request_from_another_origin_is_403_even_with_the_secret(self):
        headers = {"X-Understudy-Secret": SECRET, "Origin": "http://evil.example"}
        self.assertEqual(self.call("/api/start", {"sketch": "plain.yaml", "with": {}}, headers)[0], 403)
        self.assertEqual(self.started, [])

    def test_a_body_over_eight_kilobytes_is_413_and_bad_json_is_400(self):
        headers = {"X-Understudy-Secret": SECRET}
        self.assertEqual(self.call("/api/start", b"x" * 9000, headers)[0], 413)
        self.assertEqual(self.call("/api/start", b"{not json", headers)[0], 400)
        self.assertEqual(self.call("/api/start", b"[1, 2]", headers)[0], 400)

    def test_methods_other_than_get_and_post_are_refused_and_unknown_posts_are_404(self):
        headers = {"X-Understudy-Secret": SECRET}
        self.assertEqual(self.call("/api/start", None, headers, method="DELETE")[0], 501)
        self.assertEqual(self.call("/api/nothing", {"a": 1}, headers)[0], 404)

    def test_the_session_route_says_whether_there_are_controls_and_whether_this_caller_may_use_them(self):
        self.assertEqual(self.call("/api/session")[1], {"controls": True, "authorized": False})
        self.assertEqual(self.call("/api/session", None, {"X-Understudy-Secret": SECRET})[1], {"controls": True, "authorized": True})


class EndToEndTest(LauncherCase):
    """One real run: the coffee sketch, replayed from the committed capture, started by the console and finished."""

    def test_the_console_starts_a_real_run_that_finishes_and_lands_in_the_folder_it_watches(self):
        shutil.copytree(COFFEE, self.sketches / "coffee", ignore=shutil.ignore_patterns("replay"))
        shutil.copytree(COFFEE / "replay", self.cache / "run-20261030T000000-abcdef12")
        launcher = self.launcher()
        entries = {each["file"]: each for each in launcher.list_sketches()}
        self.assertTrue(entries["coffee/coffee_week.yaml"]["ok"])
        result = launcher.start("coffee/coffee_week.yaml", {}, replay="run-20261030T000000-abcdef12")
        self.assertTrue(result["started"])
        deadline = time.monotonic() + 60
        def finished() -> bool:
            events = [run / "events.jsonl" for run in self.runs.iterdir()]
            return any(each.is_file() and "run_finished" in each.read_text() for each in events)

        while time.monotonic() < deadline and not finished():
            time.sleep(0.3)
        (run,) = list(self.runs.iterdir())
        self.assertEqual(json.loads((run / "run.json").read_text())["status"], "complete")
        self.assertTrue((run / "ingredients.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
