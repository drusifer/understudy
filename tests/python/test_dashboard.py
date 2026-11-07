"""The dashboard server: the printed lines, gauges and tube from a run's files, and the HTTP routes."""

import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from src.dashboard.server import follow, serve
from src.dashboard.view import describe, gauges_of, list_runs, printed, read_events

EVENTS = [
    {"event": "run_started", "at": "2026-10-31T01:00:00+00:00", "play": "examples/x/coffee.yaml", "mode": "live"},
    {"event": "beat_started", "at": "2026-10-31T01:00:01+00:00", "beat":"read"},
    {"event": "beat_completed", "at": "2026-10-31T01:00:11+00:00", "beat":"read"},
    {"event": "beat_failed", "at": "2026-10-31T01:00:12+00:00", "beat":"write", "reason": "boom"},
    {"event": "run_finished", "at": "2026-10-31T01:00:30+00:00", "outcome": "complete"},
]


def make_run(root: Path, name: str = "run-20261031T010000-aa11bb22", events=EVENTS, finished: bool = True) -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "events.jsonl").write_text("".join(json.dumps(each) + "\n" for each in events), encoding="utf-8")
    status = "complete" if finished else "running"
    stages = {"read": "complete", "write": "failed"}
    (directory / "run.json").write_text(json.dumps({"status": status, "beats":stages, "mode": "live"}))
    (directory / "summary.json").write_text(json.dumps({"jev_requests": 250}))
    return directory


class PrintedTest(unittest.TestCase):
    def test_each_event_prints_a_line_with_its_clock(self):
        self.assertEqual(printed(EVENTS[0])["text"], "01:00:00  === UNDERSTUDY RUN LOG ===  examples/x/coffee.yaml  (live)")
        self.assertEqual(printed(EVENTS[1])["text"], "01:00:01    start  read")
        self.assertEqual(printed(EVENTS[3]), {"text": "01:00:12    FAILED write: boom", "tone": "held", "stage": "write",
                                              "event": "beat_failed"})
        self.assertEqual(printed(EVENTS[0])["stage"], "")

    def test_a_run_lists_the_indices_of_its_failed_lines_for_the_jump_to_first_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            run = describe(make_run(Path(folder)))
        self.assertEqual(run["failures"], [3])
        self.assertEqual(run["lines"][3]["tone"], "held")
        self.assertEqual(printed(EVENTS[4])["text"], "01:00:30  === COMPLETE ===")

    def test_a_completed_beat_prints_what_it_did_read_and_made(self):
        said = {"event": "beat_completed", "at": "2026-10-31T01:00:11+00:00", "beat": "weighed", "action": "map.weigh",
                "read": {"joined": {"rows": 12, "keys": ["a"]}, "films": {"rows": 8, "keys": ["t"]}}, "wrote": {},
                "made": {"rows": 5, "keys": ["score"]}}
        self.assertEqual(printed(said)["text"], "01:00:11    done   weighed  map.weigh  in: joined 12, films 8  made 5 rows")
        wrote = {**said, "beat": "booker", "action": "write:booking", "read": {}, "made": None,
                 "wrote": {"booking": {"rows": 1, "keys": ["x"]}}}
        self.assertEqual(printed(wrote)["text"], "01:00:11    done   booker  write:booking  wrote booking 1 row")
        self.assertEqual(printed({"event": "beat_completed", "beat": "read"})["text"], "  done   read")  # an older log

    def test_a_move_a_hold_and_a_jev_answer_print_in_words(self):
        self.assertEqual(printed({"event": "beat_entered", "beat": "pick", "caused_by": "ok"})["text"], "  next   pick")
        self.assertEqual(printed({"event": "beat_entered", "beat": "x", "caused_by": "fail"})["text"], "  next   x  (after a failure)")
        self.assertEqual(printed({"event": "paused", "beat": "pick"})["text"], "  paused before pick")
        self.assertEqual(printed({"event": "resumed", "beat": "pick"})["text"], "  resumed pick")
        jev = {"event": "jev_read", "source": "pick", "top": "showing_9", "probability": 0.82, "next": "showing_3",
               "next_probability": 0.1, "options": 5}
        self.assertEqual(printed(jev)["text"], "  jev    pick: showing_9 0.82 (then showing_3 0.10; 5 options)")
        self.assertEqual(printed({**jev, "next": None, "options": 1})["text"], "  jev    pick: showing_9 0.82 (1 option)")

    def test_an_unknown_event_still_prints(self):
        self.assertEqual(printed({"event": "novelty"})["text"], "  novelty")


