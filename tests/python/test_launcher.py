"""UND-79: the console starts, replays and stops runs, behind one secret, and only what it should."""

import contextlib
import io
import json
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from src.dashboard.runs import Launcher, Refused, _Child
from src.dashboard.server import announce, serve
from src.dashboard.view import describe
from src.paths import ROOT

COFFEE = ROOT / "tests" / "fixtures" / "coffee"
PLAIN = """name: plain
description: >
  Reads a file and says hello.
stage:
  data: { kind: file, path: "{{ file }}" }
scene:
  initial: only
  beats:
    only: { final: true }
"""
PARENT = """name: parent
description: calls a child
scene:
  initial: ask
  beats:
    ask: { do: { play: child.yaml }, to: done }
    done: { final: true }
"""
CHILD = "name: child\ndescription: only called, never run on its own\nscene: { initial: x, beats: { x: { final: true } } }\n"


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
    def test_the_list_shows_each_play_with_its_description_the_names_it_takes_and_the_files_it_reads(self):
        self.write("plain.yaml", PLAIN)
        (entry,) = self.launcher().list_sketches()
        self.assertEqual((entry["file"], entry["name"], entry["ok"]), ("plain.yaml", "plain", True))
        self.assertEqual(entry["description"], "Reads a file and says hello.")
        self.assertEqual(entry["with"], ["data", "file"])  # `data` is the stage file; `file` the name its path uses

    def test_a_sketch_that_is_only_called_by_another_is_not_offered(self):
        self.write("parent.yaml", PARENT)
        self.write("child.yaml", CHILD)
        self.assertEqual([each["file"] for each in self.launcher().list_sketches()], ["parent.yaml"])

    def test_a_symlink_that_leaves_the_folder_is_not_listed_at_all(self):
        (self.project / "outside.yaml").write_text(PLAIN)
        (self.sketches / "plain.yaml").write_text(PLAIN)
        (self.sketches / "link.yaml").symlink_to(self.project / "outside.yaml")
        self.assertEqual([each["file"] for each in self.launcher().list_sketches()], ["plain.yaml"])

    def test_a_file_that_cannot_be_read_is_listed_greyed_out_with_the_reason(self):
        self.write("broken.yaml", "name: broken\nmachine: [unclosed\n")
        (entry,) = self.launcher().list_sketches()
        self.assertFalse(entry["ok"])
        self.assertTrue(entry["problem"])

    def test_sketches_in_a_subfolder_are_listed_with_their_folder(self):
        self.write("more/plain.yaml", PLAIN)
        self.assertEqual([each["file"] for each in self.launcher().list_sketches()], ["more/plain.yaml"])

    def test_the_plan_of_a_listed_play_is_its_pieces_and_beats_laid_out(self):
        self.write("plain.yaml", PLAIN)
        found = self.launcher().plan("plain.yaml")
        self.assertEqual({each["id"] for each in found["nodes"]}, {"data", "only"})
        self.assertTrue(all("x" in each and "kind" in each for each in found["nodes"]))

    def test_a_play_that_is_not_listed_has_no_plan(self):
        self.write("parent.yaml", PARENT)
        self.write("child.yaml", CHILD)
        for name in ("child.yaml", "../outside.yaml", "missing.yaml"):
            with self.assertRaises(Refused) as caught:
                self.launcher().plan(name)
            self.assertEqual(caught.exception.status, 403, name)

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

    def test_started_held_the_child_is_told_to_pause_and_that_a_console_steps_it(self):
        result = self.launcher_.start("plain.yaml", {}, hold=True)
        self.assertTrue(result["started"])
        (process,) = self.processes
        self.assertIn("--pause", process.argv)
        self.assertIn("--by-console", process.argv)
        self.assertNotIn("--stop-at", process.argv)

    def test_a_start_not_held_passes_no_hold_flags(self):
        self.launcher_.start("plain.yaml", {})
        (process,) = self.processes
        for flag in ("--pause", "--stop-at", "--by-console"):
            self.assertNotIn(flag, process.argv)

    def test_held_before_a_beat_the_child_is_told_which(self):
        self.write("parent.yaml", PARENT)
        self.write("child.yaml", CHILD)
        self.launcher_.start("parent.yaml", {}, hold_at="ask")
        (process,) = self.processes
        self.assertEqual(process.argv[process.argv.index("--stop-at") + 1], "ask")
        self.assertIn("--by-console", process.argv)

    def test_a_beat_that_is_not_in_the_flow_or_is_final_is_refused_with_the_beats_there_are_and_nothing_starts(self):
        self.write("parent.yaml", PARENT)
        self.write("child.yaml", CHILD)
        for beat in ("nowhere", "done", "x"):
            with self.assertRaises(Refused) as caught:
                self.launcher_.start("parent.yaml", {}, hold_at=beat)
            self.assertEqual(caught.exception.status, 400)
            self.assertIn("ask", caught.exception.message)
        self.assertEqual(self.processes, [])

    def test_hold_must_be_yes_or_no_and_a_beat_a_name_and_not_both(self):
        self.write("parent.yaml", PARENT)
        self.write("child.yaml", CHILD)
        for options in ({"hold": "yes"}, {"hold_at": 3}, {"hold": True, "hold_at": "ask"}):
            with self.assertRaises(Refused) as caught:
                self.launcher_.start("parent.yaml", {}, **options)
            self.assertEqual(caught.exception.status, 400, options)
        self.assertEqual(self.processes, [])

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
        self.assertEqual(self.launcher_.replays(), [{"id": "run-20261030T000000-abcdef12", "play": ""}])  # no run folder: no play name

    def test_a_captured_run_is_offered_with_the_name_of_the_play_that_made_it(self):
        (self.cache / "run-20261030T000000-abcdef12").mkdir()
        run = self.runs / "run-20261030T000000-abcdef12"
        run.mkdir()
        (run / "run.json").write_text(json.dumps({"status": "complete", "beats": {}, "play": "evening"}), encoding="utf-8")
        self.assertEqual(self.launcher_.replays(), [{"id": "run-20261030T000000-abcdef12", "play": "evening"}])

    def test_each_file_a_play_reads_says_what_to_do_when_it_is_left_empty(self):
        entry = next(each for each in self.launcher().list_sketches() if each["file"] == "plain.yaml")
        # its path is a template value, empty until one is given
        self.assertEqual(entry["files"], {"data": {"default": "", "optional": False}})

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
        (run / "run.json").write_text(json.dumps({"status": "running", "beats": {}}))

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


