"""UND-101: the part of a sketch's load that does not depend on a row's values is read once per file version."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.paths import ROOT
from src.play import loader
from src.play.loader import PlayError, load, read_template

CHILD = """name: child
description: reads {{ thing }}
inputs:
  mood: { kind: choice, label: Mood, options: [fun, serious], default: fun }
machine: { initial: only, states: { only: { final: true } } }
"""


class CacheCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.path = self.dir / "child.yaml"
        self.path.write_text(CHILD, encoding="utf-8")
        loader._template.cache_clear()
        self.addCleanup(loader._template.cache_clear)

    def reads_without_values(self):
        """Wrap `_parse` and count the calls that do not depend on a row: no values given, read leniently."""
        calls = []
        real = loader._parse

        def spy(path, text, variables, lenient):
            calls.append((variables, lenient))
            return real(path, text, variables, lenient)

        return calls, patch.object(loader, "_parse", spy)


class CountTests(CacheCase):
    def test_a_child_loaded_for_many_rows_is_read_without_values_only_once(self):
        calls, spy = self.reads_without_values()
        with spy:
            for thing in ("a", "b", "c", "d"):
                load(self.path, variables={"thing": thing})
        row_free = [call for call in calls if call == ({}, True)]
        with_values = [call for call in calls if call != ({}, True)]
        self.assertEqual(len(row_free), 1)
        self.assertEqual(len(with_values), 4)  # each row's own values are still rendered and parsed

    def test_each_rows_values_still_reach_the_loaded_sketch(self):
        first, second = load(self.path, variables={"thing": "x"}), load(self.path, variables={"thing": "y"})
        self.assertEqual((first.description, second.description), ("reads x", "reads y"))

    def test_the_listing_of_sketches_shares_the_same_read(self):
        calls, spy = self.reads_without_values()
        with spy:
            read_template(self.path)
            read_template(self.path)
            load(self.path, variables={"thing": "z"})
        self.assertEqual([call for call in calls if call == ({}, True)].__len__(), 1)


class ChangeTests(CacheCase):
    def test_a_file_edited_between_loads_is_read_again(self):
        self.assertEqual(list(read_template(self.path)[0]["inputs"]), ["mood"])
        self.path.write_text(CHILD.replace("mood:", "tone:"), encoding="utf-8")
        self.assertEqual(list(read_template(self.path)[0]["inputs"]), ["tone"])

    def test_a_same_length_edit_is_seen_even_when_the_modification_time_is_the_same(self):
        # two writes in the same clock tick share a modification time; only the content tells them apart
        before = self.path.stat()
        read_template(self.path)
        text = CHILD.replace("fun, serious", "fan, serious")  # same length
        self.assertEqual(len(text), len(CHILD))
        self.path.write_text(text, encoding="utf-8")
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))  # as if it had not moved
        self.assertEqual(self.path.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertIn("fan", read_template(self.path)[0]["inputs"]["mood"]["options"])

    def test_a_file_that_is_not_valid_is_refused_every_time_and_loads_once_fixed(self):
        self.path.write_text("name: [unclosed\n", encoding="utf-8")
        for _ in range(2):
            with self.assertRaises(PlayError):
                load(self.path, variables={"thing": "x"})
        self.path.write_text(CHILD, encoding="utf-8")
        self.assertEqual(load(self.path, variables={"thing": "x"}).name, "child")

    def test_a_file_that_is_not_there_is_refused_as_before(self):
        with self.assertRaises(PlayError) as refused:
            load(self.dir / "nothing.yaml")
        self.assertIn("cannot be read", refused.exception.problems[0])


class SafetyTests(CacheCase):
    def test_a_caller_that_changes_what_it_was_given_does_not_change_the_next_answer(self):
        document, _ = read_template(self.path)
        document["inputs"]["mood"]["options"].append("ruined")
        document["name"] = "changed"
        again, _ = read_template(self.path)
        self.assertEqual((again["name"], again["inputs"]["mood"]["options"]), ("child", ["fun", "serious"]))

    def test_a_loaded_sketchs_inputs_are_its_own_and_changing_them_changes_no_later_load(self):
        first = load(self.path, variables={"thing": "x"})
        first.inputs["mood"]["options"].append("ruined")
        second = load(self.path, variables={"thing": "y"})
        self.assertEqual(second.inputs["mood"]["options"], ["fun", "serious"])

    def test_the_cached_load_equals_the_uncached_load_for_a_real_sketch(self):
        household = ROOT / "examples" / "household" / "categorize_merchant.yaml"
        values = {"merchant": [{"merchant": "Store"}], "additions": "additions.jsonl"}
        loader._template.cache_clear()
        cold = load(household, variables=values, lenient=True)
        warm = load(household, variables=values, lenient=True)
        self.assertEqual(cold, warm)
