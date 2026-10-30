"""The stage library: the functions a sketch's `do:` and `blend:` name, each registered with `@stage`.

A stage is `async def stage(context, <with: keys>) -> result` (see `registry`); the result is what the next stage
reads as `context.last` and what guards test. Counting and converting are DuckDB SQL; the owner's judgement is `decide` and `blend`.
"""

import math
from difflib import get_close_matches

from src.sketch import stages_rows  # noqa: F401 - importing it registers its stages
from src.sketch.decide import decide_input
from src.sketch.registry import Data, Source, stage
from src.sketch.sql import query

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
    SELECT r.ingredient, r.unit, sum(d.drinks * d.weight * r.amount) AS amount
    FROM shares AS d JOIN recipes AS r ON d.dimension = r.dimension AND d.option = r.option
    GROUP BY r.ingredient, r.unit ORDER BY r.ingredient
"""


@stage("map.split_by_share")
async def split_by_share(context, source: Source, field: str, segments: Data) -> list[dict]:
    """A total (the sum of `field` over the source's rows) split across the owner's segments by their share."""
    sales = [{"drinks": row[field]} for row in await context.read(source)]
    segments = [{"name": s["name"], "share": s["share"], "age_min": s.get("age_min"), "age_max": s.get("age_max")}
                for s in context.sketch.data[segments]]
    rows = query(context.directory, SPLIT_SQL, {"sales": sales, "segments": segments})
    context.summary["total_drinks"] = round(sum(row["drinks"] for row in rows), 6)
    return rows


@stage("map.join_weights")
async def join_weights(context, probabilities: Source, weights: Data) -> list[dict]:
    """A Jev reading (a probability per level) joined with the owner's weights per level: weighted rows."""
    probabilities = await context.read(probabilities)
    levels = context.sketch.data[weights]
    dimensions = _returned_dimensions(context)
    per_level = [{"level": level, "option": option, "weight": weight}
                 for level, options in levels.items() for option, weight in options.items()]
    mixed = query(context.directory, JOIN_SQL, {"probs": probabilities, "weights": per_level})
    context.summary[f"{context.sketch.name}_weights"] = {row["option"]: round(row["weight"], 6) for row in mixed}
    return [{dimensions[0]: row["option"], "weight": row["weight"]} for row in mixed]


def _returned_dimensions(context) -> list[str]:
    for state in context.sketch.machine["states"].values():
        if state.get("final") and state.get("outputs"):
            dimensions = state["outputs"]
            if len(dimensions) != 1:
                raise ValueError(f"map.join_weights answers one dimension; the sketch outputs {dimensions}")
            return dimensions
    raise ValueError("map.join_weights is for a sketch that declares its outputs")


def _validate(rows: list[dict], decider: str, outcomes: dict, stage: str) -> None:
    """Run-time half of the outcome check: rows that came from a source must use declared options only."""
    for row in rows:
        for dimension, option in ((d, o) for d, o in row.items() if d != "weight"):
            if dimension not in outcomes:
                near = get_close_matches(dimension, list(outcomes), n=1)
                raise ValueError(f"stage {stage}: {decider!r} returned {dimension!r}, not a declared outcome"
                                 + (f" (did you mean {near[0]!r}?)" if near else ""))
            if option not in outcomes[dimension]:
                near = get_close_matches(str(option), list(outcomes[dimension]), n=1)
                raise ValueError(f"stage {stage}: {decider!r} returned {dimension}={option!r}, not a declared option"
                                 + (f" (did you mean {near[0]!r}?)" if near else ""))


async def declared_outcomes(context) -> dict:
    """Every outcome's options: the declared ones, and for an outcome read from rows, the values found now."""
    outcomes = dict(context.sketch.outcomes)
    for dimension, found in context.sketch.candidates.items():
        rows = context.results[found.source] if found.source in context.results else await context.read(found.source)
        outcomes[dimension] = tuple(dict.fromkeys(row[found.key] for row in rows))
    return outcomes


@stage("blend")
async def blend(context) -> list[dict]:
    """For each input row, the blended weight of every option per dimension: the row's own fields plus
    `dimension`, `option` and `weight`."""
    state, outcomes = context.state, await declared_outcomes(context)
    deciders = {}
    for entry in state["blend"]:
        if "from" in entry:
            deciders[entry["from"]] = context.results[entry["from"]]
            _validate(deciders[entry["from"]], entry["from"], outcomes, context.name)
    weighted: list[dict] = []
    for row in context.last:
        distribution = decide_input(state, row, deciders, allowed=outcomes)
        # options read from rows are known only now, so what the blend produced is checked against them
        _validate([{d: o} for d, options in distribution.items() for o in options], "the blend", outcomes, context.name)
        weighted += [{**row, "dimension": d, "option": o, "weight": w}
                     for d, options in distribution.items() for o, w in options.items()]
    return weighted


@stage("map.recipes")
async def convert_recipes(context, recipes: Data, packs: Data) -> list[dict]:
    """Drink counts to ingredient amounts, rounded up to whole packs where the owner gave a pack size."""
    named_recipes = []
    for recipe in context.sketch.data[recipes]:
        named = {k: v for k, v in recipe.items() if k not in RECIPE_FIELDS}
        if len(named) != 1:
            raise ValueError(f"a recipe names one option, such as size: medium (got {named})")
        ((dimension, option),) = named.items()
        named_recipes.append({"dimension": dimension, "option": option, **{k: recipe[k] for k in RECIPE_FIELDS}})
    context.summary["drinks_per_segment"] = {row["segment"]: round(row["drinks"], 6) for row in context.last}
    context.summary["shares_per_segment"] = {}
    for row in context.last:
        options = context.summary["shares_per_segment"].setdefault(row["segment"], {}).setdefault(row["dimension"], {})
        options[row["option"]] = round(row["weight"], 6)
    totals = query(context.directory, RECIPE_SQL, {"shares": context.last, "recipes": named_recipes})
    pack_sizes = context.sketch.data[packs]
    rows = []
    for total in totals:
        pack = pack_sizes.get(total["ingredient"])
        amount = math.ceil(round(total["amount"], 9) / pack) * pack if pack else round(total["amount"], 4)
        rows.append({"ingredient": total["ingredient"], "amount": amount, "unit": total["unit"]})
    return rows
