"""Dates and amounts as exports write them, and business days (Monday to Friday, not a US federal holiday)."""

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import lru_cache

import dateparser
import holidays

MONTH_FIRST = {"DATE_ORDER": "MDY", "STRICT_PARSING": True}  # 01/02/2026 is January 2, as in the exports


def to_date(text) -> date | None:
    """The date `dateparser` reads from `text` (ISO or month-first), or None when there is none."""
    if not isinstance(text, str) or not text.strip():
        return None
    found = dateparser.parse(text.strip(), settings=MONTH_FIRST)
    return found.date() if found else None


def to_cents(text) -> int | None:
    """An amount as whole cents: `-4.50`, `$1,200.00` and `(4.50)` (negative) are read; anything else is None."""
    if not isinstance(text, str) or not text.strip():
        return None
    cleaned = text.strip()
    negative = bool(re.fullmatch(r"\(.*\)", cleaned))
    try:
        value = Decimal(re.sub(r"[^0-9.\-]", "", cleaned))
    except InvalidOperation:
        return None
    cents = int((abs(value) if negative else value) * 100)
    return -cents if negative else cents


@lru_cache(maxsize=1)
def _holidays() -> holidays.HolidayBase:
    return holidays.US(observed=True)


def is_business_day(day: date) -> bool:
    return day.weekday() < 5 and day not in _holidays()  # noqa: PLR2004 - Saturday is 5


def business_days_between(first: date, second: date) -> int:
    """Business days from the earlier date to the later: Friday to Monday is 1, two days of one weekend are 0."""
    low, high = sorted((first, second))
    return sum(is_business_day(low + timedelta(days=step)) for step in range(1, (high - low).days + 1))
