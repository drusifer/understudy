import asyncio
import unittest

from jev_double import JevDouble

from src.etl.transfers import judge_payees
from src.jev import JevError

OWNER_ACCOUNTS = ["Ridgewood Good", "Citi Simplicity Card", "Goldman Sachs Platinum Card"]


def unpaired(record_id, merchant, amount, account="Ridgewood Good (...2222)", date="2026-01-15"):
    return {"record_id": record_id, "merchant": merchant, "amount": amount, "account": account, "transaction_date": date}


ROWS = [
    unpaired("m1", "Zelle", -200.0),
    unpaired("m2", "Venmo", -600.0),
    unpaired("m3", "Venmo", -140.0),
    unpaired("m4", "venmo ", -18.5, account="Student Advantage (...3333)"),
    unpaired("m5", "Ridgewood Savings Bank", -70.0, date="2026-10-13"),
    unpaired("m6", "MIXED BY NASRIN NEW YORK NY", 205.57, account="Goldman Sachs Platinum Card (...1111)"),
]
PROBABILITIES = {"Zelle": 0.04, "Venmo": 0.05, "Ridgewood Savings Bank": 0.93, "MIXED BY NASRIN NEW YORK NY": 0.5}


class PayeeJudgmentTests(unittest.TestCase):
    def test_venmo_and_zelle_are_spending_a_savings_bank_is_an_external_transfer_the_unsure_go_to_review(self):
        decisions = asyncio.run(judge_payees(ROWS, OWNER_ACCOUNTS, JevDouble(probabilities=PROBABILITIES)))
        by_payee = {d["payee_key"]: d for d in decisions}
        self.assertEqual(by_payee["zelle"]["decision"], "spending")
        self.assertEqual(by_payee["venmo"]["decision"], "spending")
        self.assertEqual(by_payee["ridgewood savings bank"]["decision"], "external_transfer")
        self.assertEqual(by_payee["mixed by nasrin new york ny"]["decision"], "review")
        self.assertEqual(by_payee["ridgewood savings bank"]["probability"], 0.93)

    def test_one_request_per_distinct_payee_and_the_records_are_counted(self):
        jev = JevDouble(probabilities=PROBABILITIES)
        decisions = asyncio.run(judge_payees(ROWS, OWNER_ACCOUNTS, jev))
        self.assertEqual(len(jev.requests), 4)
        self.assertEqual(len(decisions), 4)
        self.assertEqual({d["payee_key"]: d["records"] for d in decisions}["venmo"], 3)

    def test_jev_sees_the_payee_and_the_owner_accounts_not_monarch_labels_or_account_numbers(self):
        jev = JevDouble(probabilities=PROBABILITIES)
        asyncio.run(judge_payees(ROWS[:1], OWNER_ACCOUNTS, jev))
        _, state, instructions, answers = jev.requests[0]
        self.assertEqual(state["payee"], "Zelle")
        self.assertEqual(state["owner_accounts"], OWNER_ACCOUNTS)
        self.assertNotIn("category", state)
        self.assertNotIn("2222", str(state))
        self.assertIn("Venmo or Zelle", answers["no"])

    def test_jev_unreachable_stops_the_stage_naming_it(self):
        with self.assertRaises(JevError) as caught:
            asyncio.run(judge_payees(ROWS, OWNER_ACCOUNTS, JevDouble(fail=JevError("Jev could not be reached"))))
        self.assertIn("transfer payees", str(caught.exception))

    def test_nothing_unpaired_asks_nothing(self):
        jev = JevDouble()
        self.assertEqual(asyncio.run(judge_payees([], OWNER_ACCOUNTS, jev)), [])
        self.assertEqual(jev.requests, [])


if __name__ == "__main__":
    unittest.main()