class DescribeTest(unittest.TestCase):
    def test_the_gauges_are_real_readings(self):
        with tempfile.TemporaryDirectory() as folder:
            run = describe(make_run(Path(folder)))
        gauges = {each["name"]: each for each in run["gauges"]}
        self.assertEqual((gauges["BEATS"]["text"], gauges["BEATS"]["level"]), ("1/2", 0.5))
        self.assertEqual(gauges["FAILED"]["text"], "1")
        self.assertEqual(gauges["FAILED"]["level"], 0.5)
        self.assertEqual((gauges["JEV"]["text"], gauges["JEV"]["level"]), ("250", None))  # no needle: no known full scale
        self.assertEqual((gauges["ELAPSED"]["text"], gauges["ELAPSED"]["level"]), ("30s", None))
        self.assertEqual(run["tube"], [{"name": "read", "state": "complete", "groups": []},
                                       {"name": "write", "state": "failed", "groups": []}])
        self.assertEqual((run["sketch"], run["state"], run["count"]), ("coffee", "done", 5))

    def test_a_run_with_no_files_reads_as_empty_gauges(self):
        self.assertEqual([each["level"] for each in gauges_of({}, [])], [0, 0, None, None])

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
            runs = list_runs(root, now=datetime.fromisoformat("2026-10-31T01:00:40+00:00"))
        self.assertEqual([each["id"] for each in runs], ["run-20261031T000000-bbbbbbbb", "run-20261030T000000-aaaaaaaa"])
        self.assertEqual(runs[0]["state"], "running")
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
        self.assertEqual(self.get("/controls.js")[0], 200)
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


