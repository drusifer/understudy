"""General stages over rows: find runs of consecutive numbers, and weigh candidates 0.0 to 1.0.

They know nothing about cinemas. `etl.adjacent_runs` finds consecutive seat numbers, consecutive days or consecutive
invoice numbers alike; the `prefer_*` stages turn a field into the weighted rows a `blend` combines with the sketch's
own weights (decision 26).
"""

from src.sketch.registry import Source, stage


def _matching(rows: list[dict], match: dict | None) -> list[dict]:
    return [row for row in rows if all(row.get(field) == value for field, value in (match or {}).items())]


@stage("etl.adjacent_runs")
async def adjacent_runs(  # noqa: PLR0913 - the stage's with: keys
    context, source: Source, group: str, order: str, length: int, match: dict | None = None,
) -> list[dict]:
    """Every run of `length` consecutive `order` numbers inside one `group`, from the source rows that `match`.

    A run is `{<group>: value, first, last, run: "<value><first>-<last>"}`; runs overlap (2, 3, 4 gives 2-3 and 3-4).
    """
    numbers: dict = {}
    for row in _matching(await context.read(source), match):
        numbers.setdefault(row[group], set()).add(row[order])
    return [
        {group: value, "first": first, "last": first + length - 1, "run": f"{value}{first}-{first + length - 1}"}
        for value, found in numbers.items()
        for first in sorted(found)
        if all(first + step in found for step in range(length))
    ]


@stage("etl.prefer_order")
async def prefer_order(context, field: str, order: list, key: str, outcome: str) -> list[dict]:
    """Weighted rows for the previous stage's rows: the first value of `order` weighs 1.0, the next less, and a value
    not listed 0. Each row becomes `{<outcome>: row[key], weight}`."""
    return [
        {outcome: row[key], "weight": (len(order) - order.index(row[field])) / len(order) if row[field] in order else 0.0}
        for row in context.last
    ]


@stage("etl.prefer_middle")
async def prefer_middle(  # noqa: PLR0913 - the stage's with: keys
    context, source: Source, group: str, order: str, key: str, outcome: str, match: dict | None = None,
) -> list[dict]:
    """Weighted rows for the previous stage's runs (see `adjacent_runs`): 1.0 for a run centred in its group, falling
    to 0.0 at the group's end. The group's extent is the lowest and highest `order` among the source rows that `match`."""
    extent: dict = {}
    for row in _matching(await context.read(source), match):
        low, high = extent.get(row[group], (row[order], row[order]))
        extent[row[group]] = (min(low, row[order]), max(high, row[order]))
    weighted = []
    for run in context.last:
        low, high = extent[run[group]]
        half = (high - low) / 2
        distance = abs((run["first"] + run["last"]) / 2 - (low + high) / 2)
        weighted.append({outcome: run[key], "weight": max(0.0, 1 - distance / half) if half else 1.0})
    return weighted
