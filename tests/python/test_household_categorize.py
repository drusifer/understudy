"""UND-97: Jev puts every merchant in a category of the clean list, in two steps, without seeing the export's categories."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from household_jev import PLAN, choose
from jev_double import JevDouble
from test_household import LEDGER, ORACLE, lines, no_pins

from src.sketch.cli import main
from src.sketch.mcc import load_mcc
from src.sketch.sources.capture import CaptureStore

ISO = load_mcc()


def run_household(monarch_text: str | None = None, *extra, plan=None):
    """Run the household with the scripted Jev; returns the exit code, the Jev double, the records and the review lines."""
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        monarch = ORACLE / "monarch.csv"
        if monarch_text is not None:
            monarch = directory / "monarch.csv"
            monarch.write_text(monarch_text, encoding="utf-8")
        double = JevDouble(choose_fn=lambda state, instructions, options: choose(state, instructions, options, plan))
        stderr = io.StringIO()
        code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={monarch}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01",
             *no_pins(directory), *extra],
            make_jev=lambda: double, store=CaptureStore(directory / "cache"), stdout=io.StringIO(), stderr=stderr)
        (folder,) = (directory / "out").iterdir()
        return code, double, lines(folder / "records.jsonl"), lines(folder / "review.jsonl"), stderr.getvalue()


def merchant_questions(double, merchant):
    """The questions asked about one merchant, in order: ('groups' or 'name', the options offered)."""
    asked = []
    for _, state, _, options in double.requests:
        if "merchant" in state and state["merchant"][0]["merchant"] == merchant:
            asked.append(("groups" if "groups" in state else "name", list(options)))
    return asked


class TwoStepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code, cls.double, cls.records, cls.review, cls.err = run_household()
        assert code == 0, cls.err

    def test_a_merchant_is_asked_a_group_and_then_a_name_in_that_group(self):
        group_step, name_step = merchant_questions(self.double, "Store")
        self.assertEqual(group_step[0], "groups")
        self.assertEqual(set(group_step[1]), {*ISO, "Household", "none_of_these"})
        self.assertEqual((name_step[0], name_step[1]), ("name", sorted(ISO["Retail outlets"])))

    def test_the_group_step_shows_jev_every_name_in_each_group_so_it_can_tell_what_a_group_covers(self):
        states = [state for _, state, _, _ in self.double.requests if "groups" in state]
        names = {row["group"]: row["names"] for row in states[0]["groups"]}
        self.assertEqual(set(names), {*ISO, "Household"})
        self.assertEqual(sorted(names["Retail outlets"]), sorted(ISO["Retail outlets"]))
        self.assertIn("Rent", names["Household"])

    def test_a_merchant_that_fits_no_group_is_never_asked_for_a_name(self):
        self.assertEqual([step for step, _ in merchant_questions(self.double, "Venmo")], ["groups"])

    def test_both_answers_above_point_seven_place_the_merchant_in_group_and_name(self):
        by = {(r["payee"], r["kind"]): r for r in self.records}
        store = by["Store", "purchase"]
        self.assertEqual((store["category_status"], store["category_level"], store["category_source"]),
                         ("placed", "Retail outlets: Bakeries", "jev"))
        employer = by["Employer", "credit"]
        self.assertEqual((employer["category_level"], employer["category_source"]), ("Household: Income", "jev"))

    def test_an_answer_under_point_seven_is_placed_when_it_is_clearly_ahead_of_the_runner_up(self):
        by = {(r["payee"], r["kind"]): r for r in self.records}
        dunkin = by["Dunkin'", "purchase"]  # 0.55 and 0.50, with nothing near them
        self.assertEqual((dunkin["category_status"], dunkin["category_level"]), ("placed", "Retail outlets: Bakeries"))

    def test_two_close_answers_send_the_merchant_to_review_even_when_the_top_one_is_over_point_four(self):
        plan = {**PLAN, "Store": ("Retail outlets", 0.45, "Bakeries", 0.9, ("Utilities", 0.43))}
        _, _, records, review, _ = run_household(plan=plan)
        self.assertEqual({r["category_status"] for r in records if r["payee"] == "Store" and r["kind"] == "purchase"}, {"review"})
        (store,) = (line for line in review if line["payee"] == "Store")
        self.assertEqual((store["top_probability"], store["reason"]), (0.45, "below_0.7"))

    def test_an_answer_under_point_four_is_for_review_however_far_ahead_it_is(self):
        by = {(r["payee"], r["kind"]): r for r in self.records}
        self.assertEqual(by["Shoe Shop", "purchase"]["category_status"], "review")

    def test_an_answer_the_run_is_not_sure_of_sends_the_merchant_to_review_with_the_least_sure_probability(self):
        (shoes,) = (line for line in self.review if line["payee"] == "Shoe Shop")
        self.assertEqual((shoes["top"], shoes["top_probability"], shoes["reason"]),
                         ("Clothing outlets: Family clothing shops", 0.35, "below_0.7"))
        record = next(r for r in self.records if r["payee"] == "Shoe Shop" and r["kind"] == "purchase")
        self.assertEqual(record["category_status"], "review")
        self.assertIsNone(record.get("category_level"))

    def test_a_merchant_that_fits_no_group_goes_to_review_as_none_of_these(self):
        (venmo,) = (line for line in self.review if line["payee"] == "Venmo")
        self.assertEqual((venmo["top"], venmo["reason"]), ("none_of_these", "none_of_these"))

    def test_every_category_chosen_is_in_the_clean_list(self):
        taxonomy = {f"{group}: {name}" for group, names in ISO.items() for name in names} | {
            f"Household: {name}" for name in ("Rent", "Mortgage", "Tuition", "Income", "Transfer", "Loan repayment")}
        chosen = {r["category_level"] for r in self.records if r.get("category_level")}
        self.assertTrue(chosen)
        self.assertLessEqual(chosen, taxonomy)


class ExportCategoriesAreNotUsedTests(unittest.TestCase):
    def test_jev_is_never_shown_an_export_category(self):
        _, double, *_ = run_household()
        export = {line.split(",")[2].strip('"') for line in (ORACLE / "monarch.csv").read_text(encoding="utf-8").splitlines()[1:]}
        shown = json.dumps([(state, options) for _, state, _, options in double.requests])
        in_the_list = {name for names in ISO.values() for name in names} | {"Transfer", "Income", "Rent"}  # words both use
        for category in export - in_the_list:
            self.assertNotIn(category, shown)

    def test_the_same_questions_are_asked_whatever_the_export_says(self):
        original = (ORACLE / "monarch.csv").read_text(encoding="utf-8")
        def scramble(line: str) -> str:  # every category, whatever it says
            return line.replace(line.split(",")[2], '"Scrambled: Nonsense"', 1)

        scrambled = "\n".join(line if i == 0 else scramble(line) for i, line in enumerate(original.splitlines())) + "\n"
        self.assertNotEqual(scrambled, original)
        _, first, *_ = run_household()
        _, second, *_ = run_household(scrambled)

        def asked(double):
            return [(json.dumps(state, sort_keys=True), list(options)) for _, state, _, options in double.requests]

        self.assertEqual(sorted(asked(first)), sorted(asked(second)))


if __name__ == "__main__":
    unittest.main()