def make_manifest(root: Path, name: str, manifest: dict, events=EVENTS, summary: dict | None = None) -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "events.jsonl").write_text("".join(json.dumps(each) + "\n" for each in events), encoding="utf-8")
    (directory / "run.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "summary.json").write_text(json.dumps(summary or {}), encoding="utf-8")
    return directory


class RunStateTest(unittest.TestCase):
    """UND-76: the console says plainly how a run went."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def test_a_finished_run_is_done_and_says_so_in_one_line_with_what_it_produced(self):
        manifest = {"status": "complete", "mode": "live", "outcome": "all_done", "with": {"mood": "calm"},
                    "beats":{"read": "complete", "write": "complete"}, "outputs": {"report.jsonl": 3}}
        run = describe(make_manifest(self.root, "run-20261101T100000-aaaaaaaa", manifest, summary={"stale": False}))
        self.assertEqual(run["state"], "done")
        self.assertEqual(run["ended"], "done after 2 beats, outcome all_done")
        self.assertEqual(run["summary"]["with"], {"mood": "calm"})
        self.assertEqual(run["summary"]["outputs"], {"report.jsonl": 3})
        self.assertEqual((run["summary"]["mode"], run["summary"]["stale"], run["summary"]["seconds"]), ("live", False, 30))
        self.assertIsNone(run["failure"])

    def test_a_failed_run_names_the_stage_the_reason_and_the_printed_line(self):
        manifest = {"status": "failed", "failed_beat": "write", "error": "boom", "beats":{"read": "complete"}}
        run = describe(make_manifest(self.root, "run-20261101T100000-bbbbbbbb", manifest))
        self.assertEqual(run["state"], "failed")
        self.assertEqual(run["failure"], {"stage": "write", "reason": "boom", "line": 3})
        self.assertEqual(run["ended"], "failed at write: boom")

    def test_a_stopped_run_reads_as_stopped(self):
        run = describe(make_manifest(self.root, "run-20261101T100000-cccccccc", {"status": "stopped", "beats":{}}, EVENTS[:2]))
        self.assertEqual(run["state"], "stopped")

    def test_a_run_still_going_is_running_until_ten_minutes_of_silence_then_stalled(self):
        directory = make_manifest(self.root, "run-20261101T100000-dddddddd", {"status": "running", "beats":{}}, EVENTS[:2])
        last = datetime.fromisoformat(EVENTS[1]["at"])
        self.assertEqual(describe(directory, now=last + timedelta(minutes=5))["state"], "running")
        self.assertEqual(describe(directory, now=last + timedelta(minutes=11))["state"], "stalled")

    def test_a_stalled_run_says_how_long_in_a_sensible_unit(self):
        directory = make_manifest(self.root, "run-20261101T100000-ffffffff", {"status": "running", "beats":{}}, EVENTS[:2])
        last = datetime.fromisoformat(EVENTS[1]["at"])
        self.assertIn("for 30 minutes", describe(directory, now=last + timedelta(minutes=30))["ended"])
        self.assertIn("for 5 hours", describe(directory, now=last + timedelta(hours=5))["ended"])
        self.assertIn("for 10 days", describe(directory, now=last + timedelta(days=10))["ended"])

    def test_the_rack_labels_an_unreadable_run_as_such(self):
        (self.root / "run-20261101T100000-eeeeeeee").mkdir()
        self.assertEqual(list_runs(self.root)[0]["sketch"], "unreadable")

    def test_a_folder_with_no_readable_files_is_unreadable_and_does_not_break_the_others(self):
        (self.root / "run-20261101T100000-eeeeeeee").mkdir()
        run = describe(self.root / "run-20261101T100000-eeeeeeee")
        self.assertEqual((run["state"], run["id"]), ("unreadable", "run-20261101T100000-eeeeeeee"))
        self.assertIn("no details", run["ended"])
        self.assertEqual(len(list_runs(self.root)), 1)


def stage_events(*steps: tuple[str, str]) -> list[dict]:
    """Events for (kind, stage) pairs, one second apart: kind is start, done or fail."""
    kinds = {"start": "beat_started", "done": "beat_completed", "fail": "beat_failed"}
    started = {"event": "run_started", "at": "2026-11-01T10:00:00+00:00", "play": "examples/h/household.yaml", "mode": "live"}
    return [started] + [
        {"event": kinds[kind], "at": f"2026-11-01T10:00:{index + 1:02d}+00:00", "beat": stage}
        for index, (kind, stage) in enumerate(steps)
    ]


class StageGroupsTest(unittest.TestCase):
    """UND-77: nested stages are grouped under the top-level stage that was running."""

    def tube(self, *steps):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            make_manifest(root, "run-20261101T100000-aaaaaaaa", {"status": "running", "beats":{}}, stage_events(*steps))
            return describe(root / "run-20261101T100000-aaaaaaaa", now=datetime.fromisoformat("2026-11-01T10:01:00+00:00"))["tube"]

    def test_iterations_of_a_child_sketch_form_one_group_with_the_stages_inside(self):
        tube = self.tube(
            ("start", "write_records"),
            ("start", "readings.judge_payee[0].decide"), ("done", "readings.judge_payee[0].decide"),
            ("start", "readings.judge_payee[1].decide"), ("done", "readings.judge_payee[1].decide"),
            ("start", "readings.judge_payee[2].decide"),
        )
        self.assertEqual([each["name"] for each in tube], ["write_records"])
        (group,) = tube[0]["groups"]
        self.assertEqual((group["name"], group["state"], group["done"], group["seen"]), ("readings.judge_payee", "running", 2, 3))
        self.assertEqual(group["stages"], [{"name": "decide", "started": 3, "completed": 2}])

    def test_a_subsketch_without_iterations_is_a_group_named_for_its_state(self):
        tube = self.tube(("start", "weather"), ("start", "weather_change.judge"),
                         ("done", "weather_change.judge"), ("done", "weather"))
        self.assertEqual(tube[0]["state"], "complete")
        (group,) = tube[0]["groups"]
        self.assertEqual((group["name"], group["state"], group["done"], group["seen"]), ("weather_change", "complete", 0, 0))

    def test_a_stage_in_progress_is_running_and_a_failure_marks_its_group_and_stage_failed(self):
        tube = self.tube(("start", "read"), ("done", "read"), ("start", "write"),
                         ("start", "a.child[0].go"), ("fail", "a.child[0].go"))
        self.assertEqual([(each["name"], each["state"]) for each in tube], [("read", "complete"), ("write", "running")])
        self.assertEqual(tube[1]["groups"][0]["state"], "failed")

    def test_a_run_with_no_nested_stages_has_no_empty_groups(self):
        tube = self.tube(("start", "read"), ("done", "read"))
        self.assertEqual(tube, [{"name": "read", "state": "complete", "groups": []}])

    def test_the_rack_entry_carries_the_state_and_the_sketch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            make_manifest(root, "run-20261101T100000-bbbbbbbb", {"status": "failed", "failed_beat": "x", "error": "e"}, EVENTS)
            make_manifest(root, "run-20261101T110000-cccccccc", {"status": "complete", "beats":{}}, EVENTS)
            entries = {each["id"]: each for each in list_runs(root, now=datetime.fromisoformat("2026-10-31T01:01:00+00:00"))}
        self.assertEqual(entries["run-20261101T100000-bbbbbbbb"]["state"], "failed")
        self.assertEqual(entries["run-20261101T110000-cccccccc"],
                         {"id": "run-20261101T110000-cccccccc", "sketch": "coffee", "state": "done"})


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
            events.write(json.dumps({"event": "beat_started", "at": "2026-11-01T12:00:03+00:00", "beat":"more"}) + "\n")
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


class ShutdownTest(unittest.TestCase):
    def test_a_server_stops_at_once_not_after_the_half_second_a_default_poll_would_wait(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        server = serve(Path(directory.name), port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.05)  # the loop is running
        began = time.monotonic()
        server.shutdown()
        server.server_close()
        self.assertLess(time.monotonic() - began, 0.2)
