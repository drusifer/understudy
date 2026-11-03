import json
import tempfile
import unittest
from pathlib import Path

from src.dashboard.spending import MAX_BYTES, read_spending
from src.dashboard.view import describe


def lines(*rows):
    return "".join(json.dumps(row) + "\n" for row in rows)


def row(category, amount, share=0.01, count=1):
    return {"category": category, "amount": amount, "share": share, "count": count}


class SpendingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)

    def write(self, text):
        (self.dir / "spending.jsonl").write_text(text, encoding="utf-8")

    def test_a_run_without_the_file_has_no_spending_at_all(self):
        self.assertIsNone(read_spending(self.dir))

    def test_the_ten_largest_categories_come_first_and_the_rest_are_counted(self):
        self.write(lines(*(row(f"cat {n}", 100 - n) for n in range(13))))
        found = read_spending(self.dir)
        self.assertEqual([each["category"] for each in found["top"]], [f"cat {n}" for n in range(10)])
        self.assertEqual((found["more"], found["problem"]), (3, None))

    def test_a_list_given_out_of_order_is_shown_largest_first(self):
        self.write(lines(row("small", 5), row("big", 500), row("middle", 50)))
        self.assertEqual([each["category"] for each in read_spending(self.dir)["top"]], ["big", "middle", "small"])

    def test_each_line_gives_the_category_amount_and_share(self):
        self.write(lines(row("Rent", 60807.08, 0.1505, 14)))
        self.assertEqual(read_spending(self.dir)["top"], [{"category": "Rent", "amount": 60807.08, "share": 0.1505}])

    def test_an_empty_file_is_a_run_with_no_spending(self):
        self.write("")
        self.assertEqual(read_spending(self.dir), {"top": [], "more": 0, "problem": None})

    def test_an_unreadable_line_is_named_and_nothing_else_is_shown(self):
        self.write(lines(row("Rent", 5)) + "not json\n")
        self.assertEqual(read_spending(self.dir), {"top": [], "more": 0, "problem": "spending.jsonl line 2 is not readable"})

    def test_a_line_without_the_fields_is_unreadable_too(self):
        self.write(lines({"category": "Rent"}))
        self.assertEqual(read_spending(self.dir)["problem"], "spending.jsonl line 1 is not readable")

    def test_a_file_over_the_size_cap_is_unreadable_and_is_not_read(self):
        self.write("x" * (MAX_BYTES + 1))
        self.assertEqual(read_spending(self.dir)["problem"], "spending.jsonl is too large to show")

    def test_describe_carries_it_and_a_run_without_the_file_carries_none(self):
        self.write(lines(row("Rent", 5)))
        self.assertEqual(describe(self.dir)["spending"]["top"][0]["category"], "Rent")
        (self.dir / "spending.jsonl").unlink()
        self.assertIsNone(describe(self.dir)["spending"])


if __name__ == "__main__":
    unittest.main()
