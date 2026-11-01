"""The dashboard server: the printed lines, gauges and tube from a run's files, and the HTTP routes."""

import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from src.dashboard.server import describe, follow, gauges_of, list_runs, printed, read_events, serve

EVENTS = [
    {"event": "run_started", "at": "2026-10-31T01:00:00+00:00", "sketch": "examples/x/coffee.yaml", "mode": "live"},
    {"event": "stage_started", "at": "2026-10-31T01:00:01+00:00", "stage": "read"},
    {"event": "stage_completed", "at": "2026-10-31T01:00:11+00:00", "stage": "read"},
    {"event": "stage_failed", "at": "2026-10-31T01:00:12+00:00", "stage": "write", "reason": "boom"},
    {"event": "run_finished", "at": "2026-10-31T01:00:30+00:00", "outcome": "complete"},
]


def make_run(root: Path, name: str = "run-20261031T010000-aa11bb22", events=EVENTS, finished: bool = True) -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "events.jsonl").write_text("".join(json.dumps(each) + "\n" for each in events), encoding="utf-8")
    status = "complete" if finished else "running"
    stages = {"read": "complete", "write": "failed"}
    (directory / "run.json").write_text(json.dumps({"status": status, "stages": stages, "mode": "live"}))
    (directory / "summary.json").write_text(json.dumps({"jev_requests": 250}))
    return directory


class PrintedTest(unittest.TestCase):
    def test_each_event_prints_a_line_with_its_clock(self):
        self.assertEqual(printed(EVENTS[0])["text"], "01:00:00  === UNDERSTUDY RUN LOG ===  examples/x/coffee.yaml  (live)")
        self.assertEqual(printed(EVENTS[1])["text"], "01:00:01    start  read")
        self.assertEqual(printed(EVENTS[3]), {"text": "01:00:12    FAILED write: boom", "tone": "held"})
        self.assertEqual(printed(EVENTS[4])["text"], "01:00:30  === COMPLETE ===")

    def test_an_unknown_event_still_prints(self):
        self.assertEqual(printed({"event": "novelty"})["text"], "  novelty")


