import asyncio
import unittest
from types import SimpleNamespace

from typesafe_sdk import TypeSafeAPIConnectionError

from src.etl.jev import Chosen, JevError, TypeSafeJev


class FakeClient:
    """Stands in for the SDK's async client."""

    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    async def system_one(self, state, questions, **options):
        self.calls.append((state, questions))
        if self.error:
            raise self.error
        return self.response


class TypeSafeJevTests(unittest.TestCase):
    def test_choose_returns_the_option_its_confidence_and_probabilities(self):
        answer = SimpleNamespace(choice="charged_2026-02-15_45.00", confidence=0.82,
                                 probabilities={"charged_2026-02-15_45.00": 0.82, "charged_2026-02-01_50.00": 0.18})
        client = FakeClient(SimpleNamespace(choices={"answer": answer}, nouls={}))
        result = asyncio.run(TypeSafeJev(client=client).choose(
            state={"refund": {}}, instructions="Which charge?",
            options={"charged_2026-02-15_45.00": "45 on the 15th", "charged_2026-02-01_50.00": "50 on the 1st"}))
        self.assertEqual(result, Chosen("charged_2026-02-15_45.00", 0.82, answer.probabilities))
        state, questions = client.calls[0]
        self.assertEqual(set(questions), {"answer"})
        self.assertEqual(set(questions["answer"].criteria), {"charged_2026-02-15_45.00", "charged_2026-02-01_50.00"})

    def test_decide_returns_the_probability_of_yes(self):
        client = FakeClient(SimpleNamespace(choices={}, nouls={"answer": SimpleNamespace(noul=0.93)}))
        probability = asyncio.run(TypeSafeJev(client=client).decide(
            state={"payee": "Ridgewood Savings Bank"}, instructions="Is the payee the owner's own account?",
            yes="An account the owner holds.", no="A person, an app or a merchant."))
        self.assertEqual(probability, 0.93)
        question = client.calls[0][1]["answer"]
        self.assertEqual(question.criteria["true"], "An account the owner holds.")
        self.assertEqual(question.criteria["false"], "A person, an app or a merchant.")

    def test_no_key_is_refused_naming_the_variable(self):
        with self.assertRaises(JevError) as caught:
            TypeSafeJev(environment={})
        self.assertIn("TYPESAFE_API_KEY", str(caught.exception))

    def test_an_unreachable_service_is_an_error_not_an_answer(self):
        client = FakeClient(error=TypeSafeAPIConnectionError("no route"))
        with self.assertRaises(JevError) as caught:
            asyncio.run(TypeSafeJev(client=client).decide(state={}, instructions="?", yes="a", no="b"))
        self.assertIn("could not be reached", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
