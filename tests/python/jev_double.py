"""A scripted Jev for tests: no network, no cost, and it counts the requests it was asked."""

from src.etl.jev import ChoiceSpec, Chosen


class JevDouble:
    def __init__(self, choices=None, probabilities=None, fail=None, choice_fn=None, noul_fn=None):
        """`choices` maps an option name to the confidence to answer with; `probabilities` maps a
        payee text to the probability of yes; `fail` is an exception to raise instead.
        `choice_fn(state, name, spec) -> Chosen` and `noul_fn(state, name, spec) -> float` script `ask`."""
        self.choices = choices or {}
        self.probabilities = probabilities or {}
        self.fail = fail
        self.choice_fn = choice_fn
        self.noul_fn = noul_fn
        self.requests = []

    async def ask(self, *, state, questions):
        self.requests.append(("ask", state, None, dict(questions)))
        if self.fail:
            raise self.fail
        answers = {}
        for name, spec in questions.items():
            if isinstance(spec, ChoiceSpec):
                answers[name] = self.choice_fn(state, name, spec)
            else:
                answers[name] = self.noul_fn(state, name, spec)
        return answers

    async def choose(self, *, state, instructions, options):
        self.requests.append(("choose", state, instructions, dict(options)))
        if self.fail:
            raise self.fail
        for name, confidence in self.choices.items():
            if name in options or name.startswith("not_offered"):
                return Chosen(option=name, confidence=confidence, probabilities={name: confidence})
        first = next(iter(options))
        return Chosen(option=first, confidence=0.5, probabilities={first: 0.5})

    async def decide(self, *, state, instructions, yes, no):
        self.requests.append(("decide", state, instructions, {"yes": yes, "no": no}))
        if self.fail:
            raise self.fail
        return self.probabilities.get(state.get("payee"), 0.5)
