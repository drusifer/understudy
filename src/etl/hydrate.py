"""Hydration: read one export and keep an immutable JSONL snapshot."""

import hashlib
import json
from pathlib import Path

from src.etl import sources
from src.etl.sources import PAGE_LIMIT


def hydrate(source: str, path: Path, destination: Path) -> dict:
    """Write every record of the export at `path` to `destination`, one JSON line each.

    Validates the file first, so a bad file stops the run before any directory or file is
    created. The snapshot is written beside its final name and renamed on success.
    """
    info = sources.describe(path, source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    rows = 0
    digest = hashlib.sha256()
    try:
        with partial.open("wb") as output:
            while records := sources.read_page(path, source, rows, PAGE_LIMIT):
                data = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records).encode("utf-8")
                output.write(data)
                digest.update(data)
                rows += len(records)
        partial.replace(destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {"source": source, "rows": rows, "columns": info["columns"], "path": str(destination), "sha256": digest.hexdigest()}
