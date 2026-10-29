"""Python entry point for `understudy etl run`."""

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

from src.etl.controller import EtlError, _check_writable, run
from src.etl.jev import JevError, TypeSafeJev
from src.etl.sources import SourceError, describe


def main(argv=None, *, make_jev=TypeSafeJev, stdout=None, stderr=None):
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    parser = argparse.ArgumentParser(prog="understudy etl run")
    parser.add_argument("--monarch", type=Path, required=True)
    parser.add_argument("--amex", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("build/runs"))
    parser.add_argument("--amex-account")
    parser.add_argument("--since")
    args = parser.parse_args(argv)
    try:
        if args.since:
            args.since = date.fromisoformat(args.since).isoformat()
        _check_writable(args.out.resolve())
        describe(args.monarch, "monarch")
        describe(args.amex, "amex")
        jev = make_jev()
    except (ValueError, OSError, SourceError, EtlError, JevError) as error:
        stderr.write(f"understudy: {error}\n")
        return 2
    try:
        result = asyncio.run(run(
            monarch=args.monarch, amex=args.amex, out=args.out, jev=jev,
            amex_account=args.amex_account, since=args.since,
            announce=lambda message: stderr.write(f"{message}\n")))
    except Exception as error:
        stderr.write(f"understudy: {error}\n")
        return 1
    stdout.write(json.dumps(result, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
