"""UND-83: a run is held between stages through a control file in its folder; a bad file never wedges the run."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_sketch_run import RunCase, library

from src.play import control
from src.play.check import load_checked
from src.play.control import Hold, read_control, write_control
from src.play.run import run_sketch


class ControlFileTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)

    def test_no_file_means_run(self):
        self.assertEqual(read_control(self.dir), {"mode": "run", "steps": 0})

    def test_what_is_written_is_read_back_and_no_temporary_file_is_left(self):
        write_control(self.dir, "hold", 2)
        self.assertEqual(read_control(self.dir), {"mode": "hold", "steps": 2})
        self.assertEqual([p.name for p in self.dir.iterdir()], ["control.json"])

    def test_a_beat_to_hold_before_is_written_and_read_back_beside_the_mode(self):
        write_control(self.dir, "run", 0, stop_at="write")
        self.assertEqual(read_control(self.dir), {"mode": "run", "steps": 0, "stop_at": "write"})
        write_control(self.dir, "hold", 1)  # a console action rewrites the file, and the beat is spent
        self.assertEqual(read_control(self.dir), {"mode": "hold", "steps": 1})

    def test_a_bad_beat_to_hold_before_means_run(self):
        for stop in ("1", "[]", '""', json.dumps("x" * 300), "null"):
            (self.dir / "control.json").write_text(f'{{"mode": "hold", "steps": 1, "stop_at": {stop}}}', encoding="utf-8")
            self.assertEqual(read_control(self.dir), {"mode": "run", "steps": 0}, stop[:20])

    def test_a_bad_file_means_run(self):
        for text in ("not json", "[]", '{"mode": "sleep", "steps": 1}', '{"mode": "hold", "steps": -1}',
                     '{"mode": "hold", "steps": "1"}', '{"mode": "hold", "steps": true}', "x" * 5000):
            (self.dir / "control.json").write_text(text, encoding="utf-8")
            self.assertEqual(read_control(self.dir), {"mode": "run", "steps": 0}, text[:20])


RELEASED_AT = 3  # the look at which a test releases a held run
SECOND_LOOK = 2


def events_of(folder: Path) -> list[dict]:
    return [json.loads(line) for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]


class HoldTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.emitted: list[tuple] = []

    def hold(self, on_sleep=None):
        sleeps = []

        async def sleep(seconds):
            sleeps.append(seconds)
            if on_sleep:
                on_sleep(len(sleeps))

        return Hold(self.dir, lambda kind, **fields: self.emitted.append((kind, fields)), sleep=sleep), sleeps

    def before(self, hold, stage):
        asyncio.run(hold.before(stage))

    def test_a_run_not_held_goes_straight_through_and_says_nothing(self):
        hold, sleeps = self.hold()
        self.before(hold, "count")
        self.assertEqual((self.emitted, sleeps), ([], []))

    def test_a_held_run_waits_names_the_stage_and_goes_on_when_released(self):
        write_control(self.dir, "hold", 0)
        hold, sleeps = self.hold(lambda n: write_control(self.dir, "run", 0) if n == RELEASED_AT else None)
        self.before(hold, "count")
        self.assertEqual(len(sleeps), RELEASED_AT)
        self.assertEqual(self.emitted,[("paused", {"beat": "count"}), ("resumed", {"beat": "count"})])

    def test_a_step_lets_exactly_one_stage_through_and_the_next_waits(self):
        write_control(self.dir, "hold", 0)
        hold, _ = self.hold(lambda n: write_control(self.dir, "hold", 1))
        self.before(hold, "count")  # waits, is stepped, goes on
        self.assertEqual([k for k, _ in self.emitted], ["paused", "resumed"])
        self.emitted.clear()
        hold2, sleeps = self.hold(lambda n: write_control(self.dir, "run", 1) if n == SECOND_LOOK else None)
        hold2.taken = 1  # the same run: one step already used
        self.before(hold2, "mark")
        self.assertEqual([k for k, _ in self.emitted], ["paused", "resumed"])
        self.assertEqual(len(sleeps), SECOND_LOOK)

    def test_resuming_after_a_pause_does_not_replay_old_steps(self):
        write_control(self.dir, "hold", 1)  # one step granted before this runner looked
        hold, sleeps = self.hold(lambda n: write_control(self.dir, "run", 1) if n == 1 else None)
        self.before(hold, "a")  # uses the step at once
        self.assertEqual(sleeps, [])
        self.before(hold, "b")  # held again with no step left
        self.assertEqual(len(sleeps), 1)

    def test_a_run_goes_through_every_beat_but_the_one_to_hold_before_and_waits_there_naming_it(self):
        write_control(self.dir, "run", 0, stop_at="write")
        hold, sleeps = self.hold(lambda n: write_control(self.dir, "hold", 1) if n == 1 else write_control(self.dir, "run", 1))
        self.before(hold, "count")
        self.assertEqual((self.emitted, sleeps), ([], []))
        self.before(hold, "write")  # waits, is stepped, goes on
        self.assertEqual(self.emitted, [("paused", {"beat": "write"}), ("resumed", {"beat": "write"})])
        self.emitted.clear()
        self.before(hold, "after")  # the console's step made it a hold: the next beat waits too (here until a resume)
        self.assertEqual([kind for kind, _ in self.emitted], ["paused", "resumed"])
        self.assertEqual(len(sleeps), 2)  # one wait at the beat, one at the next

    def test_resuming_at_the_beat_lets_the_rest_run_free(self):
        write_control(self.dir, "run", 0, stop_at="write")
        hold, _ = self.hold(lambda n: write_control(self.dir, "run", 0))
        self.before(hold, "write")
        self.emitted.clear()
        self.before(hold, "after")
        self.assertEqual(self.emitted, [])

    def test_a_bad_file_while_held_releases_the_run(self):
        write_control(self.dir, "hold", 0)
        hold, sleeps = self.hold(lambda n: (self.dir / "control.json").write_text("junk", encoding="utf-8"))
        self.before(hold, "count")
        self.assertEqual(len(sleeps), 1)


class HeldRunTests(RunCase):
    def run_held(self, driver, **options):
        """Run the branch sketch started held (or held before `stop_at`); `driver(task)` steps and resumes it."""
        async def go():
            sketch = load_checked(self.sketch())
            task = asyncio.create_task(run_sketch(sketch, self.out, library(), lambda line: None, **{"pause": True, **options}))
            await driver(task)
            return await task

        with patch.object(control, "POLL", 0.005):
            return asyncio.run(go())

    async def wait_for(self, folder_getter, kind, count=1):
        for _ in range(2000):
            folder = folder_getter()
            if folder and [e for e in events_of(folder) if e["event"] == kind][count - 1:]:
                return folder
            await asyncio.sleep(0.005)
        raise AssertionError(f"no {kind} event")

    def folder(self):
        runs = list(self.out.glob("run-*")) if self.out.exists() else []
        return next(iter(runs), None)

    def test_started_held_it_makes_no_move_until_stepped_and_then_one_per_step(self):
        async def driver(task):
            folder = await self.wait_for(self.folder, "paused")
            started = [e for e in events_of(folder) if e["event"] == "beat_started"]
            self.assertEqual(started, [])  # held before the first beat
            first_pause = next(e for e in events_of(folder) if e["event"] == "paused")
            self.assertEqual(first_pause["beat"], "count")
            write_control(folder, "hold", 1)
            await self.wait_for(self.folder, "paused", 2)
            started = [e["beat"] for e in events_of(folder) if e["event"] == "beat_started"]
            self.assertEqual(started, ["count"])  # exactly one move
            write_control(folder, "run", 1)  # resume

        result = self.run_held(driver)
        kinds = [e["event"] for e in events_of(result.directory)]
        self.assertEqual(kinds.count("paused"), 2)
        self.assertEqual(kinds.count("resumed"), 2)
        self.assertEqual(kinds[-1], "run_finished")

    def test_held_before_a_beat_it_runs_the_earlier_beats_then_waits_there(self):
        async def driver(task):
            folder = await self.wait_for(self.folder, "paused")
            events = events_of(folder)
            self.assertEqual([e["beat"] for e in events if e["event"] == "beat_started"], ["count", "quiet"])
            self.assertEqual(next(e for e in events if e["event"] == "paused")["beat"], "write")
            write_control(folder, "run", 0)  # resume

        result = self.run_held(driver, pause=False, stop_at="write")
        kinds = [e["event"] for e in events_of(result.directory)]
        self.assertEqual((kinds.count("paused"), kinds.count("resumed"), kinds[-1]), (1, 1, "run_finished"))

    def test_a_run_never_held_has_no_paused_events(self):
        result, _ = self.run_it(library())
        self.assertNotIn("paused", [e["event"] for e in events_of(result.directory)])
