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
from src.sketch.fragment import Fragment, read_stage

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
        "refund_readings": [],  # no refund is linked by Jev here: a refund that needs a choice stays a credit
        **more_stubs,
    }
    if categories is not None:
        stubs["categories"] = categories
    elif "decided" not in more_stubs and "placements" not in more_stubs:
        stubs["categories"] = []  # nothing was placed; give `decided` or `placements` to let the categories be worked out
    summary: dict = {}
    rows = asyncio.run(read_stage(household(), name, stubs=stubs, summary=summary))
    return rows, summary


def without_lines(text: str, *endings: str, containing: tuple[str, ...] = ()) -> str:
    """The CSV text without the lines that end in one of `endings` or contain one of `containing`."""
    return "\n".join(line for line in text.splitlines()
                     if not line.endswith(endings) and not any(part in line for part in containing)) + "\n"


CHILD = ROOT / "examples" / "household" / "categorize_merchant.yaml"
ADDITIONS = ROOT / "examples" / "household" / "additions.jsonl"


def merchants_of(**options) -> list[dict]:
    """The merchants the household asks Jev about (one row each: key, payee, count, amounts, statements, descriptions)."""
    rows, _ = fragment("merchants", **options)
    return rows


def categorize(merchant: dict, plan=None, jev=None):
    """What the child sketch `categorize_merchant` ends with for one merchant, and the Jev double it asked.

    The child gets the merchant's row as a call from the household gives it; Jev is the scripted double of
    `household_jev` (`plan` changes what it says; `jev` is a different choice function altogether). The route is the
    child's machine: a group that fits goes on to a name (`answer`), otherwise the merchant is for review as it is
    (`no_fit_row`)."""
    from household_jev import choose
    from jev_double import JevDouble

    values = {name: merchant[name] for name in ("payee", "count", "amounts", "statements", "descriptions")}
    child = load_checked(CHILD, {}, {**values, "additions": str(ADDITIONS)})
    double = JevDouble(choose_fn=jev or (lambda state, instructions, options: choose(state, instructions, options, plan)))

    async def route():
        with Fragment(child, jev=double) as session:
            fits = await session.read("group_fit")
            return await session.read("answer" if fits else "no_fit_row")

    (row,) = [r for r in asyncio.run(route()) if r.get("level") != ""]
    return row, double


def decided(plan=None, *, monarch: str | None = None, jev=None) -> list[dict]:
    """What the household's `decided` source holds when Jev has placed every merchant per `plan` (or per the choice
    function `jev`) in the export `monarch`: each merchant's row, the child's answer and `source: jev`, as the `placements`
    stage and `jev_placed` would make them."""
    return [{**merchant, **categorize(merchant, plan, jev)[0], "source": "jev"} for merchant in merchants_of(monarch=monarch)]


def placed_all(monarch: str | None = None, *, transfers: tuple[str, ...] = ("Ridgewood Savings Bank",)) -> list[dict]:
    """A `decided` for the export `monarch` written by hand, in the shape the child's answers have: every merchant placed in
    some category, the merchants in `transfers` in Household: Transfer. For tests of what the household does with a
    placement, where which category it was does not matter and running the child for each merchant would only cost time."""
    return [{**merchant, "level": "Household: Transfer" if merchant["payee"] in transfers else "Group: Name",
             "status": "placed", "probability": 0.9, "source": "jev"} for merchant in merchants_of(monarch=monarch)]


def run_state(name: str, **stubs):
    """Run one state of the household's machine (a check, say) against the rows written for its sources, exactly as the
    sketch's own `do` and `with` give it. It raises what the stage raises. The order of the states in a whole run is not
    tested here; a whole early-stopping run does that."""
    from types import SimpleNamespace

    from src.sketch.registry import library as registered
    from src.sketch.vocabulary import stage_of

    state = household().machine["states"][name]
    kind, target = stage_of(state)
    function = registered()[f"{kind}.{target}"]

    async def go():
        with Fragment(household(), stubs=stubs) as session:
            return await function(SimpleNamespace(read=session.read), **state.get("with", {}))

    return asyncio.run(go())
