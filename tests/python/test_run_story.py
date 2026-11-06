import json
import unittest

from test_sketch_coffee import CoffeeCase, double

from src.dashboard.view import describe, list_runs
from src.jev import JevError
from src.play.decide import decide_input


def events_of(folder):
    return [json.loads(line) for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]


class RunStoryTests(CoffeeCase):
    def setUp(self):
        super().setUp()
        code, lines, _ = self.go(jev=double())
        self.assertEqual(code, 0)
        self.folder_ = self.folder(lines)
        self.events = events_of(self.folder_)

    def test_the_first_line_carries_the_plan_of_the_play(self):
        first = self.events[0]
        self.assertEqual(first["event"], "run_started")
        found = first["plan"]
        flow = [each["id"] for each in found["nodes"] if each["kind"] == "beat" and each["flow"]]
        self.assertEqual(flow, ["weather", "split_trade", "match_orders", "to_ingredients", "write", "done"])
        self.assertEqual([each["id"] for each in found["nodes"] if each["final"]], ["done"])
        self.assertEqual(found["initial"], "weather")
        moves = {(each["from"], each["to"]) for each in found["edges"] if each["kind"] == "move"}
        self.assertTrue({("weather", "split_trade"), ("write", "done")} <= moves)
        self.assertTrue(any(each["kind"] == "piece" for each in found["nodes"]))

    def completed(self):
        return {e["beat"]: e for e in self.events if e["event"] == "beat_completed"}

    def test_a_completed_beat_says_what_it_read_made_and_wrote_by_name_rows_and_keys(self):
        done = self.completed()
        for each in done.values():
            self.assertIn("read", each)
            self.assertIn("wrote", each)
        split = done["split_trade"]
        self.assertEqual(split["read"], {"sales": {"rows": 1, "keys": ["drinks", "week"]}})
        self.assertEqual(split["wrote"], {})
        self.assertGreater(split["made"]["rows"], 1)
        self.assertIn("segment", split["made"]["keys"])
        written = done["write"]["wrote"]
        self.assertEqual(list(written), ["ingredients"])
        self.assertGreater(written["ingredients"]["rows"], 0)
        self.assertIn("ingredient", written["ingredients"]["keys"])

    def test_the_log_names_and_counts_but_carries_no_row_values(self):
        text = json.dumps([each for each in self.events if each["event"] == "beat_completed"])
        self.assertNotIn("2026-W43", text)  # the week in the sales file
        self.assertNotIn("1600", text)  # the drinks sold

    def test_every_move_to_a_beat_is_a_line_naming_the_beat_and_the_event_behind_it(self):
        moves = [(e["beat"], e["caused_by"]) for e in self.events if e["event"] == "beat_entered"]
        self.assertEqual(moves, [("weather", "start"), ("split_trade", "ok"), ("match_orders", "ok"),
                                 ("to_ingredients", "ok"), ("write", "ok"), ("done", "ok")])

    def test_each_blend_dimension_of_each_input_row_is_a_decision_with_its_options_and_pick(self):
        teens = {d["dimension"]: d for d in self.events if d["event"] == "decision" and d["row"] == "teens"}
        self.assertEqual(set(teens), {"temp", "size"})
        temp = teens["temp"]
        self.assertEqual((temp["beat"], temp["pick"]), ("match_orders", "hot"))
        self.assertEqual([o["name"] for o in temp["options"]], ["hot", "iced"])
        self.assertEqual(temp["probability"], max(o["weight"] for o in temp["options"]))
        self.assertAlmostEqual(sum(o["weight"] for o in temp["options"]), 1.0, places=5)

    def test_a_decision_with_nothing_removed_names_no_removal(self):
        commuters = [d for d in self.events if d["event"] == "decision" and d["row"] == "commuters"]
        self.assertTrue(commuters)
        self.assertEqual({o["removed_by"] for d in commuters for o in d["options"]}, {None})

    def test_a_run_that_finishes_ends_with_its_outcome(self):
        self.assertEqual(self.events[-1]["event"], "run_finished")

    def test_the_console_says_the_log_has_the_story(self):
        self.assertTrue(describe(self.folder_)["story"])


TREE = {"drink": [{"temp": "iced", "size": "large", "weight": 0.5}, {"temp": "iced", "size": "medium", "weight": 0.2},
                  {"temp": "hot", "size": "medium", "weight": 0.3}]}
STATE = {"blend": [{"decide": {"if": {"segment": {"eq": "students"}}, "then": TREE, "else": TREE}}],
         "forbid": [{"when": {"segment": {"eq": "students"}}, "drop": {"size": {"eq": "large"}}}], "shortlist": 1}


class DecisionStoryTests(unittest.TestCase):
    def story(self):
        story: list[dict] = []
        decide_input(STATE, {"segment": "students"}, {}, story=story)
        return {line["dimension"]: line for line in story}

    def test_a_forbid_rule_names_the_options_it_removed_and_they_weigh_nothing(self):
        size = self.story()["size"]
        large = next(o for o in size["options"] if o["name"] == "large")
        self.assertEqual((large["removed_by"], large["weight"]), ("forbid rule 0", 0.0))
        self.assertEqual((size["pick"], size["probability"]), ("medium", 1.0))

    def test_a_shortlist_names_the_options_it_left_out(self):
        temp = self.story()["temp"]
        hot = next(o for o in temp["options"] if o["name"] == "hot")
        self.assertEqual((hot["removed_by"], hot["weight"]), ("shortlist", 0.0))
        self.assertEqual(temp["pick"], "iced")

    def test_telling_the_story_changes_nothing_about_the_result(self):
        plain = decide_input(STATE, {"segment": "students"}, {})
        told = decide_input(STATE, {"segment": "students"}, {}, story=[])
        self.assertEqual(plain, told)


class FailedRunStoryTests(CoffeeCase):
    def test_a_run_that_fails_ends_with_the_failed_beat_and_its_message(self):
        code, lines, _ = self.go(jev=double(fail=JevError("Jev is down")))
        self.assertNotEqual(code, 0)
        events = events_of(self.folder(lines) if any(line.startswith("wrote ") for line in lines) else next(self.out.iterdir()))
        self.assertEqual(events[-1]["event"], "beat_failed")
        self.assertIn("Jev is down", events[-1]["reason"])


class OldLogTests(CoffeeCase):
    def test_a_log_written_before_plays_is_unreadable(self):
        """No back-compat (decision 41): a log whose first line does not name its play is shown as unreadable."""
        folder = self.dir / "run-20260101T000000-00000000"
        folder.mkdir()
        (folder / "events.jsonl").write_text(json.dumps({"event": "run_started", "at": "2026-01-01T00:00:00+00:00",
                                                         "sketch": "x/coffee.yaml", "mode": "live"}) + "\n", encoding="utf-8")
        (folder / "run.json").write_text(json.dumps({"status": "complete"}), encoding="utf-8")
        shown = describe(folder)
        self.assertEqual((shown["state"], shown["story"]), ("unreadable", False))
        self.assertEqual(list_runs(self.dir)[0]["sketch"], "unreadable")
