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
        found = self.seat(tickets=3, row=0, centre=0)
        self.assertTrue(all(hold["last"] - hold["first"] == 2 for hold in found))

    def test_a_taken_seat_splits_a_row(self):
        everything = [hold["run"] for hold in self.seat(tickets=2, row=1, centre=1)]
        self.assertNotIn("E5-6", everything)
        self.assertNotIn("E6-7", everything)

    def test_another_showings_seats_are_not_offered(self):
        self.assertEqual(sorted(self.runs(tickets=2, showing="21:00")), ["E1-2", "E2-3"])


class WeightTests(SeatingCase):
    def test_when_only_the_centre_matters_a_block_centred_in_its_row_comes_first(self):
        best = self.seat(tickets=2, row=0, centre=1)[0]
        self.assertEqual((best["run"], best["centre_score"]), ("D2-3", 1.0))   # D has four seats, so 2-3 is dead centre

    def test_when_the_row_matters_a_little_the_central_row_e_block_wins(self):
        self.assertEqual(self.runs(tickets=2, row=0.3, centre=1)[0], "E4-5")

    def test_when_only_the_row_matters_a_row_e_block_comes_first_wherever_it_sits(self):
        self.assertEqual(self.runs(tickets=2, row=1, centre=0)[0], "E1-2")

    def test_the_holds_are_best_first_and_carry_their_score(self):
        scores = [hold["score"] for hold in self.seat(tickets=2, row=0.7, centre=1.0)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_at_most_five_holds_are_kept(self):
        self.assertLessEqual(len(self.seat(tickets=2)), 5)


if __name__ == "__main__":
    unittest.main()
