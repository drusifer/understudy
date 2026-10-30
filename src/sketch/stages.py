"""The stage library: the functions a sketch's `do:` and `blend:` name.

Each stage is `async def stage(context) -> result`; the result is what the next stage reads as `context.last`
and what guards test. Counting and converting are DuckDB SQL; the owner's judgement is `decide` and `blend`.
"""

import math
from collections.abc import Awaitable, Callable
from difflib import get_close_matches

from src.sketch.decide import decide_input
from src.sketch.sql import query

StageFn = Callable[..., Awaitable]

RECIPE_FIELDS = ("ingredient", "amount", "unit")
SPLIT_SQL = """
    SELECT s.name AS segment, s.age_min, s.age_max, s.share, t.total * s.share AS drinks
    FROM segments AS s CROSS JOIN (SELECT sum(drinks) AS total FROM sales) AS t
    ORDER BY s.name
"""
JOIN_SQL = """
    SELECT w.option, sum(p.probability * w.weight) / (SELECT sum(probability) FROM probs) AS weight
    FROM probs AS p JOIN weights AS w USING (level) GROUP BY w.option ORDER BY w.option
"""
RECIPE_SQL = """
    SELECT r.ingredient, r.unit, sum(d.drinks * r.amount) AS amount
    FROM shares AS d JOIN recipes AS r ON d.dimension = r.dimension AND d.option = r.option
    GROUP BY r.ingredient, r.unit ORDER BY r.ingredient
"""


async def split_by_share(context) -> list[dict]:
    """Last week's total drinks split across the owner's segments by their share."""
    use = context.state["with"]
    sales = [{"drinks": row[use["field"]]} for row in await context.read(use["source"])]
    segments = [{"name": s["name"], "share": s["share"], "age_min": s.get("age_min"), "age_max": s.get("age_max")}
                for s in context.sketch.data[use["segments"]]]
    rows = query(context.directory, SPLIT_SQL, {"sales": sales, "segments": segments})
    context.summary["total_drinks"] = round(sum(row["drinks"] for row in rows), 6)
    return rows


async def join_weights(context) -> list[dict]:
    """A Jev reading (a probability per level) joined with the owner's weights per level: one decider's rows."""
    use = context.state["with"]
    probabilities = await context.read(use["probabilities"])
    levels = context.sketch.data[use["weights"]]
    dimensions = _returned_dimensions(context)
    weights = [{"level": level, "option": option, "weight": weight}
               for level, options in levels.items() for option, weight in options.items()]
    mixed = query(context.directory, JOIN_SQL, {"probs": probabilities, "weights": weights})
    context.summary[f"{context.sketch.name}_weights"] = {row["option"]: round(row["weight"], 6) for row in mixed}
    return [{dimensions[0]: row["option"], "weight": row["weight"]} for row in mixed]


def _returned_dimensions(context) -> list[str]:
    for state in context.sketch.machine["states"].values():
        if state.get("final") and state.get("outputs"):
            dimensions = state["outputs"]
            if len(dimensions) != 1:
                raise ValueError(f"etl.join_weights answers one dimension; the sketch outputs {dimensions}")
            return dimensions
    raise ValueError("etl.join_weights is for a sketch that declares its outputs")


def _validate(rows: list[dict], decider: str, outcomes: dict, stage: str) -> None:
    """Run-time half of the outcome check: rows that came from a source must use declared options only."""
    for row in rows:
        for dimension, option in ((d, o) for d, o in row.items() if d != "weight"):
            if dimension not in outcomes:
                near = get_close_matches(dimension, list(outcomes), n=1)
                raise ValueError(f"stage {stage}: decider {decider!r} returned {dimension!r}, not a declared outcome"
                                 + (f" (did you mean {near[0]!r}?)" if near else ""))
            if option not in outcomes[dimension]:
                near = get_close_matches(str(option), list(outcomes[dimension]), n=1)
                raise ValueError(f"stage {stage}: decider {decider!r} returned {dimension}={option!r}, not a declared option"
                                 + (f" (did you mean {near[0]!r}?)" if near else ""))


async def blend(context) -> list[dict]:
    """For each input row (a segment), the blended weight of every option per dimension, as drink counts."""
    state, outcomes = context.state, context.sketch.outcomes
    deciders = {}
    for entry in state["blend"]:
        if "from" in entry:
            deciders[entry["from"]] = context.results[entry["from"]]
            _validate(deciders[entry["from"]], entry["from"], outcomes, context.name)
    shares: list[dict] = []
    summary: dict = {}
    for row in context.last:
        distribution = decide_input(state, row, deciders, allowed=outcomes)
        summary[row["segment"]] = {d: {o: round(w, 6) for o, w in options.items()} for d, options in distribution.items()}
        shares += [{"segment": row["segment"], "dimension": d, "option": o, "drinks": row["drinks"] * w}
                   for d, options in distribution.items() for o, w in options.items()]
    context.summary["drinks_per_segment"] = {row["segment"]: round(row["drinks"], 6) for row in context.last}
    context.summary["shares_per_segment"] = summary
    return shares


async def convert_recipes(context) -> list[dict]:
    """Drink counts to ingredient amounts, rounded up to whole packs where the owner gave a pack size."""
    use = context.state["with"]
    recipes = []
    for recipe in context.sketch.data[use["recipes"]]:
        named = {k: v for k, v in recipe.items() if k not in RECIPE_FIELDS}
        if len(named) != 1:
            raise ValueError(f"a recipe names one option, such as size: medium (got {named})")
        ((dimension, option),) = named.items()
        recipes.append({"dimension": dimension, "option": option, **{k: recipe[k] for k in RECIPE_FIELDS}})
    totals = query(context.directory, RECIPE_SQL, {"shares": context.last, "recipes": recipes})
    packs = context.sketch.data[use["packs"]]
    rows = []
    for total in totals:
        pack = packs.get(total["ingredient"])
        amount = math.ceil(round(total["amount"], 9) / pack) * pack if pack else round(total["amount"], 4)
        rows.append({"ingredient": total["ingredient"], "amount": amount, "unit": total["unit"]})
    return rows


LIBRARY: dict[str, StageFn] = {
    "etl.split_by_share": split_by_share,
    "etl.join_weights": join_weights,
    "blend": blend,
    "convert.recipes": convert_recipes,
}