class DescribeTest(unittest.TestCase):
    def test_the_gauges_are_real_readings(self):
        with tempfile.TemporaryDirectory() as folder:
            run = describe(make_run(Path(folder)))
        gauges = {each["name"]: each for each in run["gauges"]}
        self.assertEqual((gauges["STAGES"]["text"], gauges["STAGES"]["level"]), ("1/2", 0.5))
        self.assertEqual(gauges["FAILED"]["text"], "1")
        self.assertEqual((gauges["JEV"]["text"], gauges["JEV"]["level"]), ("250", 0.25))
        self.assertEqual(gauges["ELAPSED"]["text"], "30s")
        self.assertEqual(run["tube"], [{"name": "read", "state": "complete"}, {"name": "write", "state": "failed"}])
        self.assertEqual((run["sketch"], run["status"], run["count"]), ("coffee", "complete", 5))

    def test_a_run_with_no_files_reads_as_empty_gauges(self):
        self.assertEqual([each["level"] for each in gauges_of({}, {}, [])], [0, 0, 0, 0])

    def test_a_half_written_last_line_waits_for_the_next_read(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = make_run(Path(folder))
            with (directory / "events.jsonl").open("a") as events:
                events.write('{"event": "stage_sta')
            self.assertEqual(len(read_events(directory)), 5)

    def test_runs_are_listed_newest_first_and_other_folders_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            make_run(root, "run-20261030T000000-aaaaaaaa")
            make_run(root, "run-20261031T000000-bbbbbbbb", finished=False)
            (root / "notes").mkdir()
            runs = list_runs(root)
        self.assertEqual([each["id"] for each in runs], ["run-20261031T000000-bbbbbbbb", "run-20261030T000000-aaaaaaaa"])
        self.assertEqual(runs[0]["status"], "running")
        self.assertEqual(list_runs(root / "missing"), [])


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        make_run(self.root)
        self.server = serve(self.root, port=0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def get(self, path: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=5) as response:
                return response.status, response.read().decode(errors="replace")
        except urllib.error.HTTPError as error:
            return error.code, ""

    def test_the_page_and_its_files_are_served(self):
        self.assertIn("OPERATIONS CONSOLE", self.get("/")[1])
        self.assertEqual(self.get("/page.js")[0], 200)
        self.assertEqual(self.get("/theme-starship.css")[0], 200)
        self.assertEqual(self.get("/fonts/cinzel-700.woff2")[0], 200)

    def test_the_browsers_favicon_request_is_answered_quietly(self):
        self.assertEqual(self.get("/favicon.ico")[0], 204)

    def test_the_api_lists_and_describes_runs(self):
        runs = json.loads(self.get("/api/runs")[1])
        self.assertEqual(runs[0]["sketch"], "coffee")
        self.assertEqual(json.loads(self.get(f"/api/runs/{runs[0]['id']}")[1])["count"], 5)

    def test_only_runs_and_listed_files_are_reachable(self):
        for path in ("/server.py", "/api/runs/../../etc", "/api/runs/run-nope", "/events/..%2Fx", "/fonts/../server.py"):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_a_finished_run_streams_its_lines_then_ends(self):
        _, body = self.get("/events/run-20261031T010000-aa11bb22")
        self.assertEqual(body.count("data: {"), 5 + 1)  # five lines and the end marker's empty object
        self.assertIn("event: end", body)


class StreamLimitTest(unittest.TestCase):
    """SEC-001: a run that never finishes must not hold a server thread forever, and watchers are capped."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.directory = make_run(self.root, "run-20261101T120000-00000000", EVENTS[:2], finished=False)

    def test_a_stream_with_no_new_line_for_the_idle_limit_ends(self):
        chunks = b"".join(follow(self.directory, poll_seconds=0.01, idle_seconds=0.1))
        self.assertIn(b"event: end", chunks)

    def test_a_stream_that_keeps_getting_lines_does_not_idle_out(self):
        stream = follow(self.directory, poll_seconds=0.01, idle_seconds=0.3)
        next(stream)
        with (self.directory / "events.jsonl").open("a") as events:
            events.write(json.dumps({"event": "stage_started", "at": "2026-11-01T12:00:03+00:00", "stage": "more"}) + "\n")
        chunks = [next(stream) for _ in range(3)]
        self.assertTrue(any(b"more" in each for each in chunks))
        stream.close()

    def test_watchers_beyond_the_cap_are_refused_with_503_and_a_freed_place_is_reused(self):
        server = serve(self.root, port=0, max_streams=2)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]

        def open_stream() -> socket.socket:
            sock = socket.create_connection(("127.0.0.1", port), timeout=5)
            sock.sendall(b"GET /events/run-20261101T120000-00000000 HTTP/1.0\r\n\r\n")
            return sock

        first, second = open_stream(), open_stream()
        self.assertIn(b"200", first.recv(64))
        self.assertIn(b"200", second.recv(64))
        third = open_stream()
        self.assertIn(b"503", third.recv(64))
        third.close()
        first.close()
        deadline = time.monotonic() + 5
        status = b""
        while b"200" not in status and time.monotonic() < deadline:
            fourth = open_stream()
            status = fourth.recv(64)
            fourth.close()
            time.sleep(0.1)
        self.assertIn(b"200", status)
        second.close()


class SecurityHeadersTest(unittest.TestCase):
    """SEC-003: every response carries the browser security headers."""

    def test_pages_api_and_errors_carry_the_headers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            make_run(root)
            server = serve(root, port=0)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            base = f"http://127.0.0.1:{server.server_address[1]}"
            for path in ("/", "/api/runs", "/page.js", "/nope"):
                try:
                    response = urllib.request.urlopen(base + path, timeout=5)
                    headers = response.headers
                    response.close()
                except urllib.error.HTTPError as error:
                    headers = error.headers
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff", path)
                self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"], path)
                self.assertIn("default-src 'self'", headers["Content-Security-Policy"], path)
                self.assertEqual(headers["Referrer-Policy"], "no-referrer", path)


if __name__ == "__main__":
    unittest.main()
