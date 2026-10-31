"""Stages that clean exported rows and pair two exports one to one.

`map.convert` reads dates and amounts from text; `map.pair` finds the same transaction in two exports (a card charge in
the bank's export and in the card's). Both know nothing about banks: any two lists of dated, priced rows pair alike.
"""

from collections import defaultdict

from src.sketch.dates import business_days_between, to_cents, to_date
from src.sketch.registry import Source, stage


@stage("map.convert")
async def convert(context, source: Source, dates: dict | None = None, amounts: dict | None = None) -> list[dict]:
    """Each row of `source` plus new fields read from its text: `dates` maps a field to the field that gets its ISO date
    (or null), `amounts` maps a field to the field that gets its amount in dollars (or null)."""
    converted = []
    for row in await context.read(source):
        added = {into: (day.isoformat() if (day := to_date(row.get(field))) else None) for field, into in (dates or {}).items()}
        for field, into in (amounts or {}).items():
            cents = to_cents(row.get(field))
            added[into] = None if cents is None else cents / 100
        converted.append({**row, **added})
    return converted


def mutual_nearest(edges: list[tuple[int, int, int]], rounds: int) -> list[tuple[int, int, int]]:
    """One-to-one pairs from `(first, second, gap)` edges: in each round a pair is made when two rows have each other as
    their nearest (smallest gap, ties by position), then the rows left over try again, up to `rounds` rounds."""
    pairs: list[tuple[int, int, int]] = []
    for _ in range(rounds):
        nearest_first: dict = {}
        nearest_second: dict = {}
        for first, second, gap in edges:
            best = nearest_first.get(first)
            if best is None or (gap, second) < (best[2], best[1]):
                nearest_first[first] = (first, second, gap)
            best = nearest_second.get(second)
            if best is None or (gap, first) < (best[2], best[0]):
                nearest_second[second] = (first, second, gap)
        made = [edge for first, edge in nearest_first.items() if nearest_second.get(edge[1]) == edge]
        if not made:
            break
        pairs += made
        used_first, used_second = {e[0] for e in made}, {e[1] for e in made}
        edges = [e for e in edges if e[0] not in used_first and e[1] not in used_second]
    return pairs


def _ranked(keys: dict[int, tuple], left: set[int], right: set[int], other_keys: dict[int, tuple]):
    """Pair rows with equal keys in position order: the first of each key on one side with the first on the other."""
    waiting = defaultdict(list)
    for position in sorted(left):
        waiting[keys[position]].append(position)
    seen = defaultdict(list)
    for position in sorted(right):
        seen[other_keys[position]].append(position)
    return [(a, b) for key, firsts in waiting.items() for a, b in zip(firsts, seen.get(key, []), strict=False)]


@stage("map.pair")
async def pair(  # noqa: PLR0913 - the stage's with: keys
    context, source: Source, other: Source, date: str, amount: str, opposite: bool = False, within: int = 0,
    text: str | None = None, other_text: str | None = None, rounds: int = 5,
) -> list[dict]:
    """Every row of `source` and of `other` once, paired one to one: `{match, method, source, other}`.

    Rows pair when they have the same `date` field and the same `amount` field (opposite signs when `opposite`).
    Same-day rows pair first by equal `text`/`other_text` (case and spacing ignored), then in file order; what is left
    pairs when the dates are within `within` business days, nearest first (see `mutual_nearest`). `match` is `paired`,
    `source_only`, `other_only` or `invalid_key` (no date or amount); `method` is `exact`, `order` or `near_date`.
    """
    left, right = await context.read(source), await context.read(other)
    sign = -1 if opposite else 1
    keys = lambda rows, flip: {  # noqa: E731
        i: (row[date], None if row[amount] is None else round(flip * row[amount] * 100)) for i, row in enumerate(rows)}
    left_keys, right_keys = keys(left, sign), keys(right, 1)
    valid_left = {i for i, key in left_keys.items() if None not in key}
    valid_right = {i for i, key in right_keys.items() if None not in key}
    clean = lambda row, field: " ".join(str(row.get(field) or "").lower().split())  # noqa: E731
    left_text = {i: (*left_keys[i], clean(left[i], text)) for i in valid_left} if text else None
    right_text = {i: (*right_keys[i], clean(right[i], other_text or text)) for i in valid_right} if text else None

    pairs: list[tuple[int, int, str, int | None]] = []
    taken_left: set[int] = set()
    taken_right: set[int] = set()

    def take(found, method, gap=None):
        for a, b in found:
            pairs.append((a, b, method, gap))
            taken_left.add(a)
            taken_right.add(b)

    if text:
        take(_ranked(left_text, valid_left, valid_right, right_text), "exact")
    take(_ranked(left_keys, valid_left - taken_left, valid_right - taken_right, right_keys), "order")
    if within:
        edges = [(a, b, gap) for a in sorted(valid_left - taken_left) for b in sorted(valid_right - taken_right)
                 if left_keys[a][1] == right_keys[b][1] and left_keys[a][0] != right_keys[b][0]
                 and (gap := business_days_between(to_date(left_keys[a][0]), to_date(right_keys[b][0]))) <= within]
        for a, b, gap in mutual_nearest(edges, rounds):
            take([(a, b)], "near_date", gap)

    rows = [{"match": "paired", "method": method, "source": left[a], "other": right[b]} for a, b, method, _ in sorted(pairs)]
    rows += [{"match": "source_only" if i in valid_left else "invalid_key", "method": None, "source": row, "other": None}
             for i, row in enumerate(left) if i not in taken_left]
    rows += [{"match": "other_only" if i in valid_right else "invalid_key", "method": None, "source": None, "other": row}
             for i, row in enumerate(right) if i not in taken_right]
    return rows
