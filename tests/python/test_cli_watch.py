"""UND-83: `understudy run --watch [--pause]` opens a console on one run, bound to this machine, and can hold it."""

import io
import json
import re
import socket
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from test_sketch_run import RunCase, library

from src.dashboard import server as dashboard_server
from src.dashboard import watch as watch_module
from src.play.cli import main

ADDRESS = re.compile(r"http://127\.0\.0\.1:(\d+)")
WAIT = 20  # seconds a test waits for the run to reach a state
HELD_AGAIN = 2  # pauses in the log once the run has made one move and been held again


class WatchCase(RunCase):
    def setUp(self):
        super().setUp()
        self.secret_file = self.dir / "secret"
        patcher = patch.object(watch_module, "SECRET_FILE", self.secret_file)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.out_text, self.err_text = io.StringIO(), io.StringIO()

    def argv(self, *extra):
        return ["run", str(self.sketch()), "--out", str(self.out), *extra]

    def run_main(self, *extra) -> int:
        return main(self.argv(*extra), library=library(), stdout=self.out_text, stderr=self.err_text, hold_open=lambda: None)


class RefusalTests(WatchCase):
    def test_pause_without_watch_is_refused_before_anything_starts(self):
        self.assertEqual(self.run_main("--pause"), 2)
        self.assertEqual(self.err_text.getvalue(), "understudy: --pause needs --watch\n")
        self.assertFalse(self.out.exists())

    def test_a_port_already_in_use_is_one_line_and_no_run_starts(self):
        with socket.socket() as busy:
            busy.bind(("127.0.0.1", 0))
            busy.listen()
            port = busy.getsockname()[1]
            self.assertEqual(self.run_main("--watch", "--port", str(port)), 2)
        self.assertIn(f"port {port} is already in use", self.err_text.getvalue())
        self.assertFalse(self.out.exists())


class SecretFileTests(unittest.TestCase):
    def test_a_watched_run_keeps_its_secret_apart_from_a_running_dashboards(self):
        # one file for both would overwrite the dashboard's secret and lock its owner out of it
        self.assertNotEqual(Path(watch_module.SECRET_FILE).name, Path(dashboard_server.SECRET_FILE).name)
        self.assertEqual(Path(watch_module.SECRET_FILE).parent, Path(dashboard_server.SECRET_FILE).parent)


class WatchTests(WatchCase):
    def test_a_watched_run_prints_where_to_look_and_where_the_secret_is_and_never_the_secret(self):
        self.assertEqual(self.run_main("--watch"), 0)
        text = self.out_text.getvalue()
        self.assertRegex(text, ADDRESS)
        self.assertIn(str(self.secret_file), text)
        self.assertNotIn(self.secret_file.read_text(encoding="utf-8").strip(), text)
        self.assertEqual(oct(self.secret_file.stat().st_mode & 0o777), "0o600")

    def test_the_console_binds_this_machine_only(self):
        seen = {}
        original = watch_module.serve

        def spy(root, port=0, host="0.0.0.0", **options):
            seen["host"] = host
            return original(root, port, host=host, **options)

        with patch.object(watch_module, "serve", spy):
            self.run_main("--watch")
        self.assertEqual(seen["host"], "127.0.0.1")

    def test_a_run_started_held_is_stepped_and_resumed_from_the_console(self):
        result = {}
        thread = threading.Thread(target=lambda: result.setdefault("code", self.run_main("--watch", "--pause")))
        thread.start()
        base = self.address()
        headers = {"X-Understudy-Secret": self.secret_file.read_text(encoding="utf-8").strip(), "Content-Type": "application/json"}
        run = self.until(lambda: self.runs(base) and self.runs(base)[0]["state"] == "paused", base)[0]["id"]
        self.assertEqual(self.post(base, "step", run, headers)["steps"], 1)
        self.until(lambda: self.events(run).count("paused") == HELD_AGAIN, base)
        self.assertEqual(self.events(run).count("beat_started"), 1)  # exactly one move
        self.assertEqual(self.post(base, "resume", run, headers)["mode"], "run")
        thread.join(WAIT)
        self.assertEqual(result["code"], 0)
        self.assertEqual(self.events(run)[-1], "run_finished")

    def test_the_console_may_hold_only_the_run_it_watches(self):
        thread = threading.Thread(target=lambda: self.run_main("--watch", "--pause"))
        thread.start()
        base = self.address()
        headers = {"X-Understudy-Secret": self.secret_file.read_text(encoding="utf-8").strip(), "Content-Type": "application/json"}
        run = self.until(lambda: self.runs(base) and self.runs(base)[0]["state"] == "paused", base)[0]["id"]
        other = self.out / "run-20260101T000000-aaaaaaaa"
        other.mkdir()
        body = json.dumps({"run": other.name}).encode()
        request = urllib.request.Request(f"{base}/api/pause", data=body, headers=headers, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(request, timeout=10)
        self.assertEqual(refused.exception.code, 404)
        self.post(base, "resume", run, headers)
        thread.join(WAIT)

    # -- helpers ----------------------------------------------------------------------------------------------

    def address(self) -> str:
        deadline = time.monotonic() + WAIT
        while time.monotonic() < deadline:
            found = ADDRESS.search(self.out_text.getvalue())
            if found:
                return found.group(0)
            time.sleep(0.02)
        raise AssertionError("no address printed")

    def runs(self, base: str):
        with urllib.request.urlopen(f"{base}/api/runs", timeout=10) as response:
            return json.loads(response.read().decode())

    def until(self, condition, base):
        deadline = time.monotonic() + WAIT
        while time.monotonic() < deadline:
            try:
                if condition():
                    return self.runs(base)
            except OSError:
                pass
            time.sleep(0.02)
        raise AssertionError("the run never reached the state")

    def events(self, run: str) -> list[str]:
        path = Path(self.out) / run / "events.jsonl"
        return [json.loads(line)["event"] for line in path.read_text(encoding="utf-8").splitlines()]

    def post(self, base: str, action: str, run: str, headers: dict) -> dict:
        body = json.dumps({"run": run}).encode()
        request = urllib.request.Request(f"{base}/api/{action}", data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())