class RealStopTest(LauncherCase):
    """Stop against a real process: it is ended, its whole group with it, and its run is marked stopped."""

    def test_stop_ends_a_real_long_running_process_and_marks_the_run_stopped(self):
        self.write("plain.yaml", PLAIN)
        run = self.runs / "run-20261101T100000-bbbbbbbb"
        run.mkdir()
        (run / "run.json").write_text(json.dumps({"status": "running", "beats": {}}))

        def sleeper(argv, **options):
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = self.launcher(spawn=sleeper, check=lambda argv: [], find_run=lambda sketch, before: run.name)
        launcher.start("plain.yaml", {"file": "data/in.csv"})
        child = launcher._children["plain.yaml"]["child"]
        self.assertIsNone(child.poll())
        launcher.stop(run.name)
        self.assertIsNotNone(child.poll())
        self.assertEqual(json.loads((run / "run.json").read_text())["status"], "stopped")
        launcher.start("plain.yaml", {"file": "data/in.csv"})  # the sketch is free to run again
        launcher.stop(run.name)

    def test_a_run_stopped_before_its_first_stage_finished_has_no_run_json_yet_and_still_reads_stopped(self):
        self.write("plain.yaml", PLAIN)
        run = self.runs / "run-20261101T100000-cccccccc"
        run.mkdir()  # the run made its folder and its first event, and nothing else
        (run / "events.jsonl").write_text(json.dumps({"event": "run_started", "at": "2026-11-01T10:00:00+00:00",
                                                      "play": "plain.yaml"}) + "\n")

        def sleeper(argv, **options):
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = self.launcher(spawn=sleeper, check=lambda argv: [], find_run=lambda sketch, before: run.name)
        launcher.start("plain.yaml", {"file": "data/in.csv"})
        launcher.stop(run.name)
        self.assertEqual(describe(run)["state"], "stopped")


