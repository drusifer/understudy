"""A file source: JSONL, one record per line."""

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
