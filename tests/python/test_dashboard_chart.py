"""UND-82 part 1: the server lays the machine out and says which state is lit."""

import json
import random
import tempfile
import unittest
from pathlib import Path

from src.dashboard.chart import guard_text, layout, overlay
from src.dashboard.view import describe
from src.paths import ROOT
from src.sketch.loader import load
from src.sketch.run import _story_of

HALF = 0.5
GUARDED = 2  # a move tuple with a guard has three parts


def guard(rng, n):
    """A guard on about half the moves: a one-item tuple to spread into a move, or nothing."""
    return ({"x": {"eq": n}},) if rng.random() < HALF else ()


def machine(names, moves, final=(), initial=None):
    """A machine as the story line tells it: states in order, and the moves between them (a tuple may carry a guard)."""
    return {"initial": initial or names[0], "states": [{"name": n, "final": n in final} for n in names],
            "transitions": [{"from": m[0], "to": m[1], "event": "ok", **({"when": m[2]} if len(m) > GUARDED else {})} for m in moves]}


def lay(story):
    return layout(story["states"], story["transitions"], story["initial"])


def box(each):
    return (each["x"], each["y"], each["x"] + each["w"], each["y"] + each["h"])


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def label_box(edge):
    each = edge["label_box"]
    return (each["x"], each["y"], each["x"] + each["w"], each["y"] + each["h"])


def segments(edge):
    return list(zip(edge["points"], edge["points"][1:], strict=False))


def crosses(segment, rectangle, margin=1):
    """Whether an axis-aligned segment enters the inside of a rectangle (touching its edge does not count)."""
    (x1, y1), (x2, y2) = segment
    left, top, right, bottom = rectangle[0] + margin, rectangle[1] + margin, rectangle[2] - margin, rectangle[3] - margin
    return min(x1, x2) < right and max(x1, x2) > left and min(y1, y2) < bottom and max(y1, y2) > top


def assert_clean(test, chart):
    """No two boxes overlap, no two labels overlap, no label sits on a box, and no arrow runs through a box that is not its end."""
    nodes = {each["id"]: each for each in chart["nodes"]}
    boxes = [box(each) for each in nodes.values()]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            test.assertFalse(overlap(a, b), "two boxes overlap")
    labels = [(edge, label_box(edge)) for edge in chart["edges"] if edge.get("label")]
    for i, (_, a) in enumerate(labels):
        for _, b in labels[i + 1:]:
            test.assertFalse(overlap(a, b), "two labels overlap")
        for each in boxes:
            test.assertFalse(overlap(a, each), "a label sits on a box")
    for edge in chart["edges"]:
        ends = {edge["from"], edge["to"]}
        for name, each in nodes.items():
            if name in ends:
                continue
            for segment in segments(edge):
                test.assertFalse(crosses(segment, box(each)), f"arrow {edge['from']}->{edge['to']} runs through {name}")


