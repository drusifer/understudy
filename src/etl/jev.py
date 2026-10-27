"""A thin Jev client for the ETL: bounded questions answered with typed results.

Jev only chooses among options the code offers or gives the probability of a yes
(ADR-0013); the code decides what to do with the answer. A failed call is an error,
never an answer.
"""

import os
from dataclasses import dataclass
from typing import Protocol

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, TypeSafeError

KEY = "TYPESAFE_API_KEY"


class JevError(Exception):
    """Jev could not answer; the message says why."""


@dataclass(frozen=True)
class Chosen:
    """The option Jev picked, how confident it was, and the probability of every option."""

    option: str
    confidence: float
    probabilities: dict[str, float]


class Jev(Protocol):
    async def choose(self, *, state: dict, instructions: str, options: dict[str, str]) -> Chosen: ...

    async def decide(self, *, state: dict, instructions: str, yes: str, no: str) -> float: ...


class TypeSafeJev:
    """The TypeSafe API through the official async SDK."""

    def __init__(self, client=None, environment=None):
        if client is None:
            key = ((os.environ if environment is None else environment).get(KEY) or "").strip()
            if not key:
                raise JevError(f"Jev needs a TypeSafe key: set {KEY}")
            client = AsyncTypeSafeClient(api_key=key)
        self._client = client

    async def _ask(self, state: dict, question):
        try:
            return await self._client.system_one(state=state, questions={"answer": question})
        except TypeSafeError as error:
            raise JevError(f"Jev could not be reached: {error}") from error

    async def choose(self, *, state, instructions, options):
        response = await self._ask(state, Choice(instructions=instructions, criteria=dict(options)))
        answer = response.choices["answer"]
        return Chosen(answer.choice, answer.confidence, dict(answer.probabilities))

    async def decide(self, *, state, instructions, yes, no):
        response = await self._ask(state, Noul(instructions=instructions, criteria={"true": yes, "false": no}))
        return response.nouls["answer"].noul
