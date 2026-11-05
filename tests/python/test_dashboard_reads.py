"""UND-78: the Jev list reads a run's captured answers: levels and probabilities, flagged when unsure."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from src.dashboard.reads import REVIEW_THRESHOLD, jev_reads
from src.dashboard.server import serve
from src.play.sources.capture import CaptureStore

RUN = "run-20261101T100000-aaaaaaaa"


def rows(**levels: float) -> list[dict]:
    return [{"level": level, "probability": probability} for level, probability in levels.items()]


class ReadsCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.cache = self.root / ".understudy" / "cache"
        self.store = CaptureStore(self.cache)
        self.runs = self.root / "build" / "runs"

    def make_run(self, name: str = RUN, **manifest) -> Path:
        directory = self.runs / name
        directory.mkdir(parents=True)
        (directory / "run.json").write_text(json.dumps({"status": "complete", "mode": "live", "stages": {}, **manifest}))
        (directory / "summary.json").write_text(json.dumps({"jev_requests": manifest.pop("requests", 0)}))
        return directory

    def reads(self, directory: Path) -> dict:
        return jev_reads(directory, self.cache, self.root)


class ListTest(ReadsCase):
    def test_each_read_lists_its_levels_the_top_one_and_how_close_the_next_was(self):
        directory = self.make_run()
        self.store.write(RUN, "named.child[0].kind", rows(a=0.1, b=0.8, c=0.1), "h1", instructions="Which kind is it?",
                         levels_from_data=False)
        result = self.reads(directory)
        (read,) = result["reads"]
        self.assertEqual((read["source"], read["top"], read["instructions"]), ("named.child[0].kind", "b", "Which kind is it?"))
        self.assertEqual(read["levels"], [["a", 0.1], ["b", 0.8], ["c", 0.1]])
        self.assertAlmostEqual(read["margin"], 0.7)
        self.assertFalse(read["flagged"])
        self.assertTrue(result["kept"])

    def test_a_read_below_the_review_threshold_or_choosing_none_of_these_is_flagged(self):
        directory = self.make_run()
        self.store.write(RUN, "a", rows(x=0.4, y=0.35, z=0.25), "h", instructions="q")
        self.store.write(RUN, "b", rows(none_of_these=0.9, y=0.1), "h", instructions="q")
        self.store.write(RUN, "c", rows(x=REVIEW_THRESHOLD, y=0.3), "h", instructions="q")
        flags = {each["source"]: each["flagged"] for each in self.reads(directory)["reads"]}
        self.assertEqual(flags, {"a": True, "b": True, "c": False})

    def test_two_gauges_come_from_the_reads_the_confidence_of_the_last_and_asked_against_reused(self):
        directory = self.make_run(requests=2)
        self.store.write(RUN, "a", rows(x=0.9, y=0.1), "h", instructions="q")
        self.store.write(RUN, "b", rows(x=0.6, y=0.4), "h", instructions="q")
        result = self.reads(directory)
        self.assertEqual((result["asked"], result["reused"]), (2, 0))
        self.assertEqual(result["confidence"], 0.6)

    def test_an_old_capture_without_a_question_still_lists(self):
        directory = self.make_run()
        self.store.write(RUN, "a", rows(x=0.9, y=0.1), "h")
        self.assertIsNone(self.reads(directory)["reads"][0]["instructions"])


class PrivacyTest(ReadsCase):
    """SEC-007: level names that come from the owner's data (a refund candidate named by its date and amount) are not
    sent to the network; only the sketch's own words are."""

    def test_levels_from_data_or_of_unknown_origin_read_as_option_numbers_with_their_probabilities(self):
        directory = self.make_run()
        self.store.write(RUN, "from_data", rows(**{"refund_2026-01-05_-12.50_x1": 0.2, "refund_2026-01-06_-9.99_x2": 0.8}), "h",
                         instructions="Which charge?", levels_from_data=True)
        self.store.write(RUN, "unknown", rows(**{"charge_2026-02-01_-3.00_x3": 0.9, "charge_2026-02-02_-4.00_x4": 0.1}), "h")
        reads = {each["source"]: each for each in self.reads(directory)["reads"]}
        for key, top in (("from_data", "option 2"), ("unknown", "option 1")):
            self.assertEqual(reads[key]["top"], top)
            for private in ("12.50", "9.99", "3.00", "4.00", "refund_", "charge_"):
                self.assertNotIn(private, json.dumps(reads[key]))
        self.assertEqual(reads["from_data"]["levels"], [["option 1", 0.2], ["option 2", 0.8]])
        self.assertEqual(reads["from_data"]["instructions"], "Which charge?")

    def test_the_list_says_how_many_reads_have_their_names_hidden_so_the_page_can_say_why(self):
        directory = self.make_run()
        self.store.write(RUN, "own_words", rows(x=0.9, y=0.1), "h", levels_from_data=False)
        self.store.write(RUN, "from_data", rows(a=0.6, b=0.4), "h", levels_from_data=True)
        self.store.write(RUN, "unknown", rows(a=0.6, b=0.4), "h")
        self.assertEqual(self.reads(directory)["hidden"], 2)
        self.assertEqual(jev_reads(directory, self.cache, self.root, reveal=True)["hidden"], 0)
        self.assertEqual(self.reads(self.make_run("run-20261101T110000-bbbbbbbb"))["hidden"], 0)  # no captures: nothing to hide

    def test_the_holder_of_the_secret_sees_the_real_names(self):
        directory = self.make_run()
        self.store.write(RUN, "a", rows(**{"refund_x1": 0.2, "refund_x2": 0.8}), "h", levels_from_data=True)
        self.assertEqual(jev_reads(directory, self.cache, self.root, reveal=True)["reads"][0]["top"], "refund_x2")
        self.assertEqual(jev_reads(directory, self.cache, self.root)["reads"][0]["top"], "option 2")

    def test_the_sketchs_own_none_of_these_stays_readable_so_the_flag_makes_sense(self):
        directory = self.make_run()
        self.store.write(RUN, "a", rows(**{"charge_2026-02-01_-3.00_x3": 0.1, "none_of_these": 0.9}), "h", levels_from_data=True)
        (read,) = self.reads(directory)["reads"]
        self.assertEqual((read["top"], read["flagged"]), ("none_of_these", True))
        self.assertEqual(read["levels"][0][0], "option 1")


