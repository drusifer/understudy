"""A file source: JSONL, one record per line, or CSV with a header row."""

import csv
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path} line {number} is not valid JSON: {error.msg}") from error
        if not isinstance(row, dict):
            raise ValueError(f"{path} line {number} is not a JSON object")
        rows.append(row)
    return rows


def read_csv(path: Path) -> list[dict]:
    """A CSV file: the header row names the fields, every value is text."""
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (csv.Error, UnicodeDecodeError) as error:
        raise ValueError(f"{path} is not a readable CSV file: {error}") from error


def read_rows(path: Path) -> list[dict]:
    """The rows of a file source: CSV when the name ends in `.csv`, otherwise JSONL."""
    return read_csv(path) if Path(path).suffix == ".csv" else read_jsonl(path)
