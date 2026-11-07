"""A small summary of a list of rows, for the beat box to draw (UND-118).

`profile(rows)` says, per column, what kind of values it holds and how they are spread: a number column by its range and
mean (a gauge), a text column by its commonest values (bars, or a donut when there are few). It is small enough for a line
of the run log and never carries the rows themselves; values are cut short.
"""

from collections import Counter

MAX_COLUMNS = 6  # columns a piece's profile keeps
VALUE_CHARS = 40  # the most of a text value the profile keeps
TOP_VALUES = 5  # the commonest values of a text column
ORDER = {"number": 0, "text": 1, "other": 2}  # the most chartable columns first


def _is_number(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _round(value: float) -> float | int:
    return int(value) if float(value).is_integer() else round(value, 4)


def _column(name: str, values: list) -> dict | None:
    """The summary of one column's non-empty values, or None when it has none."""
    if not values:
        return None
    if all(isinstance(value, list | dict) for value in values):
        return {"name": name, "kind": "other", "rows": len(values)}
    if all(_is_number(value) for value in values):
        return {"name": name, "kind": "number", "rows": len(values), "min": _round(min(values)), "max": _round(max(values)),
                "mean": _round(sum(values) / len(values))}
    counted = Counter(str(value)[:VALUE_CHARS] for value in values)
    top = [[value, count] for value, count in counted.most_common(TOP_VALUES)]
    return {"name": name, "kind": "text", "rows": len(values), "distinct": len(counted), "top": top}


ITEM_CHARS = 60  # the most of a value the box shows for one pass of a repeated beat
ITEM_FIELDS = 12  # the most fields of that row


def brief(row: dict) -> dict:
    """One row as a few labeled values: scalars cut short, a list or dict by its size, nothing for a missing value."""
    found = {}
    for name, value in row.items():
        if value is None:
            continue
        if isinstance(value, list):
            found[name] = f"{len(value)} item" + ("" if len(value) == 1 else "s")
        elif isinstance(value, dict):
            found[name] = f"{len(value)} field" + ("" if len(value) == 1 else "s")
        else:
            found[name] = value[:ITEM_CHARS] if isinstance(value, str) else value
        if len(found) == ITEM_FIELDS:
            break
    return found


def profile(rows: list[dict]) -> list[dict]:
    """The columns of `rows` (the most chartable first, at most `MAX_COLUMNS`), each summarized."""
    names = list(dict.fromkeys(name for row in rows if isinstance(row, dict) for name in row))
    columns = []
    for name in names:
        values = [row[name] for row in rows if isinstance(row, dict) and row.get(name) is not None]
        found = _column(name, values)
        if found:
            columns.append(found)
    return sorted(columns, key=lambda each: ORDER[each["kind"]])[:MAX_COLUMNS]
