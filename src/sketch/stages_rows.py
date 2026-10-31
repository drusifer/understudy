"""General stages over rows: find runs of consecutive numbers, score candidates, and keep the highest or lowest.

They know nothing about cinemas. `map.adjacent_runs` finds consecutive seat numbers, consecutive days or consecutive
invoice numbers alike. The `prefer_*` maps add a 0.0 to 1.0 score field to each row, `map.weigh` adds the weighted sum
of fields, and `reduce.max` / `reduce.min` keep the best rows by a field (decisions 26, 30 and 31). Every stage reads
its rows from a named source, which may itself be computed by a stage.
"""

import re

from src.sketch.conditions import holds
from src.sketch.registry import Data, Source, stage


def _matching(rows: list[dict], match: dict | None) -> list[dict]:
    return [row for row in rows if all(row.get(field) == value for field, value in (match or {}).items())]


@stage("map.where")
async def where(context, source: Source, keep: dict) -> list[dict]:
    """The rows of `source` that satisfy the condition `keep` (the same explicit YAML conditions as everywhere)."""
    return [row for row in await context.read(source) if holds(keep, row)]


@stage("map.join")
async def join(  # noqa: PLR0913 - the stage's with: keys
    context, source: Source, other: Source, on: str, other_on: str | None = None, keep_unmatched: bool = False,
) -> list[dict]:
    """Each row of `source` plus the fields of the row of `other` whose `other_on` (default: `on`) equals the row's `on`
    (the first, if several). A row with no match is dropped, or kept as it is when `keep_unmatched`; where both have a
    field the row of `source` wins."""
    matching: dict = {}
    for row in await context.read(other):
        matching.setdefault(row[other_on or on], row)
    return [{**matching.get(row[on], {}), **row} for row in await context.read(source) if keep_unmatched or row[on] in matching]


@stage("map.expect")
async def expect(context, probabilities: Source, values: Data, into: str) -> list[dict]:
    """One row, `{<into>: <number>}`: the average of your numbers per level (`data.<values>`, level to number) weighted
    by the probability of each level in a Jev reading (`probabilities`)."""
    readings = await context.read(probabilities)
    numbers = context.sketch.data[values]
    total = sum(row["probability"] for row in readings) or 1.0
    return [{into: sum(row["probability"] * numbers[row["level"]] for row in readings) / total}]


@stage("map.unpair")
async def unpair(context, source: Source) -> list[dict]:
    """Flat rows from an `each` result: for every `{input, output}` pair, the input row plus each row it output."""
    return [{**pair["input"], **output} for pair in await context.read(source) for output in pair["output"]]


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


@stage("map.group")
async def group(context, source: Source, by: str, collect: dict | None = None, take: int = 3) -> list[dict]:
    """One row per distinct `by` value (case, spacing and edges ignored), in the order they first appear:
    `{key, <by>: the first spelling, count, <into>: [...]}`. Each `collect` entry, `into: field`, lists up to `take`
    different non-empty values of `field` among the group's rows."""
    groups: dict[str, list[dict]] = {}
    for row in await context.read(source):
        groups.setdefault(" ".join(str(row[by] or "").lower().split()), []).append(row)
    return [
        {"key": key, by: rows[0][by], "count": len(rows),
         **{into: list(dict.fromkeys(row[field] for row in rows if row.get(field) not in (None, "")))[:take]
            for into, field in (collect or {}).items()}}
        for key, rows in groups.items()
    ]


@stage("map.rows")
async def rows(context, rows: list) -> list[dict]:  # noqa: ARG001 - a stage always gets its context
    """The rows written in the sketch (often a list another sketch handed in), as a source."""
    return list(rows)


@stage("map.classify")
async def classify(context, source: Source, into: str, cases: list, otherwise: str) -> list[dict]:
    """Each row of `source` plus `into`: the `then` of the first case whose `if` condition the row satisfies, else
    `otherwise`. A case is `{ if: <condition>, then: <value> }`."""
    return [
        {**row, into: next((case["then"] for case in cases if holds(case["if"], row)), otherwise)}
        for row in await context.read(source)
    ]


@stage("map.number")
async def number(context, source: Source, into: str, prefix: str = "") -> list[dict]:
    """Each row of `source` plus `into`: its position in the source, from 1, after `prefix` (`m1`, `m2`, ...)."""
    return [{**row, into: f"{prefix}{position}"} for position, row in enumerate(await context.read(source), start=1)]


@stage("map.coalesce")
async def coalesce(context, source: Source, fields: dict) -> list[dict]:
    """Each row of `source` plus the fields in `fields`, each `into: [candidate, ...]` taking the first candidate field the
    row has with a value (null when none): one record from two exports that name the same thing differently."""
    return [
        {**row, **{into: next((row[name] for name in names if row.get(name) not in (None, "")), None)
                   for into, names in fields.items()}}
        for row in await context.read(source)
    ]


@stage("map.replace")
async def replace(  # noqa: PLR0913 - the stage's with: keys
    context, source: Source, field: str, pattern: str, into: str, by: str = "",
) -> list[dict]:
    """Each row of `source` plus `into`: its `field` with every match of the regular expression `pattern` replaced by
    `by` (default: removed) and the ends trimmed."""
    return [{**row, into: re.sub(pattern, by, str(row.get(field) or "")).strip()} for row in await context.read(source)]


@stage("map.normalize")
async def normalize(context, source: Source, field: str, into: str) -> list[dict]:
    """Each row of `source` plus `into`: its `field` in lower case with spaces collapsed, the key that `map.group` uses."""
    return [{**row, into: " ".join(str(row.get(field) or "").lower().split())} for row in await context.read(source)]


@stage("map.format")
async def format_text(context, source: Source, template: str, into: str) -> list[dict]:
    """Each row of `source` plus `into`: `template` with `{field}` filled from the row (Python format syntax)."""
    return [{**row, into: template.format_map(row)} for row in await context.read(source)]


@stage("map.earlier")
async def earlier(  # noqa: PLR0913 - the stage's with: keys
    context, source: Source, other: Source, on: str, date: str, amount: str, tie: str, prefix: str = "candidate_",
    take: int = 5,
) -> list[dict]:
    """For each row of `source`, one row per `other` row with the same `on` value, a `date` no later, and an `amount`
    at least as large in size and of the opposite sign (a refund and the charges it could reverse), most recent first
    (equal dates: the larger `tie` first) and at most `take`. The row is joined with the candidate's fields (named
    with `prefix` before them) and a `candidates` count of all of them; a row with no candidate comes back once with `candidates` 0."""
    others = await context.read(other)
    found = []
    for row in await context.read(source):
        fits = sorted(
            (o for o in others if o[on] == row[on] and o[date] <= row[date] and o[amount] * row[amount] < 0
             and abs(o[amount]) >= abs(row[amount])),
            key=lambda o: (o[date], str(o[tie])), reverse=True)
        found += [{**row, "candidates": len(fits), **{f"{prefix}{k}": v for k, v in o.items()}} for o in fits[:take]]
        if not fits:
            found.append({**row, "candidates": 0})
    return found


@stage("map.concat")
async def concat(context, sources: list) -> list[dict]:
    """The rows of every source named in `sources`, one after the other."""
    return [row for name in sources for row in await context.read(name)]


@stage("map.matching")
async def matching(context, source: Source, among: Source, on: str, among_on: str | None = None) -> list[dict]:
    """The rows of `source` whose `on` value is also the `among_on` (default: `on`) value of some row of `among`."""
    wanted = {row[among_on or on] for row in await context.read(among)}
    return [row for row in await context.read(source) if row[on] in wanted]
