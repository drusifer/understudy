"""UND-84: the run as it was after event N, computed in Python from the events alone."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from story_plan import story_plan

from src.dashboard.replay import decisions, replay
from src.dashboard.runs import Refused
from src.dashboard.server import serve
from src.dashboard.view import describe, printed

RUN = "run-20261103T100000-aaaaaaaa"
NOW = datetime(2026, 11, 3, 10, 0, 30, tzinfo=UTC)
STORY = {"event": "run_started", "play": "x/plain.yaml", "mode": "live",
         **story_plan(["a", "b", "done"], [("a", "b"), ("b", "done")], final={"done"})}
FINISHED = [
    STORY, {"event": "beat_entered", "beat":"a", "caused_by": "start"}, {"event": "beat_started", "beat":"a"},
    {"event": "beat_completed", "beat":"a"}, {"event": "beat_entered", "beat":"b", "caused_by": "ok"},
    {"event": "beat_started", "beat":"b"}, {"event": "beat_completed", "beat":"b"},
    {"event": "beat_entered", "beat":"done", "caused_by": "ok"}, {"event": "run_finished", "outcome": "complete"},
]


def write(root: Path, events: list[dict], manifest: dict, run_id: str = RUN, summary: dict | None = None) -> Path:
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=True)
    start = NOW - timedelta(seconds=len(events))
    lines = [{"at": (start + timedelta(seconds=n)).isoformat(timespec="seconds"), **event} for n, event in enumerate(events)]
    (folder / "events.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    (folder / "run.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "summary.json").write_text(json.dumps(summary or {"jev_requests": 7}), encoding="utf-8")
    return folder


COMPLETE = {"status": "complete", "beats":{"a": "complete", "b": "complete"}, "mode": "live", "outcome": "complete"}


class ReplayCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)


class CursorTests(ReplayCase):
    def setUp(self):
        super().setUp()
        self.folder = write(self.root, FINISHED, COMPLETE)

    def test_without_a_position_it_says_only_how_many_events_there_are(self):
        self.assertEqual(replay(self.folder), {"id": RUN, "events": len(FINISHED)})

    def test_after_event_zero_nothing_has_happened(self):
        shown = replay(self.folder, 0)
        self.assertEqual((shown["at"], shown["of"], shown["lines"], shown["chart"], shown["state"]),
                         (0, len(FINISHED), [], None, "running"))

    def test_mid_run_the_state_is_lit_the_stage_shown_and_only_the_lines_so_far_printed(self):
        shown = replay(self.folder, 4)  # run_started, a entered, a started, a completed
        self.assertEqual(shown["state"], "running")
        self.assertEqual(len(shown["lines"]), 4)
        self.assertEqual([(s["name"], s["state"]) for s in shown["tube"]], [("a", "complete")])
        self.assertEqual([n["id"] for n in shown["chart"]["nodes"] if n["current"]], ["a"])
        self.assertEqual(shown["ended"], "")

    def test_the_move_just_made_is_marked_where_the_cursor_is(self):
        shown = replay(self.folder, 5)  # b entered
        self.assertEqual(shown["chart"]["last_move"], {"from": "a", "to": "b"})

    def test_the_jev_count_is_unknown_until_the_run_ends(self):
        names = {g["name"]: g["text"] for g in replay(self.folder, 4)["gauges"]}
        self.assertEqual(names["JEV"], "-")
        names = {g["name"]: g["text"] for g in replay(self.folder, len(FINISHED))["gauges"]}
        self.assertEqual(names["JEV"], "7")

    def test_the_last_event_shows_the_run_exactly_as_the_live_view_does(self):
        shown, live = replay(self.folder, len(FINISHED)), describe(self.folder, NOW)
        for key in ("state", "ended", "hold", "chart", "tube", "gauges", "lines", "failure"):
            self.assertEqual(shown[key], live[key], key)
        self.assertEqual(shown["state"], "done")

    def test_a_position_outside_the_log_is_refused(self):
        for at in (-1, len(FINISHED) + 1):
            with self.assertRaises(Refused) as refused:
                replay(self.folder, at)
            self.assertEqual(refused.exception.status, 400, at)


SAID = {"read": {"in": {"rows": 3, "keys": ["a", "b"]}}, "wrote": {}, "made": {"rows": 2, "keys": ["c"]}}


class StepTests(ReplayCase):
    """UND-113: what each completed beat read, made and wrote, from the log alone."""

    def events(self):
        return [STORY, {"event": "beat_entered", "beat": "a", "caused_by": "start"}, {"event": "beat_started", "beat": "a"},
                {"event": "beat_completed", "beat": "a", **SAID}, {"event": "beat_entered", "beat": "b", "caused_by": "ok"},
                {"event": "beat_started", "beat": "b"}, {"event": "beat_completed", "beat": "b", "read": {}, "wrote": {}}]

    def test_a_run_lists_what_each_completed_beat_said(self):
        folder = write(self.root, self.events(), {"status": "running", "beats": {}})
        self.assertEqual(describe(folder, NOW)["steps"], {"a": SAID, "b": {"read": {}, "wrote": {}}})

    def test_a_replay_shows_only_the_beats_completed_by_that_event(self):
        folder = write(self.root, self.events(), {"status": "running", "beats": {}})
        self.assertEqual(replay(folder, 3)["steps"], {})
        self.assertEqual(replay(folder, 4)["steps"], {"a": SAID})
        self.assertEqual(replay(folder, 7)["steps"], describe(folder, NOW)["steps"])

    def test_a_beat_logged_before_this_said_nothing_and_is_shown_without_the_lists_and_without_error(self):
        events = [STORY, {"event": "beat_started", "beat": "a"}, {"event": "beat_completed", "beat": "a"}]
        folder = write(self.root, events, {"status": "running", "beats": {}})
        self.assertEqual(describe(folder, NOW)["steps"], {"a": {}})


class EndingTests(ReplayCase):
    def test_a_failed_run_is_running_until_its_failure_and_then_says_why(self):
        events = [*FINISHED[:3], {"event": "beat_failed", "beat":"a", "reason": "boom"}]
        folder = write(self.root, events, {"status": "failed", "failed_beat": "a", "error": "boom", "beats":{}})
        self.assertEqual(replay(folder, 3)["state"], "running")
        end = replay(folder, 4)
        self.assertEqual((end["state"], end["ended"]), ("failed", "failed at a: boom"))
        self.assertEqual(end["failure"], describe(folder, NOW)["failure"])

    def test_a_stopped_run_ends_stopped(self):
        folder = write(self.root, FINISHED[:3], {"status": "stopped", "beats":{}})
        self.assertEqual(replay(folder, 2)["state"], "running")
        self.assertEqual(replay(folder, 3)["state"], "stopped")

    def test_a_hold_is_replayed_as_paused_before_the_stage_and_released_by_the_next_event(self):
        events = [STORY, {"event": "paused", "beat":"a"}, {"event": "resumed", "beat":"a"},
                  {"event": "beat_started", "beat":"a"}]
        folder = write(self.root, events, {"status": "running", "beats":{}})
        held = replay(folder, 2)
        self.assertEqual((held["state"], held["ended"], held["hold"]), ("paused", "paused before a", {"stage": "a"}))
        self.assertEqual((replay(folder, 3)["state"], replay(folder, 3)["hold"]), ("running", None))

    def test_a_log_without_a_story_replays_what_it_has_and_draws_no_diagram(self):
        folder = write(self.root, [{"event": "run_started", "sketch": "old.yaml", "mode": "live"},
                                   {"event": "beat_started", "beat":"a"}], {"status": "running", "beats":{}})
        shown = replay(folder, 2)
        self.assertEqual((shown["chart"], len(shown["lines"])), (None, 2))


class RefusalTests(ReplayCase):
    def refused(self, folder, status):
        with self.assertRaises(Refused) as refused:
            replay(folder, 0)
        self.assertEqual(refused.exception.status, status)
        return refused.exception.message

    def test_a_line_that_is_not_json_is_named(self):
        folder = write(self.root, FINISHED, COMPLETE)
        lines = (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
        lines[2] = "{not json"
        (folder / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertEqual(self.refused(folder, 422), "events.jsonl line 3 is not readable")

    def test_a_line_that_is_not_an_object_is_named(self):
        folder = write(self.root, FINISHED, COMPLETE)
        with (folder / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write("[1, 2]\n")
        self.assertEqual(self.refused(folder, 422), f"events.jsonl line {len(FINISHED) + 1} is not readable")

    def test_no_events_or_no_file_has_nothing_to_replay(self):
        empty = write(self.root, [], COMPLETE)
        self.assertEqual(self.refused(empty, 422), "this run has no events to replay")
        (empty / "events.jsonl").unlink()
        self.assertEqual(self.refused(empty, 422), "this run has no events to replay")


class ReplayHttpTests(ReplayCase):
    def setUp(self):
        super().setUp()
        self.folder = write(self.root, FINISHED, COMPLETE)
        self.server = serve(self.root, port=0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def get(self, path: str):
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as error:
            text = error.read().decode()
            return error.code, json.loads(text) if text.startswith("{") else text

    def test_the_count_and_a_position_are_served(self):
        self.assertEqual(self.get(f"/api/runs/{RUN}/replay"), (200, {"id": RUN, "events": len(FINISHED)}))
        status, shown = self.get(f"/api/runs/{RUN}/replay?at=4")
        self.assertEqual((status, shown["at"], shown["of"]), (200, 4, len(FINISHED)))

    def test_a_bad_position_is_400_with_the_reason(self):
        for query in ("at=99", "at=-1", "at=x", "at="):
            status, body = self.get(f"/api/runs/{RUN}/replay?{query}")
            self.assertEqual(status, 400, query)
            self.assertIn("problem", body)

    def test_an_unreadable_log_is_422_with_one_line(self):
        (self.folder / "events.jsonl").write_text("{broken\n", encoding="utf-8")
        status, body = self.get(f"/api/runs/{RUN}/replay?at=0")
        self.assertEqual((status, body), (422, {"problem": "events.jsonl line 1 is not readable"}))

    def test_a_run_that_is_not_there_is_404(self):
        self.assertEqual(self.get("/api/runs/run-20990101T000000-bbbbbbbb/replay")[0], 404)


def decision(row="teens", dimension="temp", pick="hot", options=None, **extra):
    options = options or [{"name": "hot", "weight": 0.7, "removed_by": None}, {"name": "iced", "weight": 0.3, "removed_by": None}]
    return {"event": "decision", "beat":"match", "row": row, "dimension": dimension, "pick": pick, "probability": 0.7,
            "options": options, **extra}


class DecisionsTests(ReplayCase):
    def folder(self, events):
        return write(self.root, [STORY, *events, {"event": "run_finished", "outcome": "complete"}], COMPLETE)

    def test_each_decision_is_listed_with_its_event_number_stage_row_dimension_pick_and_options(self):
        folder = self.folder([{"event": "beat_started", "beat":"match"}, decision(),
                              decision(row="adults", dimension="size", pick="large", options=[
                                  {"name": "small", "weight": 0.0, "removed_by": "forbid rule 2"},
                                  {"name": "large", "weight": 0.7, "removed_by": None},
                                  {"name": "medium", "weight": 0.3, "removed_by": "shortlist"}])])
        found = decisions(folder)
        self.assertEqual([(d["index"], d["row"], d["dimension"], d["pick"]) for d in found],
                         [(2, "teens", "temp", "hot"), (3, "adults", "size", "large")])  # index = the event's position (0-based)
        self.assertEqual(found[1]["options"][0], {"name": "small", "weight": 0.0, "removed_by": "forbid rule 2"})
        self.assertEqual(found[1]["options"][2]["removed_by"], "shortlist")
        self.assertEqual((found[0]["stage"], found[0]["probability"]), ("match", 0.7))

    def test_a_run_with_no_decisions_lists_none(self):
        self.assertEqual(decisions(write(self.root, FINISHED, COMPLETE)), [])

    def test_a_decision_missing_fields_shows_what_it_has_and_names_what_is_missing(self):
        folder = self.folder([{"event": "decision", "beat":"match", "dimension": "temp"}])
        (found,) = decisions(folder)
        self.assertEqual((found["dimension"], found["pick"], found["options"]), ("temp", None, []))
        self.assertEqual(found["missing"], ["row", "pick", "probability", "options"])

    def test_options_that_are_not_a_list_of_objects_are_dropped_not_crashed_on(self):
        folder = self.folder([decision(options=["hot", {"name": "iced"}, None, {"weight": "heavy"}])])
        (found,) = decisions(folder)
        self.assertEqual([o["name"] for o in found["options"]], ["iced", None])
        self.assertIn("options", found["missing"])  # only part of them could be shown

    def test_names_with_markup_are_returned_as_they_are_for_the_page_to_draw_as_text(self):
        folder = self.folder([decision(row="<b>x</b>", pick="<script>1</script>")])
        (found,) = decisions(folder)
        self.assertEqual((found["row"], found["pick"]), ("<b>x</b>", "<script>1</script>"))

    def test_an_unreadable_log_is_refused_like_a_replay(self):
        folder = self.folder([decision()])
        (folder / "events.jsonl").write_text("{broken\n", encoding="utf-8")
        with self.assertRaises(Refused) as refused:
            decisions(folder)
        self.assertEqual(refused.exception.status, 422)

    def test_the_printed_line_of_a_decision_names_the_choice(self):
        self.assertEqual(printed({"event": "decision", "at": "2026-11-03T10:00:01+00:00", "beat": "match", "row": "teens",
                                  "dimension": "temp", "pick": "hot", "probability": 0.7})["text"],
                         "10:00:01    decision match: teens temp = hot (0.7)")

    def test_a_decision_line_can_be_told_from_the_rest_so_the_page_can_open_it(self):
        self.assertEqual(printed({"event": "decision"})["event"], "decision")


class DecisionsHttpTests(ReplayCase):
    def test_the_list_is_served_for_a_run_and_a_bad_log_is_422(self):
        folder = write(self.root, [STORY, decision(), {"event": "run_finished", "outcome": "complete"}], COMPLETE)
        server = serve(self.root, port=0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(f"{base}/api/runs/{RUN}/decisions", timeout=10) as response:
            self.assertEqual([d["pick"] for d in json.loads(response.read().decode())], ["hot"])
        (folder / "events.jsonl").write_text("{broken\n", encoding="utf-8")
        with self.assertRaises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(f"{base}/api/runs/{RUN}/decisions", timeout=10)
        self.assertEqual(refused.exception.code, 422)
