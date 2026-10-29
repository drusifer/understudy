"""Hydration: page one source server to the end and keep an immutable JSONL snapshot."""

import hashlib
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.etl import sources
from src.etl.sources import PAGE_LIMIT

ROOT = Path(__file__).resolve().parents[2]


def _text(result) -> str:
    return "".join(part.text for part in result.content if hasattr(part, "text"))


async def hydrate(source: str, path: Path, destination: Path) -> dict:
    """Serve `path` through its source server and write every record to `destination`.

    Validates the file first, so a bad file stops the run before any directory or file is
    created. The snapshot is written beside its final name and renamed on success.
    """
    sources.describe(path, source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.etl.source_server", source, str(path)],
        cwd=str(ROOT),
    )
    rows, pages = 0, 0
    digest = hashlib.sha256()
    try:
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                info = json.loads(_text(await session.call_tool("describe", {})))
                with partial.open("wb") as output:
                    while True:
                        page = _text(await session.call_tool("read_transactions", {"offset": rows, "limit": PAGE_LIMIT}))
                        lines = [line for line in page.split("\n") if line]
                        if not lines:
                            break
                        data = ("\n".join(lines) + "\n").encode("utf-8")
                        output.write(data)
                        digest.update(data)
                        rows += len(lines)
                        pages += 1
        if rows != info["rows"]:
            raise RuntimeError(f"{source} source served {rows} of {info['rows']} rows")
        os.replace(partial, destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {
        "source": source,
        "rows": rows,
        "columns": info["columns"],
        "pages": pages,
        "path": str(destination),
        "sha256": digest.hexdigest(),
    }
