import asyncio
import unittest

from jev_double import JevDouble

from src.etl.categorize import place_merchants
from src.jev import Chosen, JevError

CATEGORIES = ["Food & Dining: Groceries", "Food & Dining: Coffee & Cafes", "Transportation: Public Transit"]
MCC = {
    "Retail outlets": ["Groceries and supermarkets", "Bookstores"],
    "Utilities": ["Electric, gas, sanitary and water utilities", "Wire transfers and money orders"],
    "Service providers": ["Financial institutions -- manual cash disbursements", "Laundry services"],
}
WIRE = "Wire transfers and money orders"


def merchant(key, text=None, records=3):
    return {"merchant_key": key, "merchant": text or key.title(), "records": records,
            "example_amounts": [-4.5, -4.5], "statements": []}


MERCHANTS = [merchant("gristedes", "Gristedes", 5), merchant("odd shop", "Odd Shop", 2),
             merchant("venmo", "Venmo", 59), merchant("zelle", "Zelle", 6), merchant("sorter", "Sorter", 1)]
FITS = {"Gristedes": 0.95, "Odd Shop": 0.5, "Venmo": 0.05, "Zelle": 0.04, "Sorter": 0.02}
FITS_NEW = {"Zelle": 0.92, "Sorter": 0.1}
PICK = {"Gristedes": "Food & Dining: Groceries", "Odd Shop": "Food & Dining: Coffee & Cafes"}
GROUP = {"Venmo": "Utilities", "Sorter": "Retail outlets"}
NAME_PROBS = {"Venmo": {WIRE: 0.7, "Electric, gas, sanitary and water utilities": 0.2},
              "Sorter": {"Bookstores": 0.6, "Groceries and supermarkets": 0.4}}
RUBRIC = {WIRE: 0.9, "Bookstores": 0.3, "Groceries and supermarkets": 0.2,
          "Electric, gas, sanitary and water utilities": 0.1}


def jev(rubric=None, group=None, fits=None, picks=None):
    rubric, group, fits, picks = rubric or RUBRIC, group or GROUP, fits or FITS, picks or PICK

    def noul(state, name, spec):
        if name == "fits":
            return (FITS_NEW if WIRE in state["categories"] else fits).get(state["merchant"], 0.5)
        return next(p for candidate, p in rubric.items() if f'"{candidate}"' in spec.instructions)

    def choice(state, name, spec):
        who = state["merchant"]
        if name == "category":
            option = WIRE if WIRE in spec.options else picks.get(who, next(iter(spec.options)))
            return Chosen(option, 0.8, {option: 0.8})
        if name == "group":
            option = group.get(who, next(iter(spec.options)))
            return Chosen(option, 0.7, {option: 0.7})
        probabilities = NAME_PROBS[who]
        return Chosen(max(probabilities, key=probabilities.get), 0.7, probabilities)

    return JevDouble(choice_fn=choice, noul_fn=noul)


def run(merchants=MERCHANTS, double=None, announce=None):
    return asyncio.run(place_merchants(merchants, CATEGORIES, double or jev(), MCC, announce=announce or (lambda m: None)))


def by_key(result):
    return {p["merchant_key"]: p for p in result["placements"]}


