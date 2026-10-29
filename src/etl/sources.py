"""Read a Monarch or Amex CSV export as normalized, provenance-bearing records.

The source servers serve these pages; the readers know the file format, the row
identity and nothing else. A record keeps every column of its row in `raw_record`.
"""

import csv
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

PAGE_LIMIT = 1000

DISPLAY = {"monarch": "Monarch", "amex": "Amex"}

ALIASES = {
    "date": ["date", "transaction date", "trans date", "posted date"],
    "amount": ["amount", "transaction amount"],
    "merchant": ["merchant", "description", "original statement", "payee", "name"],
}
OPTIONAL_ALIASES = {"account": ["account", "account #"]}


class SourceError(Exception):
    """A source that cannot be served: the message names the file and the problem."""


def normalize_date(value: str | None) -> str | None:
    """ISO text for the supported export dates (2026-01-02, 01/02/2026); anything else unchanged."""
    if not value:
        return value
    for parse in (date.fromisoformat, lambda text: datetime.strptime(text, "%m/%d/%Y").date()):
        try:
            return parse(value).isoformat()
        except ValueError:
            continue
    return value


def _display(source: str) -> str:
    if source not in DISPLAY:
        raise SourceError(f"unknown source {source!r} (known: {', '.join(DISPLAY)})")
    return DISPLAY[source]


def _map_columns(columns: list[str], source: str, path: Path) -> dict[str, str | None]:
    lowered = [column.lower().strip() for column in columns]
    mapping: dict[str, str | None] = {}
    for field, aliases in ALIASES.items():
        found = next((lowered.index(alias) for alias in aliases if alias in lowered), None)
        if found is None:
            raise SourceError(
                f"{_display(source)} CSV {path} is missing a required {field} column "
                f"(recognized: {', '.join(aliases)})"
            )
        mapping[field] = columns[found]
    for field, aliases in OPTIONAL_ALIASES.items():
        found = next((lowered.index(alias) for alias in aliases if alias in lowered), None)
        mapping[field] = columns[found] if found is not None else None
    return mapping


@lru_cache(maxsize=8)
def _load_cached(path_text: str, source: str, modified_ns: int, size: int):  # noqa: ARG001 - cache key: a changed file reloads
    path = Path(path_text)
    display = _display(source)
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise SourceError(f"{display} CSV cannot be read: {path} is empty")
            columns = [name.strip() for name in reader.fieldnames]
            reader.fieldnames = columns
            mapping = _map_columns(columns, source, path)
            rows = list(reader)
    except OSError as error:
        raise SourceError(f"{display} CSV cannot be read: {path} ({error.strerror or error})") from error
    return columns, mapping, rows


def _load(path: Path, source: str):
    _display(source)
    try:
        status = path.stat()
    except OSError as error:
        raise SourceError(f"{DISPLAY[source]} CSV cannot be read: {path} ({error.strerror or error})") from error
    return _load_cached(str(path), source, status.st_mtime_ns, status.st_size)


def describe(path: Path, source: str) -> dict:
    """Validate the file and say how many rows it holds and which columns it has."""
    columns, _, rows = _load(path, source)
    return {"rows": len(rows), "columns": columns}


def read_page(path: Path, source: str, offset: int, limit: int) -> list[dict]:
    """Return up to `limit` records (never more than PAGE_LIMIT) starting at row `offset`."""
    if offset < 0 or limit < 0:
        raise ValueError("offset and limit must not be negative")
    _, mapping, rows = _load(path, source)
    page = rows[offset : offset + min(limit, PAGE_LIMIT)]
    account_column = mapping["account"]
    return [
        {
            "source": source,
            "source_row_number": offset + index + 1,
            "transaction_date": normalize_date(row[mapping["date"]]),
            "amount": row[mapping["amount"]],
            "merchant": row[mapping["merchant"]],
            "account": row[account_column] if account_column else None,
            "raw_record": dict(row),
        }
        for index, row in enumerate(page)
    ]
