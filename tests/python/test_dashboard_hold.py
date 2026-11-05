"""UND-83: the console shows a held run as paused, and holds, steps and resumes the runs it may control."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from src.dashboard import server as server_module
from src.dashboard.hold import apply_hold
from src.dashboard.runs import Refused
from src.dashboard.server import serve
from src.dashboard.view import describe, list_runs
from src.play.control import read_control, write_control

RUN = "run-20261103T100000-aaaaaaaa"
SECRET = "s3cret-for-tests"
NOW = datetime(2026, 11, 3, 10, 30, tzinfo=UTC)
STARTED = {"event": "run_started", "play": "x/plain.yaml", "mode": "live",
           "beats": [{"name": "a", "final": False}, {"name": "done", "final": True}],
           "transitions": [{"from": "a", "to": "done", "event": "ok"}], "initial": "a"}


def write_run(root: Path, events: list[dict], run_id: str = RUN, status: str = "running") -> Path:
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=True)
    stamp = (NOW - timedelta(seconds=len(events))).isoformat()
    lines = [{"at": (datetime.fromisoformat(stamp) + timedelta(seconds=n)).isoformat(), **event} for n, event in enumerate(events)]
    (folder / "events.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    (folder / "run.json").write_text(json.dumps({"status": status, "beats": {}, "play": "plain"}), encoding="utf-8")
    return folder


class HeldViewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_a_run_whose_last_event_is_a_pause_reads_paused_before_the_stage(self):
        folder = write_run(self.root, [STARTED, {"event": "beat_entered", "beat": "a", "caused_by": "start"},
                                       {"event": "paused", "beat": "a"}])
        shown = describe(folder, NOW)
        self.assertEqual((shown["state"], shown["ended"]), ("paused", "paused before a"))
        self.assertEqual(shown["hold"], {"stage": "a"})

    def test_a_resumed_run_reads_running_again_and_has_no_hold(self):
        folder = write_run(self.root, [STARTED, {"event": "paused", "beat": "a"}, {"event": "resumed", "beat": "a"},
                                       {"event": "beat_started", "beat": "a"}])
        shown = describe(folder, NOW)
        self.assertEqual((shown["state"], shown["hold"]), ("running", None))

    def test_a_run_held_for_hours_is_paused_not_stalled(self):
        folder = write_run(self.root, [STARTED, {"event": "paused", "beat": "a"}])
        self.assertEqual(describe(folder, NOW + timedelta(hours=5))["state"], "paused")

    def test_the_rack_tab_of_a_held_run_says_paused(self):
        write_run(self.root, [STARTED, {"event": "paused", "beat": "a"}])
        self.assertEqual([each["state"] for each in list_runs(self.root, NOW)], ["paused"])

    def test_a_finished_run_is_never_paused_even_if_its_last_pause_is_old(self):
        folder = write_run(self.root, [STARTED, {"event": "paused", "beat": "a"}, {"event": "resumed", "beat": "a"},
                                       {"event": "run_finished", "outcome": "complete"}], status="complete")
        self.assertEqual(describe(folder, NOW)["state"], "done")


class ApplyHoldTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.folder = write_run(self.root, [STARTED])

    def test_pause_holds_step_adds_one_and_resume_runs_and_the_step_count_is_kept(self):
        self.assertEqual(apply_hold(self.root, RUN, "pause"), {"run": RUN, "mode": "hold", "steps": 0})
        self.assertEqual(apply_hold(self.root, RUN, "step"), {"run": RUN, "mode": "hold", "steps": 1})
        self.assertEqual(apply_hold(self.root, RUN, "resume"), {"run": RUN, "mode": "run", "steps": 1})
        self.assertEqual(apply_hold(self.root, RUN, "pause"), {"run": RUN, "mode": "hold", "steps": 1})
        self.assertEqual(read_control(self.folder), {"mode": "hold", "steps": 1})

    def test_step_on_a_run_that_is_not_held_holds_it_after_one_more_stage(self):
        self.assertEqual(apply_hold(self.root, RUN, "step"), {"run": RUN, "mode": "hold", "steps": 1})

    def test_a_bad_control_file_is_replaced_not_trusted(self):
        (self.folder / "control.json").write_text("junk", encoding="utf-8")
        self.assertEqual(apply_hold(self.root, RUN, "step")["steps"], 1)

    def test_an_id_that_is_not_a_run_or_a_run_that_is_not_there_is_refused_with_404(self):
        for run_id in ("../etc", "run-1/../../x", "nothing", "run-20261103T100000-bbbbbbbb", ""):
            with self.assertRaises(Refused) as refused:
                apply_hold(self.root, run_id, "pause")
            self.assertEqual(refused.exception.status, 404, run_id)

    def test_an_action_that_is_not_one_of_the_three_is_refused(self):
        with self.assertRaises(Refused) as refused:
            apply_hold(self.root, RUN, "explode")
        self.assertEqual(refused.exception.status, 400)

    def test_a_folder_that_is_a_link_out_of_the_runs_folder_is_refused(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (self.root / "run-20261103T100000-cccccccc").symlink_to(outside.name)
        with self.assertRaises(Refused):
            apply_hold(self.root, "run-20261103T100000-cccccccc", "pause")
        self.assertEqual(list(Path(outside.name).iterdir()), [])

    def test_a_run_that_has_finished_cannot_be_held(self):
        write_control(self.folder, "run", 0)
        finished = write_run(self.root, [STARTED, {"event": "run_finished", "outcome": "complete"}],
                             run_id="run-20261103T100000-dddddddd", status="complete")
        with self.assertRaises(Refused) as refused:
            apply_hold(self.root, finished.name, "pause")
        self.assertEqual(refused.exception.status, 409)
        self.assertFalse((finished / "control.json").exists())


class HoldHttpTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.folder = write_run(self.root, [STARTED])
        patcher = patch.object(server_module, "WRONG_SECRET_PAUSE", 0)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.allowed = {RUN}
        self.server = serve(self.root, port=0, secret=SECRET, controllable=lambda run: run in self.allowed)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def call(self, path: str, body=None, headers: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, headers=headers or {}, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode() or "{}")

    def secret(self):
        return {"X-Understudy-Secret": SECRET}

    def test_the_session_says_a_console_that_can_hold_runs_can(self):
        self.assertEqual(self.call("/api/session")[1], {"controls": False, "holdable": True, "authorized": False})

    def test_pause_step_and_resume_write_the_control_for_a_run_the_console_may_control(self):
        self.assertEqual(self.call("/api/pause", {"run": RUN}, self.secret())[1]["mode"], "hold")
        self.assertEqual(read_control(self.folder), {"mode": "hold", "steps": 0})
        self.assertEqual(self.call("/api/step", {"run": RUN}, self.secret())[1]["steps"], 1)
        self.assertEqual(self.call("/api/resume", {"run": RUN}, self.secret())[1]["mode"], "run")

    def test_no_secret_or_another_origin_changes_nothing(self):
        self.assertEqual(self.call("/api/pause", {"run": RUN})[0], 401)
        self.assertEqual(self.call("/api/pause", {"run": RUN}, {**self.secret(), "Origin": "http://evil.example"})[0], 403)
        self.assertFalse((self.folder / "control.json").exists())

    def test_a_run_the_console_did_not_start_is_refused_with_a_plain_message(self):
        self.allowed = set()
        status, body = self.call("/api/pause", {"run": RUN}, self.secret())
        self.assertEqual((status, body["problem"]), (404, "that run was not started by this console, or it has finished"))
        self.assertFalse((self.folder / "control.json").exists())

    def test_a_missing_or_wrong_run_field_is_400(self):
        self.assertEqual(self.call("/api/pause", {}, self.secret())[0], 400)
        self.assertEqual(self.call("/api/pause", {"run": 5}, self.secret())[0], 400)


class NoHoldConsoleTests(unittest.TestCase):
    def test_a_console_that_cannot_hold_runs_has_no_such_routes(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        server = serve(Path(directory.name), port=0, secret=SECRET)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        request = urllib.request.Request(f"http://127.0.0.1:{server.server_address[1]}/api/pause", data=b"{}", method="POST",
                                         headers={"X-Understudy-Secret": SECRET})
        with self.assertRaises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(request, timeout=10)
        self.assertEqual(refused.exception.code, 404)
