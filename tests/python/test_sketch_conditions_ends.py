import unittest

from src.sketch.conditions import holds
from src.sketch.vocabulary import OPERATORS


class EndsTests(unittest.TestCase):
    def test_text_that_ends_with_the_operand_matches(self):
        self.assertTrue(holds({"Category": {"ends": ": Transfers"}}, {"Category": "Transportation: Transfers"}))

    def test_text_that_only_contains_or_starts_with_it_does_not(self):
        self.assertFalse(holds({"Category": {"ends": ": Transfer"}}, {"Category": "Shopping: Transferware"}))
        self.assertFalse(holds({"Category": {"ends": "Transfer"}}, {"Category": "Transfer Fees"}))

    def test_a_value_that_is_not_text_and_a_missing_field_never_match(self):
        self.assertFalse(holds({"n": {"ends": "1"}}, {"n": 11}))
        self.assertFalse(holds({"Category": {"ends": "x"}}, {}))

    def test_ends_is_one_of_the_operators(self):
        self.assertIn("ends", OPERATORS)


if __name__ == "__main__":
    unittest.main()
