"""UND-97: Jev puts every merchant in a category of the clean list, in two steps, without seeing the export's categories.

The two-step choice and its thresholds belong to the child sketch `categorize_merchant`, so they are tested on it directly
with the scripted Jev (`categorize`); what the household does with the answers (the records, the review list) is tested on
its own stages with `decided` written from those answers. No whole run is needed; the wiring is checked once in
`test_household.LedgerTests`.
"""

import json
import unittest

from household_fragment import ORACLE, categorize, decided, fragment, merchants_of
from household_jev import PLAN

from src.play.mcc import load_mcc

ISO = load_mcc()
HOUSEHOLD = ("Rent", "Mortgage", "Tuition", "Income", "Transfer", "Loan repayment")
TAXONOMY = {f"{group}: {name}" for group, names in ISO.items() for name in names} | {f"Household: {name}" for name in HOUSEHOLD}
MERCHANTS = {merchant["payee"]: merchant for merchant in merchants_of()}


def questions(double):
    """The questions the double was asked, in order: ('groups' or 'name', the options offered)."""
    return [("groups" if "groups" in state else "name", list(options)) for _, state, _, options in double.requests]


class TwoStepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answers = {payee: categorize(merchant) for payee, merchant in MERCHANTS.items()}

    def test_a_merchant_is_asked_a_group_and_then_a_name_in_that_group(self):
        group_step, name_step = questions(self.answers["Store"][1])
        self.assertEqual(group_step[0], "groups")
        self.assertEqual(set(group_step[1]), {*ISO, "Household", "none_of_these"})
        self.assertEqual((name_step[0], name_step[1]), ("name", sorted(ISO["Retail outlets"])))

    def test_the_group_step_shows_jev_every_name_in_each_group_so_it_can_tell_what_a_group_covers(self):
        states = [state for _, state, _, _ in self.answers["Store"][1].requests if "groups" in state]
        names = {row["group"]: row["names"] for row in states[0]["groups"]}
        self.assertEqual(set(names), {*ISO, "Household"})
        self.assertEqual(sorted(names["Retail outlets"]), sorted(ISO["Retail outlets"]))
        self.assertIn("Rent", names["Household"])

    def test_a_merchant_that_fits_no_group_is_never_asked_for_a_name(self):
        self.assertEqual([step for step, _ in questions(self.answers["Venmo"][1])], ["groups"])

    def test_both_answers_above_point_seven_place_the_merchant_in_group_and_name(self):
        store, employer = self.answers["Store"][0], self.answers["Employer"][0]
        self.assertEqual((store["status"], store["level"]), ("placed", "Retail outlets: Bakeries"))
        self.assertEqual((employer["status"], employer["level"]), ("placed", "Household: Income"))

    def test_an_answer_under_point_seven_is_placed_when_it_is_clearly_ahead_of_the_runner_up(self):
        dunkin = self.answers["Dunkin'"][0]  # 0.55 and 0.50, with nothing near them
        self.assertEqual((dunkin["status"], dunkin["level"]), ("placed", "Retail outlets: Bakeries"))

    def test_two_close_answers_send_the_merchant_to_review_even_when_the_top_one_is_over_point_four(self):
        plan = {**PLAN, "Store": ("Retail outlets", 0.45, "Bakeries", 0.9, ("Utilities", 0.43))}
        store, _ = categorize(MERCHANTS["Store"], plan)
        self.assertEqual((store["status"], store["probability"]), ("review", 0.45))

    def test_an_answer_under_point_four_is_for_review_however_far_ahead_it_is(self):
        self.assertEqual(self.answers["Shoe Shop"][0]["status"], "review")

    def test_an_answer_the_run_is_not_sure_of_is_for_review_with_the_least_sure_probability(self):
        shoes = self.answers["Shoe Shop"][0]
        self.assertEqual((shoes["level"], shoes["probability"], shoes["status"]),
                         ("Clothing outlets: Family clothing shops", 0.35, "review"))

    def test_a_merchant_that_fits_no_group_goes_to_review_as_none_of_these(self):
        venmo = self.answers["Venmo"][0]
        self.assertEqual((venmo["level"], venmo["status"]), ("none_of_these", "review"))

    def test_every_category_chosen_is_in_the_clean_list(self):
        chosen = {row["level"] for row, _ in self.answers.values() if row["status"] == "placed"}
        self.assertTrue(chosen)
        self.assertLessEqual(chosen, TAXONOMY)


class WhatTheHouseholdMakesOfThemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = decided()
        cls.records, _ = fragment("finished", decided=cls.rows)
        cls.review, _ = fragment("review_list", decided=cls.rows)

    def record(self, payee):
        return next(r for r in self.records if r["payee"] == payee and r["kind"] in ("purchase", "credit"))

    def test_a_placed_merchants_records_carry_the_category_the_status_and_that_jev_chose_it(self):
        store = self.record("Store")
        self.assertEqual((store["category_status"], store["category_level"], store["category_source"]),
                         ("placed", "Retail outlets: Bakeries", "jev"))
        self.assertEqual(self.record("Employer")["category_level"], "Household: Income")

    def test_a_merchant_for_review_keeps_its_records_without_a_category(self):
        shoes = self.record("Shoe Shop")
        self.assertEqual(shoes["category_status"], "review")
        self.assertIsNone(shoes.get("category_level"))

    def test_the_review_list_names_the_guess_and_how_sure_and_why(self):
        by = {line["payee"]: line for line in self.review}
        self.assertEqual((by["Shoe Shop"]["top"], by["Shoe Shop"]["top_probability"], by["Shoe Shop"]["reason"]),
                         ("Clothing outlets: Family clothing shops", 0.35, "below_0.7"))
        self.assertEqual((by["Venmo"]["top"], by["Venmo"]["reason"]), ("none_of_these", "none_of_these"))

    def test_close_answers_are_in_the_review_list_with_the_top_probability(self):
        plan = {**PLAN, "Store": ("Retail outlets", 0.45, "Bakeries", 0.9, ("Utilities", 0.43))}
        review, _ = fragment("review_list", decided=decided(plan))
        (store,) = (line for line in review if line["payee"] == "Store")
        self.assertEqual((store["top_probability"], store["reason"]), (0.45, "below_0.7"))


class ExportCategoriesAreNotUsedTests(unittest.TestCase):
    def test_what_jev_is_given_about_a_merchant_holds_no_export_category(self):
        export = {line.split(",")[2].strip('"') for line in (ORACLE / "monarch.csv").read_text(encoding="utf-8").splitlines()[1:]}
        in_the_list = {name for names in ISO.values() for name in names} | {"Transfer", "Income", "Rent"}  # words both use
        self.assertEqual({tuple(sorted(m)) for m in MERCHANTS.values()},
                         {("amounts", "count", "descriptions", "key", "payee", "statements")})
        shown = json.dumps(list(MERCHANTS.values()))
        for category in export - in_the_list:
            self.assertNotIn(category, shown)

    def test_the_same_merchants_are_given_to_jev_whatever_the_export_says(self):
        original = (ORACLE / "monarch.csv").read_text(encoding="utf-8")

        def scramble(line: str) -> str:  # every category, whatever it says
            return line.replace(line.split(",")[2], '"Scrambled: Nonsense"', 1)

        scrambled = "\n".join(line if i == 0 else scramble(line) for i, line in enumerate(original.splitlines())) + "\n"
        self.assertNotEqual(scrambled, original)
        self.assertEqual(merchants_of(monarch=scrambled), merchants_of())


if __name__ == "__main__":
    unittest.main()
