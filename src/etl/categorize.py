"""Place each merchant in a category (UND-53) and name a new one when none fits (UND-55).

Jev only chooses among names the code offers and gives the probability of a yes; the code
validates every answer and decides what to do (ADR-0013). Every category in the result is one of
the offered categories or a name from the MCC list, never made up. Merchants are processed in a
fixed order so a run is repeatable.
"""

import asyncio
from collections.abc import Callable

from src.jev import ChoiceSpec, Chosen, GatedJev, Jev, JevError, NoulSpec

CONCURRENCY = 8
FITS_ABOVE = 0.7
DOES_NOT_FIT_BELOW = 0.3
NAME_ABOVE = 0.7
CANDIDATE_NAMES = 3
GROUP_EXAMPLES = 8

FIT_INSTRUCTIONS = "Does `merchant` belong in one of the categories listed in `categories`?"
FIT_YES = "At least one category in `categories` describes what is bought from `merchant`."
FIT_NO = "None of the categories in `categories` describes what is bought from `merchant`."
CATEGORY_INSTRUCTIONS = "Which category in `categories` best describes what is bought from `merchant`?"
GROUP_INSTRUCTIONS = "Which kind of business is `merchant`?"
NAME_INSTRUCTIONS = "Which name best describes what is bought from `merchant`?"
RUBRIC_YES = (
    "The name says in common words what is bought or what kind of business it is, "
    "and it is not already covered by a category in `existing_categories`."
)
RUBRIC_NO = (
    "The name is vague, names a brand, a person or a place, or repeats a category in `existing_categories`."
)


def _state(merchant: dict, **extra) -> dict:
    return {
        "merchant": merchant["merchant"],
        "also_seen_as": merchant.get("statements", [])[:3],
        "payments": {"count": merchant["records"], "example_amounts": merchant.get("example_amounts", [])[:3]},
        **extra,
    }


def _order(probabilities: dict[str, float], allowed: list[str]) -> list[str]:
    ranked = sorted((n for n in allowed if n in probabilities), key=lambda n: (-probabilities[n], n))
    return ranked[:CANDIDATE_NAMES]


async def _fit(jev: GatedJev, merchant: dict, categories: list[str]) -> tuple[float, Chosen]:
    answers = await jev.ask(
        state=_state(merchant, categories=categories),
        questions={
            "fits": NoulSpec(FIT_INSTRUCTIONS, FIT_YES, FIT_NO),
            "category": ChoiceSpec(CATEGORY_INSTRUCTIONS, {name: None for name in categories}),
        },
    )
    return answers["fits"], answers["category"]


def _placement(merchant: dict, **fields) -> dict:
    base = {"merchant_key": merchant["merchant_key"], "merchant": merchant["merchant"], "records": merchant["records"],
            "category": None, "source": None, "status": "review", "fit_probability": None, "confidence": None,
            "suggestion": None}
    return {**base, **fields}


async def _name_new(jev: GatedJev, merchant: dict, offered: list[str], new_names: list[str], mcc: dict[str, list[str]]):
    """Group, then name, then a rubric check on the top names. Returns (group, name, probability) or None."""
    groups = {
        group: "Includes: " + "; ".join(names[:GROUP_EXAMPLES]) + ("; ..." if len(names) > GROUP_EXAMPLES else "")
        for group, names in mcc.items()
    }
    group = (await jev.ask(state=_state(merchant), questions={"group": ChoiceSpec(GROUP_INSTRUCTIONS, groups)}))["group"]
    if group.option not in mcc:
        return None
    names = mcc[group.option]
    picked = (await jev.ask(
        state=_state(merchant, mcc_group=group.option),
        questions={"name": ChoiceSpec(NAME_INSTRUCTIONS, {name: None for name in names})},
    ))["name"]
    candidates = _order(picked.probabilities, names) or ([picked.option] if picked.option in names else [])
    if not candidates:
        return None
    existing = offered + new_names
    answers = await jev.ask(
        state=_state(merchant, existing_categories=existing),
        questions={
            f"candidate_{i}": NoulSpec(f'Is "{name}" a good name for the category `merchant` belongs in?', RUBRIC_YES, RUBRIC_NO)
            for i, name in enumerate(candidates, start=1)
        },
    )
    scored = sorted(((answers[f"candidate_{i}"], name) for i, name in enumerate(candidates, start=1)), key=lambda s: (-s[0], s[1]))
    best_probability, best_name = scored[0]
    if best_probability > NAME_ABOVE:
        return group.option, best_name, best_probability
    return None


async def place_merchants(
    merchants: list[dict],
    categories: list[str],
    jev: Jev,
    mcc: dict[str, list[str]],
    announce: Callable[[str], None] = print,
) -> dict:
    """Place every distinct merchant. Returns placements, new categories and the request count.

    A merchant whose fit is above 0.7 takes the category Jev chose among `categories`; below 0.3 it
    is named from the MCC list (a group, a name, then a rubric check on the top three names, the best
    above 0.7 winning), after first checking whether a category named earlier in the run fits it; in
    between, or whenever an answer is not one of the offered names, it goes to review.
    """
    ordered = sorted(merchants, key=lambda m: m["merchant_key"])
    announce(f"Jev will be asked about {len(ordered)} merchants ({len(ordered)} requests) before any naming.")
    counting = GatedJev(jev, CONCURRENCY)
    placements: dict[str, dict] = {}
    unfit: list[dict] = []
    new_categories: dict[str, dict] = {}
    fits = [asyncio.ensure_future(_fit(counting, m, categories)) for m in ordered]
    try:
        results = await asyncio.gather(*fits)
        for merchant, (probability, chosen) in zip(ordered, results, strict=True):
            valid = chosen.option in categories
            if probability > FITS_ABOVE and valid:
                placements[merchant["merchant_key"]] = _placement(
                    merchant, category=chosen.option, source="existing", status="placed",
                    fit_probability=probability, confidence=chosen.confidence)
            elif probability < DOES_NOT_FIT_BELOW:
                unfit.append(merchant)
                placements[merchant["merchant_key"]] = _placement(merchant, fit_probability=probability)
            else:
                placements[merchant["merchant_key"]] = _placement(
                    merchant, fit_probability=probability, confidence=chosen.confidence,
                    suggestion=chosen.option if valid else None)

        for merchant in unfit:
            key = merchant["merchant_key"]
            if new_categories:
                names = list(new_categories)
                probability, chosen = await _fit(counting, merchant, names)
                if probability > FITS_ABOVE and chosen.option in new_categories:
                    placements[key].update(category=chosen.option, source="new", status="placed",
                                           fit_probability=probability, confidence=chosen.confidence)
                    new_categories[chosen.option]["merchants"] += 1
                    new_categories[chosen.option]["records"] += merchant["records"]
                    continue
            named = await _name_new(counting, merchant, categories, list(new_categories), mcc)
            if named is None:
                continue
            group, name, probability = named
            entry = new_categories.setdefault(
                name, {"category": name, "mcc_group": group, "rubric_probability": probability, "merchants": 0, "records": 0})
            entry["merchants"] += 1
            entry["records"] += merchant["records"]
            placements[key].update(category=name, source="new", status="placed")
    except JevError as error:
        for task in fits:
            task.cancel()  # a failed Jev must not keep spending on the merchants still queued
        raise JevError(f"the category placement stage failed: {error}") from error
    return {
        "placements": [placements[m["merchant_key"]] for m in ordered],
        "new_categories": list(new_categories.values()),
        "requests": counting.requests,
        "records_covered": sum(m["records"] for m in ordered),
    }
