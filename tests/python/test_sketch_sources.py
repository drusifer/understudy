import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jev_double import JevDouble

from src.jev import Chosen, JevError
from src.paths import ROOT
from src.sketch.cli import main
from src.sketch.registry import STAGES, Stage
from src.sketch.sources.capture import CaptureStore, ReplayError, choose_replay
from src.sketch.sources.file import read_jsonl

FIXTURE = ROOT / "tests" / "fixtures" / "jev_read.yaml"
KEY = "jev_read.mood"
HAPPY = Chosen("happy", 0.7, {"happy": 0.7, "sad": 0.3})


async def read_mood(context):
    return await context.read("mood")


async def read_twice(context):
    await context.read("mood")
    return await context.read("mood")


def double(answer=HAPPY, fail=None):
    return JevDouble(choose_fn=lambda state, instructions, options: answer, fail=fail)


class SourcesCase(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(STAGES, {"etl.read": Stage("etl.read", None, {})})
        patcher.start()
        self.addCleanup(patcher.stop)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        (self.dir / "notes.jsonl").write_text('{"text": "the coffee was warm"}\n', encoding="utf-8")
        self.sketch = self.dir / "sketch.yaml"
        self.sketch.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        self.store = CaptureStore(self.dir / "cache")
        self.out = self.dir / "out"

    def go(self, *flags, jev=None, library=None):
        stdout, stderr = io.StringIO(), io.StringIO()

        def make_jev():
            if jev is None:
                raise JevError("Jev needs a TypeSafe key: set TYPESAFE_API_KEY")
            return jev

        code = main(["run", str(self.sketch), "--out", str(self.out), *flags], library=library or {"etl.read": read_mood},
                    make_jev=make_jev, store=self.store, stdout=stdout, stderr=stderr)
        return code, stdout.getvalue().splitlines(), stderr.getvalue().splitlines()

    def output_of(self, lines) -> list[dict]:
        wrote = next(line for line in lines if line.startswith("wrote "))
        return read_jsonl(Path(wrote.removeprefix("wrote ")))

    def summary_of(self, lines) -> dict:
        wrote = next(line for line in lines if line.startswith("wrote "))
        return json.loads((Path(wrote.removeprefix("wrote ")).parent / "summary.json").read_text(encoding="utf-8"))

    def seed(self, run_id: str, keys=(KEY,)) -> None:
        for key in keys:
            self.store.write(run_id, key, [{"level": "sad", "probability": 1.0}, {"level": "happy", "probability": 0.0}], "x")


class LiveTests(SourcesCase):
    def test_a_jev_source_returns_one_row_per_level_and_is_captured(self):
        jev = double()
        code, lines, err = self.go(jev=jev)
        self.assertEqual((code, err), (0, []))
        self.assertEqual(self.output_of(lines), [{"level": "happy", "probability": 0.7}, {"level": "sad", "probability": 0.3}])
        self.assertEqual(len(jev.requests), 1)
        self.assertEqual(jev.requests[0][1], {"notes": [{"text": "the coffee was warm"}]})
        self.assertEqual(jev.requests[0][2], "How does the customer feel about the notes?")
        self.assertEqual(jev.requests[0][3], {"happy": "Smiling, pleased.", "sad": "Frowning, disappointed."})
        (run_id,) = self.store.runs()
        meta = json.loads((self.store.run_dir(run_id) / f"{KEY}.meta.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["run_id"], meta["source"]), (run_id, KEY))
        self.assertEqual(len(meta["request_hash"]), 64)
        summary = self.summary_of(lines)
        self.assertEqual((summary["mode"], summary["stale"], summary["jev_requests"]), ("live", False, 1))

    def test_a_source_read_twice_in_a_run_asks_jev_once(self):
        jev = double()
        code, _, _ = self.go(jev=jev, library={"etl.read": read_twice})
        self.assertEqual(code, 0)
        self.assertEqual(len(jev.requests), 1)

    def test_a_live_run_with_no_key_is_refused_before_any_stage(self):
        code, out, err = self.go()
        self.assertEqual(code, 2)
        self.assertEqual(out, [])
        self.assertIn("TYPESAFE_API_KEY", err[-1])
        self.assertFalse(self.out.exists())

    def test_a_failed_jev_call_fails_the_run_and_captures_nothing(self):
        code, out, err = self.go(jev=double(fail=JevError("Jev could not be reached: down")))
        self.assertEqual(code, 1)
        self.assertEqual(err, ["understudy: Jev could not be reached: down"])
        self.assertFalse(any(line.startswith("wrote ") for line in out))
        self.assertEqual(self.store.runs(), [])

    def test_a_file_with_a_bad_line_names_the_file_and_the_line(self):
        (self.dir / "notes.jsonl").write_text('{"ok": 1}\nnot json\n', encoding="utf-8")
        code, _, err = self.go(jev=double())
        self.assertEqual(code, 1)
        self.assertIn("notes.jsonl line 2 is not valid JSON", err[-1])


class ReplayTests(SourcesCase):
    def test_a_replay_uses_the_capture_with_no_jev_and_no_key(self):
        self.go(jev=double())
        code, lines, err = self.go("--replay")
        self.assertEqual((code, err), (0, []))
        self.assertTrue(lines[0].startswith("replay: reading captures from ") and lines[0].endswith(", no live calls"), lines[0])
        self.assertEqual(self.output_of(lines), [{"level": "happy", "probability": 0.7}, {"level": "sad", "probability": 0.3}])
        summary = self.summary_of(lines)
        self.assertEqual((summary["mode"], summary["stale"], summary["jev_requests"]), ("replay", False, 0))

    def test_two_replays_are_byte_identical(self):
        self.go(jev=double())
        first = self.go("--replay")[1]
        second = self.go("--replay")[1]
        read = lambda lines: Path(next(x for x in lines if x.startswith("wrote ")).removeprefix("wrote ")).read_bytes()  # noqa: E731
        self.assertEqual(read(first), read(second))

    def test_a_replay_never_goes_live_and_names_the_missing_source(self):
        code, out, err = self.go("--replay", jev=double())
        self.assertEqual(code, 2)
        self.assertEqual(out, [])
        self.assertIn(KEY, err[-1])
        self.assertIn("do a live run first", err[-1])
        self.assertFalse(self.out.exists())

    def test_the_latest_run_that_covers_every_source_is_the_one_replayed(self):
        self.seed("run-20260101T000000-aaaa")
        self.seed("run-20260102T000000-bbbb", keys=("jev_read.other",))
        self.assertEqual(choose_replay(self.store, None, [KEY]), self.store.run_dir("run-20260101T000000-aaaa"))
        self.seed("run-20260103T000000-cccc")
        self.assertEqual(choose_replay(self.store, None, [KEY]), self.store.run_dir("run-20260103T000000-cccc"))

    def test_a_named_run_and_a_folder_of_captures_can_be_replayed(self):
        self.seed("run-20260101T000000-aaaa")
        self.seed("run-20260102T000000-bbbb")
        code, lines, _ = self.go("--replay=run-20260101T000000-aaaa")
        self.assertEqual(code, 0)
        self.assertEqual(self.output_of(lines)[0], {"level": "sad", "probability": 1.0})
        code, lines, _ = self.go(f"--replay={self.store.run_dir('run-20260102T000000-bbbb')}")
        self.assertEqual(code, 0)
        code, _, err = self.go("--replay=run-nope")
        self.assertEqual(code, 2)
        self.assertIn("no capture named 'run-nope'", err[-1])

    def test_a_replay_with_a_source_missing_from_the_named_run_stops(self):
        self.seed("run-20260101T000000-aaaa", keys=("jev_read.other",))
        code, _, err = self.go("--replay=run-20260101T000000-aaaa")
        self.assertEqual(code, 2)
        self.assertIn(KEY, err[-1])

    def test_a_changed_rubric_is_flagged_stale_and_the_run_carries_on(self):
        self.go(jev=double())
        self.sketch.write_text(self.sketch.read_text(encoding="utf-8").replace("Smiling, pleased.", "Beaming."), encoding="utf-8")
        code, lines, _ = self.go("--replay")
        self.assertEqual(code, 0)
        self.assertTrue(any("is stale" in line for line in lines))
        self.assertTrue(self.summary_of(lines)["stale"])

    def test_replay_is_not_asked_of_check(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        self.assertEqual(main(["check", str(self.sketch)], stdout=stdout, stderr=stderr), 0)
        self.assertEqual(self.store.runs(), [])


class StoreTests(SourcesCase):
    def test_the_last_runs_are_kept_together_and_the_rest_dropped(self):
        store = CaptureStore(self.dir / "small", keep=2)
        for number in range(4):
            for key in ("a.one", "a.two"):
                store.write(f"run-2026010{number + 1}T000000-x", key, [{"n": number}], "h")
        store.prune()
        self.assertEqual(store.runs(), ["run-20260104T000000-x", "run-20260103T000000-x"])
        for run_id in store.runs():
            self.assertEqual(sorted(p.name for p in store.run_dir(run_id).iterdir()),
                             ["a.one.jsonl", "a.one.meta.json", "a.two.jsonl", "a.two.meta.json"])

    def test_a_replay_with_an_empty_store_says_so(self):
        with self.assertRaisesRegex(ReplayError, "no saved run captured a.one, a.two"):
            choose_replay(CaptureStore(self.dir / "nothing"), None, ["a.one", "a.two"])


if __name__ == "__main__":
    unittest.main()