class ReplayAndMissingTest(ReadsCase):
    def test_a_replayed_run_shows_the_answers_it_replayed_and_counts_them_as_reused(self):
        original = "run-20261030T100000-bbbbbbbb"
        self.store.write(original, "a", rows(x=0.9, y=0.1), "h", instructions="q")
        directory = self.make_run(mode="replay", replay_of=f".understudy/cache/{original}")
        result = self.reads(directory)
        self.assertEqual([each["source"] for each in result["reads"]], ["a"])
        self.assertEqual((result["asked"], result["reused"]), (0, 1))

    def test_a_replay_path_pointing_outside_the_project_reads_nothing(self):
        directory = self.make_run(mode="replay", replay_of="../../../etc")
        result = self.reads(directory)
        self.assertEqual((result["kept"], result["reads"]), (False, []))

    def test_a_run_whose_captures_were_pruned_says_so(self):
        directory = self.make_run(requests=5)
        (self.runs / RUN / "summary.json").write_text(json.dumps({"jev_requests": 5}))
        result = self.reads(directory)
        self.assertFalse(result["kept"])
        self.assertIn("no longer kept", result["note"])

    def test_a_run_that_never_asked_jev_says_so(self):
        result = self.reads(self.make_run())
        self.assertFalse(result["kept"])
        self.assertIn("did not ask Jev", result["note"])

    def test_a_capture_missing_its_other_half_is_named_and_the_rest_still_lists(self):
        directory = self.make_run()
        self.store.write(RUN, "good", rows(x=0.9, y=0.1), "h", instructions="q")
        (self.cache / RUN / "broken.jsonl").write_text(json.dumps({"level": "x", "probability": 1.0}) + "\n")
        result = self.reads(directory)
        self.assertEqual([each["source"] for each in result["reads"]], ["good"])
        self.assertEqual(result["missing"], ["broken"])


class RouteTest(ReadsCase):
    def test_the_jev_route_answers_for_a_run_and_refuses_a_bad_id(self):
        self.make_run()
        self.store.write(RUN, "a", rows(x=0.9, y=0.1), "h", instructions="q")
        server = serve(self.runs, port=0, cache=self.cache, project=self.root)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(f"{base}/api/runs/{RUN}/jev", timeout=5) as response:
            body = json.loads(response.read())
        self.assertEqual(body["reads"][0]["source"], "a")
        for bad in ("/api/runs/..%2F..%2Fx/jev", "/api/runs/run-nope/jev"):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(base + bad, timeout=5)
            self.assertEqual(caught.exception.code, 404, bad)


if __name__ == "__main__":
    unittest.main()
