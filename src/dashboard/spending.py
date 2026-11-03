"""The household's `spending.jsonl` as the run summary shows it: the largest categories, and how many more there are.

The file is read through a size cap. A file the console cannot read is named, so the rest of the page still works.
"""

import json
from pathlib import Path

NAME = "spending.jsonl"
SHOWN = 10  # categories listed; the rest are counted
MAX_BYTES = 1_000_000


def read_spending(directory: Path) -> dict | None:
    """`{top: [{category, amount, share}], more, problem}` for a run that wrote the file, None for one that did not."""
    path = directory / NAME
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > MAX_BYTES:
        return _unreadable(f"{NAME} is too large to show")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return _unreadable(f"{NAME} could not be read")
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        try:
            each = json.loads(line)
            rows.append({"category": str(each["category"]), "amount": float(each["amount"]), "share": float(each["share"])})
        except (ValueError, KeyError, TypeError):
            return _unreadable(f"{NAME} line {number} is not readable")
    rows.sort(key=lambda each: -each["amount"])
    return {"top": rows[:SHOWN], "more": max(len(rows) - SHOWN, 0), "problem": None}


def _unreadable(problem: str) -> dict:
    return {"top": [], "more": 0, "problem": problem}