class HttpTest(LauncherCase):
    """The routes: reads and starts are open (there is no login); every POST needs a same-origin request and a small JSON body."""

    def setUp(self):
        super().setUp()
        self.write("plain.yaml", PLAIN)
        self.started: list[tuple[str, dict]] = []
        launcher = self.launcher(spawn=lambda *a, **k: self.fail("not here"), check=lambda argv: [])
        self.hold_choices: list[tuple] = []
        launcher.start = lambda sketch, values, replay=None, hold=False, hold_at=None: (
            self.started.append((sketch, values)) or self.hold_choices.append((hold, hold_at)) or {"started": True, "run": None})
        self.server = serve(self.runs, port=0, cache=self.cache, project=self.project, launcher=launcher)
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

    def test_a_client_that_hangs_up_before_its_answer_leaves_no_traceback_behind(self):
        noise = io.StringIO()
        with contextlib.redirect_stderr(noise):
            sock = socket.create_connection(("127.0.0.1", self.server.server_address[1]), timeout=5)
            sock.sendall(b"POST /api/start HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n{}")  # a start of nothing: refused at once
            sock.close()
            time.sleep(0.4)  # long enough for the answer to find the hung-up client
        self.assertNotIn("Traceback", noise.getvalue())

    def test_the_sketch_list_is_open_to_read(self):
        status, body = self.call("/api/sketches")
        self.assertEqual((status, body[0]["file"]), (200, "plain.yaml"))

    def test_the_plan_of_a_listed_play_is_open_to_read_and_an_unlisted_one_is_refused(self):
        status, body = self.call("/api/plan?play=plain.yaml")
        self.assertEqual((status, {each["id"] for each in body["nodes"]}), (200, {"data", "only"}))
        status, body = self.call("/api/plan?play=..%2Fnope.yaml")
        self.assertEqual(status, 403)
        self.assertIn("problem", body)
        self.assertEqual(self.call("/api/plan")[0], 400)

    def test_the_hold_choice_in_a_start_request_reaches_the_launcher(self):
        self.call("/api/start", {"sketch": "plain.yaml", "with": {}, "hold": True})
        self.call("/api/start", {"sketch": "plain.yaml", "with": {}, "hold_at": "only"})
        self.call("/api/start", {"sketch": "plain.yaml", "with": {}})
        self.assertEqual(self.hold_choices, [(True, None), (False, "only"), (False, None)])

    def test_a_start_with_no_login_starts_the_sketch_with_the_values_given(self):
        request = {"sketch": "plain.yaml", "with": {"file": "data/in.csv"}}
        status, body = self.call("/api/start", request)
        self.assertEqual((status, body["started"]), (200, True))
        self.assertEqual(self.started, [("plain.yaml", {"file": "data/in.csv"})])

    def test_a_request_from_another_origin_is_403(self):
        self.assertEqual(self.call("/api/start", {"sketch": "plain.yaml", "with": {}}, {"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.started, [])

    def test_a_body_over_eight_kilobytes_is_413_and_bad_json_is_400(self):
        self.assertEqual(self.call("/api/start", b"x" * 9000)[0], 413)
        self.assertEqual(self.call("/api/start", b"{not json")[0], 400)
        self.assertEqual(self.call("/api/start", b"[1, 2]")[0], 400)

    def test_a_negative_or_unreadable_content_length_is_400_not_a_wait_for_more_data(self):
        for length in ("-1", "abc", "1.5"):
            with socket.create_connection(("127.0.0.1", self.server.server_address[1]), timeout=5) as sock:
                sock.sendall((f"POST /api/start HTTP/1.1\r\nHost: x\r\n"
                              f"Content-Length: {length}\r\n\r\n").encode())
                self.assertIn(b" 400 ", sock.recv(100), length)

    def test_methods_other_than_get_and_post_are_refused_and_unknown_posts_are_404(self):
        self.assertEqual(self.call("/api/start", None, method="DELETE")[0], 501)
        self.assertEqual(self.call("/api/nothing", {"a": 1})[0], 404)

    def test_the_session_route_says_whether_there_are_controls(self):
        self.assertEqual(self.call("/api/session")[1], {"controls": True, "holdable": False})


class AnnounceTest(unittest.TestCase):
    """The console says where it is, and nothing about a login (there is none)."""

    class Output:
        def __init__(self):
            self.text, self.flushed = "", 0

        def write(self, text):
            self.text += text

        def flush(self):
            self.flushed += 1

    def test_the_address_is_written_and_flushed_so_a_pipe_or_log_shows_it(self):
        shown = self.Output()
        announce(shown, Path("build/runs"), 4180)
        self.assertIn("0.0.0.0:4180", shown.text)
        self.assertNotIn("secret", shown.text)
        self.assertEqual(shown.flushed, 1)


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


class HoldsTest(LauncherCase):
    def test_a_launcher_holds_only_the_runs_it_started_and_still_has_going(self):
        self.write("plain.yaml", PLAIN)
        run = self.runs / "run-20261101T100000-eeeeeeee"
        run.mkdir()

        def sleeper(argv, **options):
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = self.launcher(spawn=sleeper, check=lambda argv: [], find_run=lambda sketch, before: run.name)
        self.assertFalse(launcher.holds(run.name))
        launcher.start("plain.yaml", {"file": "data/in.csv"})
        self.assertTrue(launcher.holds(run.name))
        self.assertFalse(launcher.holds("run-20261101T100000-ffffffff"))
        launcher.stop(run.name)
        self.assertFalse(launcher.holds(run.name))
