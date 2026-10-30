"""General stages over rows: find runs of consecutive numbers, score candidates, and keep the highest or lowest.

They know nothing about cinemas. `map.adjacent_runs` finds consecutive seat numbers, consecutive days or consecutive
invoice numbers alike. The `prefer_*` maps add a 0.0 to 1.0 score field to each row, `map.weigh` adds the weighted sum
of fields, and `reduce.max` / `reduce.min` keep the best rows by a field (decisions 26, 30 and 31). Every stage reads
its rows from a named source, which may itself be computed by a stage.
"""

from src.sketch.registry import Source, stage


def _matching(rows: list[dict], match: dict | None) -> list[dict]:
    return [row for row in rows if all(row.get(field) == value for field, value in (match or {}).items())]


@stage("map.adjacent_runs")
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


@stage("map.prefer_order")
async def prefer_order(context, rows: Source, field: str, order: list, into: str) -> list[dict]:
    """Each row of `rows` plus a score in `into`: the first value of `order` scores 1.0, the next less, and a value not
    listed 0."""
    return [
        {**row, into: (len(order) - order.index(row[field])) / len(order) if row[field] in order else 0.0}
        for row in await context.read(rows)
    ]


@stage("map.prefer_middle")
async def prefer_middle(  # noqa: PLR0913 - the stage's with: keys
    context, rows: Source, extent: Source, group: str, order: str, into: str, match: dict | None = None,
) -> list[dict]:
    """Each row of `rows` (runs, see `adjacent_runs`) plus a score in `into`: 1.0 for a run centerd in its group, falling
    to 0.0 at the group's end. A group's extent is the lowest and highest `order` among the `extent` rows that `match`."""
    ends: dict = {}
    for row in _matching(await context.read(extent), match):
        low, high = ends.get(row[group], (row[order], row[order]))
        ends[row[group]] = (min(low, row[order]), max(high, row[order]))
    scored = []
    for run in await context.read(rows):
        low, high = ends[run[group]]
        half = (high - low) / 2
        distance = abs((run["first"] + run["last"]) / 2 - (low + high) / 2)
        scored.append({**run, into: max(0.0, 1 - distance / half) if half else 1.0})
    return scored


@stage("map.weigh")
async def weigh(context, source: Source, by: dict, into: str) -> list[dict]:
    """Each row of `source` plus `into`: the sum of its `by` fields, each times its weight."""
    return [
        {**row, into: sum(weight * row[field] for field, weight in by.items())}
        for row in await context.read(source)
    ]


@stage("reduce.any")
async def reduce_any(context, source: Source) -> list[dict]:
    """One row, `{any: true}` when `source` has at least one row and `{any: false}` when it has none, for a guard."""
    return [{"any": bool(await context.read(source))}]


@stage("reduce.max")
async def reduce_max(context, source: Source, field: str, take: int = 1) -> list[dict]:
    """The `take` rows of `source` with the highest `field`, highest first. Equal values keep the order they had."""
    return sorted(await context.read(source), key=lambda row: -row[field])[:take]


@stage("reduce.min")
async def reduce_min(context, source: Source, field: str, take: int = 1) -> list[dict]:
    """The `take` rows of `source` with the lowest `field`, lowest first. Equal values keep the order they had."""
    return sorted(await context.read(source), key=lambda row: row[field])[:take]