class PlacementTests(unittest.TestCase):
    def test_announces_the_request_count_before_the_first_request(self):
        messages, double = [], jev()
        original = double.ask

        async def ask(**kwargs):
            self.assertTrue(messages, "announce must come before the first Jev request")
            return await original(**kwargs)

        double.ask = ask
        run(double=double, announce=messages.append)
        self.assertIn("5 merchants", messages[0])

    def test_a_merchant_that_fits_is_placed_with_its_fit_probability_and_confidence(self):
        placed = by_key(run())["gristedes"]
        self.assertEqual((placed["category"], placed["source"], placed["status"]), ("Food & Dining: Groceries", "existing", "placed"))
        self.assertEqual((placed["fit_probability"], placed["confidence"]), (0.95, 0.8))

    def test_an_unsure_fit_goes_to_review_with_the_suggestion(self):
        odd = by_key(run())["odd shop"]
        self.assertEqual((odd["status"], odd["category"], odd["source"]), ("review", None, None))
        self.assertEqual(odd["suggestion"], "Food & Dining: Coffee & Cafes")

    def test_one_fit_request_per_merchant_and_each_asks_for_a_fit_and_a_choice_together(self):
        double = jev()
        run(merchants=MERCHANTS[:2], double=double)
        self.assertEqual(len(double.requests), 2)
        self.assertTrue(all(set(r[3]) == {"fits", "category"} for r in double.requests))

    def test_what_fits_nothing_is_named_from_the_mcc_list_after_a_group_then_a_name_then_a_rubric_check(self):
        result = run()
        venmo = by_key(result)["venmo"]
        self.assertEqual((venmo["category"], venmo["source"], venmo["status"]), (WIRE, "new", "placed"))
        new = {c["category"]: c for c in result["new_categories"]}
        self.assertEqual(new[WIRE]["mcc_group"], "Utilities")
        self.assertEqual(new[WIRE]["rubric_probability"], 0.9)

    def test_a_new_category_is_offered_to_later_merchants_and_they_share_it(self):
        result = run()
        zelle = by_key(result)["zelle"]
        self.assertEqual((zelle["category"], zelle["source"]), (WIRE, "new"))
        new = {c["category"]: c for c in result["new_categories"]}
        self.assertEqual(new[WIRE]["merchants"], 2)
        self.assertEqual(new[WIRE]["records"], 59 + 6)

    def test_no_name_passing_the_rubric_sends_the_merchant_to_review_without_a_new_category(self):
        sorter = by_key(run())["sorter"]
        self.assertEqual((sorter["status"], sorter["category"]), ("review", None))
        self.assertNotIn("Bookstores", [c["category"] for c in run()["new_categories"]])

    def test_every_category_in_the_result_is_one_offered_or_one_from_the_mcc_list(self):
        allowed = set(CATEGORIES) | {n for names in MCC.values() for n in names}
        for placement in run()["placements"]:
            if placement["category"] is not None:
                self.assertIn(placement["category"], allowed)

    def test_an_answer_that_is_not_offered_is_never_placed(self):
        def off_list_choice(state, name, spec):
            return Chosen("A Made Up Category", 0.9, {"A Made Up Category": 0.9})

        double = JevDouble(choice_fn=off_list_choice, noul_fn=lambda state, name, spec: 0.95)
        result = run(merchants=MERCHANTS[:1], double=double)
        self.assertEqual(result["placements"][0]["status"], "review")
        self.assertIsNone(result["placements"][0]["category"])

    def test_the_run_reports_how_many_requests_were_made_for_how_many_records(self):
        result = run()
        self.assertEqual(result["records_covered"], 5 + 2 + 59 + 6 + 1)
        # 5 fit requests, then naming in sorted order: sorter (group, name, rubric: 3, sent to review),
        # venmo (3, creates the category), zelle (1: it fits the new category)
        self.assertEqual(result["requests"], 5 + 3 + 3 + 1)

    def test_after_a_jev_failure_no_further_requests_are_made(self):
        many = [merchant(f"shop {i:02d}", f"Shop {i:02d}") for i in range(40)]
        double = JevDouble(fail=JevError("Jev could not be reached"))
        original = double.ask

        async def slow_failure(**kwargs):
            await asyncio.sleep(0)
            return await original(**kwargs)

        double.ask = slow_failure
        with self.assertRaises(JevError):
            run(merchants=many, double=double)
        # only the requests already in flight (the stage's concurrency limit) were ever made
        self.assertLessEqual(len(double.requests), 8)

    def test_jev_unreachable_stops_the_stage_naming_it(self):
        with self.assertRaises(JevError) as caught:
            run(double=JevDouble(fail=JevError("Jev could not be reached")))
        self.assertIn("category placement", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
