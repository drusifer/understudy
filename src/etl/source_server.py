"""An MCP source server: one export, two tools (`describe`, `read_transactions`).

Run as `python -m src.etl.source_server <monarch|amex> <csv>`. A file that cannot be
served stops the server before it answers anything, naming the file and the problem.
"""

import argparse
import json
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from src.etl import sources
from src.etl.sources import SourceError


def build_server(source: str, path: Path) -> MCPServer:
    """Validate the file, then return a server that serves it."""
    sources.describe(path, source)
    server = MCPServer(f"{source}-source")

    @server.tool()
    def describe() -> dict:
        """Row count and column names of this export."""
        return sources.describe(path, source)

    @server.tool()
    def read_transactions(offset: int, limit: int) -> str:
        """Up to 1000 JSONL records starting at row `offset`; an empty answer is the end."""
        records = sources.read_page(path, source, offset, limit)
        return "\n".join(json.dumps(record, ensure_ascii=False) for record in records)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=sorted(sources.DISPLAY))
    parser.add_argument("path", type=Path)
    arguments = parser.parse_args()
    try:
        server = build_server(arguments.source, arguments.path)
    except SourceError as error:
        print(f"understudy: {error}", file=sys.stderr)
        sys.exit(2)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
