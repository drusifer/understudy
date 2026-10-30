import io
import json
import tempfile
import unittest
from pathlib import Path

from src.paths import ROOT
from src.sketch.cli import main

SEATING = ROOT / "tests" / "fixtures" / "evening" / "seating.yaml"


class SeatingCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.out = Path(directory.name) / "out"

    def seat(self, **values):
        """Run the seating sketch with `--with name=value` and return its holds, best first."""
        flags = [flag for name, value in values.items() for flag in ("--with", f"{name}={value}")]
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["run", str(SEATING), "--out", str(self.out), *flags], stdout=stdout, stderr=stderr)
        self.assertEqual((code, stderr.getvalue()), (0, ""))
        wrote = next(line for line in stdout.getvalue().splitlines() if line.startswith("wrote "))
        return [json.loads(line) for line in Path(wrote.removeprefix("wrote ")).read_text(encoding="utf-8").splitlines()]

    def runs(self, **values):
        return [hold["run"] for hold in self.seat(**values)]


class BlockTests(SeatingCase):
    def test_a_party_of_two_gets_blocks_of_two_adjacent_free_seats(self):
        found = self.seat(tickets=2)
        self.assertTrue(found and all(hold["last"] - hold["first"] == 1 for hold in found))

    def test_a_party_of_three_only_gets_blocks_of_three(self):
        found = self.seat(tickets=3, row=0, center=0)
        self.assertTrue(found and all(len(range(hold["first"], hold["last"] + 1)) == 3 for hold in found))  # noqa: PLR2004

    def test_a_taken_seat_splits_a_row(self):
        everything = [hold["run"] for hold in self.seat(tickets=2, row=1, center=1)]
        self.assertNotIn("E5-6", everything)
        self.assertNotIn("E6-7", everything)

    def test_another_showings_seats_are_not_offered(self):
        self.assertEqual(sorted(self.runs(tickets=2, showing="21:00")), ["E1-2", "E2-3"])


class NothingFitsTests(SeatingCase):
    def run_seating(self, **values):
        flags = [flag for name, value in values.items() for flag in ("--with", f"{name}={value}")]
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["run", str(SEATING), "--out", str(self.out), *flags], stdout=stdout, stderr=stderr)
        return code, stdout.getvalue().splitlines(), stderr.getvalue()

    def test_a_party_too_big_for_any_block_ends_in_the_none_outcome_and_writes_nothing(self):
        code, out, err = self.run_seating(tickets=9)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out[-1], "outcome: none")
        self.assertFalse(any(line.startswith("wrote ") for line in out))
        self.assertEqual(list(self.out.glob("*/hold.jsonl")), [])

    def test_a_party_that_fits_does_not_end_in_none(self):
        code, out, _ = self.run_seating(tickets=2)
        self.assertEqual(code, 0)
        self.assertNotIn("outcome: none", out)


class WeightTests(SeatingCase):
    def test_when_only_the_center_matters_a_block_centerd_in_its_row_comes_first(self):
        best = self.seat(tickets=2, row=0, center=1)[0]
        self.assertEqual((best["run"], best["center_score"]), ("D2-3", 1.0))   # D has four seats, so 2-3 is dead center

    def test_when_the_row_matters_a_little_the_central_row_e_block_wins(self):
        self.assertEqual(self.runs(tickets=2, row=0.3, center=1)[0], "E4-5")

    def test_when_only_the_row_matters_a_row_e_block_comes_first_wherever_it_sits(self):
        self.assertEqual(self.runs(tickets=2, row=1, center=0)[0], "E1-2")

    def test_the_holds_are_best_first_and_carry_their_score(self):
        scores = [hold["score"] for hold in self.seat(tickets=2, row=0.7, center=1.0)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_at_most_five_holds_are_kept(self):
        self.assertLessEqual(len(self.seat(tickets=2)), 5)


if __name__ == "__main__":
    unittest.main()
