"""A scripted Jev for the household tests: what it says for each merchant, in the two steps the household asks (a group,
then a name in it), and for the refund question. It never sees an export category (the tests check that)."""

from src.jev import Chosen

# merchant: (group, how sure of it, name or None for the group's first, how sure of it, optionally (a rival group, how sure))
PLAN = {
    "Store": ("Retail outlets", 0.9, "Bakeries", 0.9),
    "Dunkin'": ("Retail outlets", 0.55, "Bakeries", 0.5),  # under 0.7 but clearly ahead of the rest: placed
    "Employer": ("Household", 0.99, "Income", 0.99),
    "Shoe Shop": ("Clothing outlets", 0.35, "Family clothing shops", 0.9),  # not sure of the group: for review
    "Venmo": ("none_of_these", 0.9, None, 0.0),  # fits no group: for review, and the name is never asked
}


def spread(top: str, sure: float, options, rival: tuple[str, float] | None = None) -> Chosen:
    """Probability `sure` on `top`, a close second on `rival` if given, the rest shared out evenly."""
    taken = {top: sure, **({rival[0]: rival[1]} if rival else {})}
    rest = (1 - sum(taken.values())) / max(len(options) - len(taken), 1)
    return Chosen(top, sure, {name: taken.get(name, rest) for name in options})


def choose(state, instructions, options, plan=None) -> Chosen:
    """The answer to one question: the refund's original, a merchant's group, or a merchant's name."""
    if "refund" in state:  # the refund of 45.00 reverses the charge of 45.00 on the 15th
        original = next(label for label in options if "2026-02-15" in label)
        return Chosen(original, 0.8, {label: 0.8 if label == original else 0.2 for label in options})
    merchant = state["merchant"][0]["merchant"]
    group, group_sure, name, name_sure, *rival = (plan or PLAN)[merchant]
    if "groups" in state:
        return spread(group, group_sure, options, rival[0] if rival else None)
    return spread(name or next(iter(options)), name_sure, options)


def first_choice(state, instructions, options) -> Chosen:
    """A Jev that is sure of the first option of every question, and picks the original a refund reversed."""
    if "refund" in state:
        return choose(state, instructions, options)
    top = next(iter(options))
    return Chosen(top, 0.9, {name: 0.9 if name == top else 0.1 for name in options})
