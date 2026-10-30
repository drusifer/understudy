import io
import json
import tempfile
import unittest
from pathlib import Path

from jev_double import JevDouble

from src.jev import Chosen
from src.paths import ROOT
from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

EVENING = ROOT / "examples" / "evening" / "evening.yaml"
MAX_SHORTLIST = 5


def reading(state, instructions, options):
    """A scripted Jev. Asked about reviews it answers by what they say; asked to pick, it takes the first option."""
    if "reviews" in state:
        text = " ".join(row["text"] for row in state["reviews"])
        level = ("loved" if "loved" in text else "solid" if "recommend" in text or "solid" in text
                 else "bored" if "walked out" in text or "Boring" in text else "mixed")
    else:
        level = next(iter(options))
    return Chosen(level, 0.9, {option: 1.0 if option == level else 0.0 for option in options})


class EveningCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.out = self.dir / "out"
        self.store = CaptureStore(self.dir / "cache")
        self.jev = JevDouble(choose_fn=reading)

    def go(self, *flags, jev=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["run", str(EVENING), "--out", str(self.out), *flags], make_jev=lambda: jev or self.jev,
                    store=self.store, stdout=stdout, stderr=stderr)
        return code, stdout.getvalue().splitlines(), stderr.getvalue()

    def withs(self, **values):
        return [flag for name, value in values.items() for flag in ("--with", f"{name}={value}")]

    def booking(self, lines) -> list[dict]:
        wrote = next(line for line in lines if line.startswith("wrote "))
        return [json.loads(row) for row in Path(wrote.removeprefix("wrote ")).read_text(encoding="utf-8").splitlines()]

    def pick_request(self):
        """The Jev request that chose a showing: the one whose options are showings."""
        return next(request for request in self.jev.requests if any(" " in option and ":" in option for option in request[3]))

    def offered(self):
        return list(self.pick_request()[3])


class BookingTests(EveningCase):
    def test_the_evening_books_a_showing_that_obeys_the_owners_rules(self):
        code, lines, err = self.go()
        self.assertEqual((code, err, lines[-1]), (0, "", "outcome: booked"))
        (booking,) = self.booking(lines)
        offered = self.offered()
        self.assertIn(booking["showing"], offered)
        self.assertLessEqual(len(offered), MAX_SHORTLIST)
        for dropped in ("Sharknado 20:00", "Barbie 21:30", "Alien 15:00"):   # too low, not horror and under 91, afternoon
            self.assertNotIn(dropped, offered)
        self.assertIn(booking["row"], ("E", "F", "D"))

    def test_jev_is_asked_about_every_films_reviews_and_then_to_pick(self):
        self.go()
        kinds = ["reviews" if "reviews" in request[1] else "pick" for request in self.jev.requests]
        self.assertEqual(kinds.count("reviews"), 8)
        self.assertEqual(kinds.count("pick"), 1)


class InputTests(EveningCase):
    def test_evenings_off_admits_an_afternoon_showing(self):
        self.go()
        self.assertNotIn("Alien 15:00", self.offered())
        self.jev.requests.clear()
        self.go(*self.withs(evenings="off"))
        self.assertIn("Alien 15:00", self.offered())

    def test_tickets_sets_the_length_of_the_block_booked(self):
        _, lines, _ = self.go(*self.withs(tickets=3))
        (booking,) = self.booking(lines)
        self.assertEqual(booking["last"] - booking["first"] + 1, 3)

    def test_the_row_and_center_weights_change_the_seats_booked(self):
        _, row_lines, _ = self.go(*self.withs(row=1, center=0))
        _, center_lines, _ = self.go(*self.withs(row=0, center=1))
        (by_row,), (by_center,) = self.booking(row_lines), self.booking(center_lines)
        self.assertNotEqual(by_row["run"], by_center["run"])

    def test_the_mood_is_shown_to_jev(self):
        self.go(*self.withs(mood="romantic"))
        self.assertTrue(all("romantic" in request[2] for request in self.jev.requests))


class WalkAwayTests(EveningCase):
    def test_nothing_qualifying_ends_successfully_and_books_nothing(self):
        only_low = self.dir / "low.jsonl"
        only_low.write_text(json.dumps({"showing": "Sharknado 20:00", "title": "Sharknado", "starts": "20:00",
                                        "genre": "horror", "tomato": 40}) + "\n", encoding="utf-8")
        code, lines, err = self.go("--source", f"showings.path={only_low}")
        self.assertEqual((code, err, lines[-1]), (0, "", "outcome: walked_away"))
        self.assertFalse(any(line.startswith("wrote ") for line in lines))

    def test_a_party_too_big_for_any_block_walks_away(self):
        code, lines, err = self.go(*self.withs(tickets=9))
        self.assertEqual((code, err, lines[-1]), (0, "", "outcome: walked_away"))
        self.assertEqual(list(self.out.glob("*/booking.jsonl")), [])


class FailureTests(EveningCase):
    def test_a_missing_showings_file_is_refused_naming_it(self):
        code, lines, err = self.go("--source", f"showings.path={self.dir / 'nope.jsonl'}")
        self.assertEqual((code, lines), (2, []))
        self.assertIn("nope.jsonl", err)

    def test_check_passes_on_the_example(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        self.assertEqual(main(["check", str(EVENING)], stdout=stdout, stderr=stderr), 0)
        self.assertEqual(stdout.getvalue(), "ok: evening\n")


class ReplayTests(EveningCase):
    def test_a_captured_run_replays_offline_with_the_same_booking(self):
        _, lines, _ = self.go()
        first = self.booking(lines)
        stdout, stderr = io.StringIO(), io.StringIO()
        code = main(["run", str(EVENING), "--out", str(self.out), "--replay"], make_jev=lambda: self.fail("went live"),
                    store=self.store, stdout=stdout, stderr=stderr)
        self.assertEqual((code, stderr.getvalue()), (0, ""))
        self.assertEqual(self.booking(stdout.getvalue().splitlines()), first)


if __name__ == "__main__":
    unittest.main()
