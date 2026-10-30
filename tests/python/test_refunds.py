import asyncio
import unittest

from jev_double import JevDouble

from src.etl.refunds import decide_refunds
from src.jev import JevError


def row(refund_id, refund_date, refund_amount, merchant, candidate_id, candidate_date, candidate_amount, rank, count, status):
    return {"refund_id": refund_id, "refund_date": refund_date, "refund_amount": refund_amount, "merchant": merchant,
            "candidate_id": candidate_id, "candidate_date": candidate_date, "candidate_amount": candidate_amount,
            "candidate_rank": rank, "candidate_count": count, "link_status": status}


CHOICE = [
    row("m5", "2026-03-01", 45.0, "Store", "m2", "2026-02-15", -45.0, 1, 2, "needs_choice"),
    row("m5", "2026-03-01", 45.0, "Store", "m1", "2026-02-01", -50.0, 2, 2, "needs_choice"),
]
SINGLE = [row("m9", "2026-03-10", 30.0, "Shoe Shop", "m8", "2026-03-01", -30.0, 1, 1, "single")]
NONE = [row("m7", "2026-03-05", 12.0, "Bookshop", None, None, None, None, 0, "no_original")]


class RefundDecisionTests(unittest.TestCase):
    def test_a_refund_with_several_originals_asks_jev_and_keeps_the_choice_and_confidence(self):
        jev = JevDouble(choices={"charged_2026-02-01_50.00": 0.71})
        decisions = asyncio.run(decide_refunds(CHOICE, jev))
        self.assertEqual(len(jev.requests), 1)
        self.assertEqual(decisions, [{"refund_id": "m5", "candidate_id": "m1", "status": "chosen", "confidence": 0.71}])

    def test_the_question_offers_only_the_listed_originals_without_merchant_labels_of_other_rows(self):
        jev = JevDouble()
        asyncio.run(decide_refunds(CHOICE, jev))
        _, state, _, options = jev.requests[0]
        self.assertEqual(set(options), {"charged_2026-02-15_45.00", "charged_2026-02-01_50.00"})
        self.assertEqual(state["refund"], {"merchant": "Store", "date": "2026-03-01", "amount": 45.0})

    def test_an_answer_that_is_not_offered_links_nothing(self):
        jev = JevDouble(choices={"not_offered_x": 0.9})
        decisions = asyncio.run(decide_refunds(CHOICE, jev))
        self.assertEqual(decisions, [{"refund_id": "m5", "candidate_id": None, "status": "off_list", "confidence": None}])

    def test_one_original_links_without_asking_and_none_is_marked(self):
        jev = JevDouble()
        decisions = asyncio.run(decide_refunds(SINGLE + NONE, jev))
        self.assertEqual(jev.requests, [])
        self.assertEqual(decisions, [
            {"refund_id": "m9", "candidate_id": "m8", "status": "single", "confidence": None},
            {"refund_id": "m7", "candidate_id": None, "status": "no_original", "confidence": None},
        ])

    def test_jev_unreachable_stops_the_stage_naming_it(self):
        with self.assertRaises(JevError) as caught:
            asyncio.run(decide_refunds(CHOICE, JevDouble(fail=JevError("Jev could not be reached"))))
        self.assertIn("refund originals", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
