"""Which Monarch account is the Amex card (UND-50, ARCH_SPRINT17 section 3).

Matching every Monarch row would pair coincidences from other accounts (same day, same
amount), so pairing is limited to the card's account. It is the account holding the most
sign-flipped matches with the Amex rows, unless the owner names it with --amex-account.
"""

import re
from datetime import date
from pathlib import Path

import duckdb


class PairingError(Exception):
    """The Amex account cannot be settled; the message says what to pass."""


_COLUMNS = (
    "{source_row_number: 'INTEGER', source: 'VARCHAR', transaction_date: 'VARCHAR', "
    "amount: 'VARCHAR', merchant: 'VARCHAR', account: 'VARCHAR', raw_record: 'JSON'}"
)

_AMOUNT = (
    "CASE WHEN regexp_matches(trim(amount), '^[(].*[)]$') "
    "THEN -TRY_CAST(regexp_replace(trim(amount), '[^0-9.]', '', 'g') AS DECIMAL(18, 2)) "
    "ELSE TRY_CAST(regexp_replace(trim(amount), '[^0-9.-]', '', 'g') AS DECIMAL(18, 2)) END"
)


def _literal(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def _masked(name: str) -> str:
    """An account name without its digits, so errors never print account numbers."""
    return re.sub(r"\(\.\.\.\d+\)", "(...)", name)


def _describe(counts: dict[str, int]) -> str:
    merged: dict[str, int] = {}
    for name, count in counts.items():
        merged[_masked(name)] = merged.get(_masked(name), 0) + count
    return ", ".join(f"{name} ({count} matches)" for name, count in sorted(merged.items()))


def detect_amex_account(
    monarch_jsonl: Path, amex_jsonl: Path, override: str | None = None, since: str | None = None
) -> dict:
    """The Monarch account of the Amex card: {account, matches, source}. Refuses when unclear.

    Only rows dated on or after `since` (an ISO date) are looked at, the run's period.
    """
    start = "DATE '1900-01-01'" if not since else f"DATE '{date.fromisoformat(since).isoformat()}'"
    with duckdb.connect(":memory:") as connection:
        rows = connection.execute(
            f"""
            WITH m AS (
              SELECT account, TRY_CAST(transaction_date AS DATE) AS day, {_AMOUNT} AS signed
              FROM read_json({_literal(monarch_jsonl)}, format = 'newline_delimited', columns = {_COLUMNS})
            ),
            a AS (
              SELECT TRY_CAST(transaction_date AS DATE) AS day, {_AMOUNT} AS signed
              FROM read_json({_literal(amex_jsonl)}, format = 'newline_delimited', columns = {_COLUMNS})
            )
            SELECT m.account, count(*) AS matches
            FROM m JOIN a ON m.day = a.day AND m.signed = -a.signed
            WHERE m.day IS NOT NULL AND m.day >= {start} AND m.account IS NOT NULL
            GROUP BY m.account
            """
        ).fetchall()
        accounts = [
            name for (name,) in connection.execute(
                f"SELECT DISTINCT account FROM read_json({_literal(monarch_jsonl)}, "
                f"format = 'newline_delimited', columns = {_COLUMNS}) WHERE account IS NOT NULL ORDER BY account"
            ).fetchall()
        ]
    counts = {name: matches for name, matches in rows}
    everyone = {name: counts.get(name, 0) for name in accounts}

    if override is not None:
        chosen = [name for name in accounts if override.lower() in name.lower()]
        if len(chosen) != 1:
            found = "no account" if not chosen else f"{len(chosen)} accounts"
            raise PairingError(
                f"--amex-account {override!r} matches {found}; Monarch accounts: {_describe(everyone)}; "
                "pass --amex-account <text that appears in one account's name>"
            )
        return {"account": chosen[0], "matches": counts.get(chosen[0], 0), "source": "override"}

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        raise PairingError(
            "could not tell which Monarch account is the Amex card "
            f"(candidates: {_describe(everyone)}); pass --amex-account <text>"
        )
    return {"account": ranked[0][0], "matches": ranked[0][1], "source": "detected"}
