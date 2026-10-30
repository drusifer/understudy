"""A thin Jev client for the ETL: bounded questions answered with typed results.

Jev only chooses among options the code offers or gives the probability of a yes
(ADR-0013); the code decides what to do with the answer. A failed call is an error,
never an answer.
"""

import asyncio
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


@dataclass(frozen=True)
class ChoiceSpec:
    """A Choice question: pick one of the named options (a description is optional)."""

    instructions: str
    options: dict[str, str | None]


@dataclass(frozen=True)
class NoulSpec:
    """A yes/no question: the probability that the statement is true."""

    instructions: str
    yes: str
    no: str


class Jev(Protocol):
    async def choose(self, *, state: dict, instructions: str, options: dict[str, str]) -> Chosen: ...

    async def decide(self, *, state: dict, instructions: str, yes: str, no: str) -> float: ...

    async def ask(self, *, state: dict, questions: dict[str, "ChoiceSpec | NoulSpec"]) -> dict[str, "Chosen | float"]:
        """Several questions about one state in one request; a Choice answers with Chosen, a Noul with a float."""
        ...


class GatedJev:
    """Wraps a Jev for a stage: at most `concurrency` requests in flight, a count of the requests made,
    and a stop after the first failure, so a Jev outage never keeps spending on what is still queued."""

    def __init__(self, jev, concurrency: int = 8):
        self._jev, self._gate, self._failed = jev, asyncio.Semaphore(concurrency), False
        self.requests = 0

    async def _run(self, call):
        async with self._gate:
            if self._failed:
                raise JevError("stopped after an earlier Jev failure")
            self.requests += 1
            try:
                return await call()
            except JevError:
                self._failed = True
                raise

    async def ask(self, *, state, questions):
        return await self._run(lambda: self._jev.ask(state=state, questions=questions))

    async def choose(self, *, state, instructions, options):
        return await self._run(lambda: self._jev.choose(state=state, instructions=instructions, options=options))

    async def decide(self, *, state, instructions, yes, no):
        return await self._run(lambda: self._jev.decide(state=state, instructions=instructions, yes=yes, no=no))


class TypeSafeJev:
    """The TypeSafe API through the official async SDK."""

    def __init__(self, client=None, environment=None):
        if client is None:
            key = ((os.environ if environment is None else environment).get(KEY) or "").strip()
            if not key:
                raise JevError(f"Jev needs a TypeSafe key: set {KEY}")
            client = AsyncTypeSafeClient(api_key=key)
        self._client = client

    async def ask(self, *, state, questions):
        built = {
            name: Choice(instructions=spec.instructions, criteria=dict(spec.options))
            if isinstance(spec, ChoiceSpec)
            else Noul(instructions=spec.instructions, criteria={"true": spec.yes, "false": spec.no})
            for name, spec in questions.items()
        }
        try:
            response = await self._client.system_one(state=state, questions=built)
        except TypeSafeError as error:
            raise JevError(f"Jev could not be reached: {error}") from error
        answers: dict = {}
        for name, spec in questions.items():
            if isinstance(spec, ChoiceSpec):
                answer = response.choices[name]
                answers[name] = Chosen(answer.choice, answer.confidence, dict(answer.probabilities))
            else:
                answers[name] = response.nouls[name].noul
        return answers

    async def choose(self, *, state, instructions, options):
        return (await self.ask(state=state, questions={"answer": ChoiceSpec(instructions, dict(options))}))["answer"]

    async def decide(self, *, state, instructions, yes, no):
        return (await self.ask(state=state, questions={"answer": NoulSpec(instructions, yes, no)}))["answer"]
