"""Test support for the household sketch's rules (UND-102): compute one stage from written rows, no whole run.

`fragment("payments", monarch=..., amex=..., categories=...)` returns that source's rows and the summary it filled. The
sketch is loaded once; the exports are CSV text (the fixture's by default), and `categories` stands in for the per-merchant
Jev sketches, so nothing here asks Jev or runs the machine. A test of the sketch as a whole uses `test_household.run_folder`.
"""

import asyncio
import csv
import io
from functools import cache

from src.paths import ROOT
from src.sketch.check import load_checked
from src.sketch.fragment import read_stage

LEDGER = ROOT / "examples" / "household" / "household.yaml"
ORACLE = ROOT / "tests" / "fixtures" / "household"
NO_PINS = ROOT / "tests" / "fixtures" / "household" / "no_pins.jsonl"  # not read: pins are stubbed


def csv_rows(text: str) -> list[dict]:
    """The rows a CSV file source would give: the header names the fields, every value is text."""
    return list(csv.DictReader(io.StringIO(text)))


@cache
def household():
    """The household sketch, loaded and checked once for the fixture exports and the period of the tests."""
    values = {"monarch": str(ORACLE / "monarch.csv"), "amex": str(ORACLE / "amex.csv"), "amex_account": "Platinum",
              "since": "2026-01-01", "pinned": str(NO_PINS)}
    return load_checked(LEDGER, {}, values)


def placed(levels: dict[str, str]) -> list[dict]:
    """Stand-ins for Jev's placements: each merchant (its name as the sketch keys it: lower case) in the category given."""
    return [{"key": payee, "level": level, "status": "placed", "probability": 1.0, "source": "jev"}
            for payee, level in levels.items()]


def fragment(name: str, *, monarch: str | None = None, amex: str | None = None, categories: list[dict] | None = None,
             pins: list[dict] | None = None, **more_stubs) -> tuple[list[dict], dict]:
    """The rows of source `name` and the summary it noted, from the fixture exports unless others are given."""
    stubs = {
        "monarch_csv": csv_rows(monarch if monarch is not None else (ORACLE / "monarch.csv").read_text(encoding="utf-8")),
        "amex_csv": csv_rows(amex if amex is not None else (ORACLE / "amex.csv").read_text(encoding="utf-8")),
        "pins_file": pins or [],
        "categories": categories if categories is not None else [],
        "refund_readings": [],  # no refund is linked by Jev here: a refund that needs a choice stays a credit
        **more_stubs,
    }
    summary: dict = {}
    rows = asyncio.run(read_stage(household(), name, stubs=stubs, summary=summary))
    return rows, summary


def without_lines(text: str, *endings: str, containing: tuple[str, ...] = ()) -> str:
    """The CSV text without the lines that end in one of `endings` or contain one of `containing`."""
    return "\n".join(line for line in text.splitlines()
                     if not line.endswith(endings) and not any(part in line for part in containing)) + "\n"