class LayoutTests(unittest.TestCase):
    def test_states_are_laid_out_in_layers_from_the_initial_state_downward(self):
        chart = lay(machine(["a", "b", "c"], [("a", "b"), ("b", "c")], final={"c"}))
        rows = {each["id"]: each["y"] for each in chart["nodes"]}
        self.assertTrue(rows["a"] < rows["b"] < rows["c"])
        self.assertEqual(len({each["x"] for each in chart["nodes"]}), 1)  # a straight line of states lines up

    def test_a_branch_puts_the_two_branches_side_by_side_and_the_join_below_both(self):
        chart = lay(machine(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")], final={"d"}))
        at = {each["id"]: each for each in chart["nodes"]}
        self.assertEqual(at["b"]["y"], at["c"]["y"])
        self.assertNotEqual(at["b"]["x"], at["c"]["x"])
        self.assertGreater(at["d"]["y"], at["b"]["y"])
        assert_clean(self, chart)

    def test_the_initial_and_final_states_are_flagged(self):
        chart = lay(machine(["a", "b"], [("a", "b")], final={"b"}))
        flags = {each["id"]: (each["initial"], each["final"]) for each in chart["nodes"]}
        self.assertEqual(flags, {"a": (True, False), "b": (False, True)})

    def test_every_move_is_an_arrow_ending_at_its_target(self):
        chart = lay(machine(["a", "b", "c"], [("a", "b"), ("b", "c")]))
        self.assertEqual([(each["from"], each["to"]) for each in chart["edges"]], [("a", "b"), ("b", "c")])
        at = {each["id"]: each for each in chart["nodes"]}
        for edge in chart["edges"]:
            x, y = edge["points"][-1]
            target = at[edge["to"]]
            self.assertTrue(target["x"] <= x <= target["x"] + target["w"] and y == target["y"])  # arrives at the top edge

    def test_an_arrow_that_skips_a_layer_goes_around_the_boxes_in_between(self):
        chart = lay(machine(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("c", "d"), ("a", "d")]))
        long = next(each for each in chart["edges"] if (each["from"], each["to"]) == ("a", "d"))
        self.assertGreater(len(long["points"]), 2)
        assert_clean(self, chart)

    def test_a_move_back_to_an_earlier_state_is_a_loop_drawn_beside_the_boxes(self):
        chart = lay(machine(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")]))
        back = next(each for each in chart["edges"] if (each["from"], each["to"]) == ("c", "a"))
        self.assertTrue(back["back"])
        at = {each["id"]: each for each in chart["nodes"]}
        self.assertGreater(max(x for x, _ in back["points"]), at["a"]["x"] + at["a"]["w"])
        self.assertFalse(any(each["back"] for each in chart["edges"] if (each["from"], each["to"]) != ("c", "a")))
        assert_clean(self, chart)

    def test_a_state_that_moves_to_itself_is_a_loop(self):
        chart = lay(machine(["a", "b"], [("a", "a", {"n": {"lt": 3}}), ("a", "b")]))
        self.assertTrue(next(each for each in chart["edges"] if each["from"] == each["to"])["back"])
        assert_clean(self, chart)

    def test_a_state_nothing_leads_to_is_still_drawn(self):
        chart = lay(machine(["a", "b", "lost"], [("a", "b")]))
        self.assertEqual({each["id"] for each in chart["nodes"]}, {"a", "b", "lost"})
        assert_clean(self, chart)

    def test_two_moves_between_the_same_states_with_the_same_guard_are_one_arrow(self):
        chart = lay(machine(["a", "b"], [("a", "b"), ("a", "b")]))
        self.assertEqual(len(chart["edges"]), 1)


class LabelTests(unittest.TestCase):
    def test_a_guarded_move_is_labeled_with_its_guard_and_a_plain_move_is_not(self):
        chart = lay(machine(["a", "b", "c"], [("a", "b", {"any": {"eq": True}}), ("a", "c")]))
        by = {(each["from"], each["to"]): each for each in chart["edges"]}
        self.assertEqual(by["a", "b"]["label"], "any = true")
        self.assertNotIn("label", by["a", "c"])
        self.assertNotIn("label_box", by["a", "c"])

    def test_a_guard_is_written_the_way_a_person_would_say_it(self):
        self.assertEqual(guard_text({"any": {"eq": True}}), "any = true")
        self.assertEqual(guard_text({"count": {"lt": 3}}), "count < 3")
        self.assertEqual(guard_text({"kind": {"in": ["a", "b"]}}), "kind in a, b")
        self.assertEqual(guard_text({"and": [{"a": {"eq": 1}}, {"b": {"ne": 2}}]}), "a = 1 and b != 2")
        self.assertEqual(guard_text({"or": [{"a": {"eq": 1}}, {"b": {"eq": 2}}]}), "a = 1 or b = 2")
        self.assertEqual(guard_text({"not": {"a": {"eq": 1}}}), "not a = 1")

    def test_a_long_guard_is_cut_short_with_dots(self):
        text = guard_text({"a_very_long_field_name_indeed": {"eq": "a very long value that goes on and on"}})
        self.assertLessEqual(len(text), 32)
        self.assertTrue(text.endswith("..."))

    def test_many_labeled_arrows_leave_no_two_labels_on_each_other(self):
        names = ["start", *[f"s{n}" for n in range(8)], "end"]
        moves = [("start", f"s{n}", {"pick": {"eq": f"option {n}"}}) for n in range(8)]
        moves += [(f"s{n}", "end", {"done": {"eq": n}}) for n in range(8)]
        assert_clean(self, lay(machine(names, moves, final={"end"})))


class ScaleTests(unittest.TestCase):
    def test_a_machine_of_forty_states_is_drawn_without_overlaps(self):
        for seed in range(6):
            rng = random.Random(seed)
            names = [f"state_{n}" for n in range(40)]
            moves = [(names[rng.randrange(0, n)], names[n], *guard(rng, n)) for n in range(1, 40)]
            for _ in range(15):  # extra moves forward, skipping layers, and back to earlier states
                a, b = rng.randrange(40), rng.randrange(40)
                moves.append((names[a], names[b], *guard(rng, a)))
            chart = lay(machine(names, moves, final={names[-1]}))
            self.assertEqual(len(chart["nodes"]), 40)
            assert_clean(self, chart)

    def test_a_wide_fan_wraps_into_rows_instead_of_running_off_the_page(self):
        names = ["root", *[f"child_{n}" for n in range(20)]]
        chart = lay(machine(names, [("root", name) for name in names[1:]]))
        self.assertLess(chart["width"], 1800)
        assert_clean(self, chart)

    def test_the_drawing_is_as_big_as_its_contents(self):
        chart = lay(machine(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"), ("d", "a")]))
        for each in chart["nodes"]:
            self.assertGreaterEqual(each["x"], 0)
            self.assertLessEqual(each["x"] + each["w"], chart["width"])
            self.assertLessEqual(each["y"] + each["h"], chart["height"])
        for edge in chart["edges"]:
            for x, y in edge["points"]:
                self.assertTrue(0 <= x <= chart["width"] and 0 <= y <= chart["height"], (x, y))

    def test_the_same_machine_always_gives_the_same_drawing(self):
        story = machine(["a", "b", "c"], [("a", "b"), ("a", "c"), ("c", "b")])
        self.assertEqual(json.dumps(lay(story)), json.dumps(lay(story)))


class RealMachineTests(unittest.TestCase):
    def test_the_examples_machines_are_drawn_cleanly(self):
        for path in ("examples/household/household.yaml", "examples/evening/evening.yaml", "tests/fixtures/coffee/coffee_week.yaml"):
            story = _story_of(load(ROOT / path, variables={"monarch": "m.csv", "amex": "a.csv", "amex_account": "x"}))
            chart = lay(story)
            self.assertEqual({each["id"] for each in chart["nodes"]}, {state["name"] for state in story["states"]}, path)
            assert_clean(self, chart)


class OverlayTests(unittest.TestCase):
    STORY = machine(["a", "b", "c"], [("a", "b"), ("b", "c")], final={"c"})

    def events(self, *entered):
        return [{"event": "run_started", **self.STORY}, *({"event": "state_entered", "state": s, "caused_by": c} for s, c in entered)]

    def test_the_state_the_run_is_in_is_lit_and_the_move_just_taken_is_marked(self):
        chart = overlay(self.STORY, self.events(("a", "start"), ("b", "ok")), "running", "")
        self.assertEqual({each["id"] for each in chart["nodes"] if each["current"]}, {"b"})
        self.assertEqual(chart["last_move"], {"from": "a", "to": "b"})
        self.assertEqual({(each["from"], each["to"]) for each in chart["edges"] if each["taken"]}, {("a", "b")})
        self.assertEqual(chart["ended"], "")

    def test_before_the_first_move_nothing_is_lit(self):
        chart = overlay(self.STORY, self.events(), "running", "")
        self.assertFalse(any(each["current"] for each in chart["nodes"]))
        self.assertIsNone(chart["last_move"])

    def test_a_finished_run_keeps_its_last_state_lit_and_says_how_it_ended(self):
        chart = overlay(self.STORY, self.events(("a", "start"), ("b", "ok"), ("c", "ok")), "done", "done after 3 stages")
        self.assertEqual({each["id"] for each in chart["nodes"] if each["current"]}, {"c"})
        self.assertEqual(chart["ended"], "done after 3 stages")

    def test_the_initial_state_comes_from_the_first_move_when_the_story_line_has_none(self):
        story = {key: value for key, value in self.STORY.items() if key != "initial"}
        chart = overlay(story, [{"event": "state_entered", "state": "b", "caused_by": "start"}], "running", "")
        self.assertTrue(next(each for each in chart["nodes"] if each["id"] == "b")["initial"])

    def test_a_state_name_with_markup_is_kept_as_plain_text(self):
        name, guard = "<script>alert(1)</script>", {"<img src=x onerror=y>": {"eq": 1}}
        hostile = machine([name, "b"], [(name, "b", guard)])
        chart = lay(hostile)
        self.assertEqual(chart["nodes"][0]["id"], "<script>alert(1)</script>")
        self.assertIn("<img src=x onerror=y>", chart["edges"][0]["label"])
        json.dumps(chart)  # it is data, and it serializes


class DescribeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)

    def write(self, events, manifest):
        (self.dir / "events.jsonl").write_text("".join(json.dumps(each) + "\n" for each in events), encoding="utf-8")
        (self.dir / "run.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_a_run_with_a_story_has_a_chart_with_its_lit_state(self):
        story = machine(["a", "b"], [("a", "b")], final={"b"})
        self.write([{"event": "run_started", "at": "2026-11-01T10:00:00+00:00", "sketch": "x/s.yaml", "mode": "live", **story},
                    {"event": "state_entered", "at": "2026-11-01T10:00:00+00:00", "state": "a", "caused_by": "start"}],
                   {"status": "running", "stages": {}})
        chart = describe(self.dir)["chart"]
        self.assertEqual({each["id"] for each in chart["nodes"] if each["current"]}, {"a"})

    def test_a_run_whose_log_has_no_story_has_no_chart(self):
        self.write([{"event": "run_started", "at": "2026-11-01T10:00:00+00:00", "sketch": "x/s.yaml", "mode": "live"}],
                   {"status": "running", "stages": {}})
        self.assertIsNone(describe(self.dir)["chart"])


if __name__ == "__main__":
    unittest.main()
