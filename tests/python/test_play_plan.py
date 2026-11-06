"""UND-111: a play file becomes a plan: its pieces, its beats, who reads what, and the moves between beats."""

import unittest
from typing import ClassVar

from src.paths import ROOT
from src.play.loader import read_template
from src.play.plan import plan

HOUSEHOLD = ROOT / "examples" / "household" / "household.yaml"
EVENING = ROOT / "examples" / "evening" / "evening.yaml"
LINK = ROOT / "examples" / "household" / "link_refund.yaml"


def edges(found, kind):
    return {(each["from"], each["to"]) for each in found["edges"] if each["kind"] == kind}


def node(found, name):
    return next(each for each in found["nodes"] if each["id"] == name)


class SmallPlan(unittest.TestCase):
    document: ClassVar[dict] = {
        "name": "small",
        "stage": {
            "tickets": {"kind": "count", "min": 1, "max": 5, "default": 2},
            "rows": {"kind": "file", "path": "rows.jsonl"},
            "other": {"kind": "file", "path": "other.jsonl"},
            "out": {"kind": "file", "path": "out.jsonl", "access": "write"},
        },
        "scene": {
            "initial": "checker",
            "beats": {
                "checker": {"do": {"reduce": {"action": "any"}}, "with": {"from": "joined"},
                            "transitions": [{"if": {"any": {"eq": False}}, "to": "gone"}, {"to": "writer"}]},
                "writer": {"do": {"write": "out"}, "with": {"from": "joined"}, "to": "done"},
                "done": {"final": True, "outcome": "ok"},
                "gone": {"final": True, "outcome": "none"},
                "joined": {"do": {"map": {"action": "join"}}, "with": {"from": "rows", "other": "other", "on": "k"}},
            },
        },
    }

    def setUp(self):
        self.found = plan(self.document)

    def test_pieces_and_beats_are_nodes_and_props_are_not(self):
        names = {each["id"] for each in self.found["nodes"]}
        self.assertEqual(names, {"rows", "other", "out", "checker", "writer", "done", "gone", "joined"})
        self.assertEqual(self.found["props"], ["tickets"])

    def test_each_node_says_what_it_is(self):
        self.assertEqual(node(self.found, "rows")["kind"], "piece")
        self.assertFalse(node(self.found, "rows")["write"])
        self.assertTrue(node(self.found, "out")["write"])
        self.assertTrue(node(self.found, "checker")["flow"])
        self.assertTrue(node(self.found, "done")["final"])
        self.assertTrue(node(self.found, "joined")["waits"])
        self.assertFalse(node(self.found, "joined")["flow"])
        self.assertEqual(node(self.found, "joined")["action"], "map.join")

    def test_a_move_is_a_to_and_each_transition_with_its_guard(self):
        self.assertEqual(edges(self.found, "move"), {("checker", "gone"), ("checker", "writer"), ("writer", "done")})
        guarded = [each for each in self.found["edges"] if each["kind"] == "move" and each["to"] == "gone"]
        self.assertEqual(guarded[0]["when"], {"any": {"eq": False}})

    def test_a_beat_reads_what_its_from_and_other_name(self):
        self.assertEqual(edges(self.found, "reads"),
                         {("rows", "joined"), ("other", "joined"), ("joined", "checker"), ("joined", "writer")})

    def test_a_write_beat_writes_its_piece(self):
        self.assertEqual(edges(self.found, "writes"), {("writer", "out")})

    def test_the_scene_starts_at_the_initial_beat(self):
        self.assertEqual(self.found["initial"], "checker")


class RealPlans(unittest.TestCase):
    def test_jev_beat_reads_the_pieces_of_its_options_and_state(self):
        found = plan(read_template(LINK)[0])
        self.assertTrue({("charges", "reading"), ("facts", "reading")} <= edges(found, "reads"))
        self.assertEqual(node(found, "reading")["action"], "jev.choice")

    def test_a_play_call_reads_the_pieces_it_loops_over_and_the_ones_it_binds(self):
        found = plan(read_template(EVENING)[0])
        self.assertIn(("films", "scored"), edges(found, "reads"))
        self.assertIn(("chosen", "booked"), edges(found, "reads"))
        self.assertEqual(node(found, "scored")["action"], "play:review_score.yaml")

    def test_every_edge_ends_are_nodes_in_the_household(self):
        found = plan(read_template(HOUSEHOLD)[0])
        names = {each["id"] for each in found["nodes"]}
        for each in found["edges"]:
            self.assertIn(each["from"], names)
            self.assertIn(each["to"], names)
        self.assertTrue(any(each["flow"] for each in found["nodes"]))
        self.assertTrue(edges(found, "writes"))


if __name__ == "__main__":
    unittest.main()
