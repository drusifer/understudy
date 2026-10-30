"""Conditions are explicit YAML: a field, one operator, a value (ADR-0042).

    segment: { eq: students }
    temp:    { in: [80:90] }          # a slice: start included, stop excluded
    or: [ { genre: { eq: horror } }, { tomato: { gt: 90 } } ]

Several fields in one mapping mean `and`. A condition compares a field with a fixed value only.
"""

import re
from difflib import get_close_matches

from src.sketch.vocabulary import COMBINATORS, OPERATORS

SLICE = re.compile(r"^-?\d+(\.\d+)?:-?\d+(\.\d+)?$")
NUMERIC = ("lt", "le", "gt", "ge")


def is_slice(value) -> bool:
    return isinstance(value, str) and SLICE.match(value) is not None


def _number(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _nearest(word: str, choices) -> str:
    match = get_close_matches(word, list(choices), n=1)
    return f" (did you mean {match[0]!r}?)" if match else ""


def _operand_problem(operator: str, value) -> str | None:
    if operator in NUMERIC:
        return None if _number(value) else f"{operator} needs a number, not {value!r}"
    if operator in ("in", "not_in"):
        if is_slice(value):
            return None
        if not isinstance(value, list) or not value:
            return f"{operator} needs a list of values or a slice such as [80:90], not {value!r}"
        if any(is_slice(item) for item in value) and len(value) > 1:
            return f"{operator} takes one slice or a list of plain values, not both: {value!r}"
        return None
    return None if isinstance(value, str | int | float | bool) else f"{operator} needs a single value, not {value!r}"


def problems(condition, path: str) -> list[tuple[str, str]]:
    """What is wrong with a condition, as (path, message) pairs; empty when it is fine."""
    if not isinstance(condition, dict) or not condition:
        return [(path, "a condition is a mapping such as { segment: { eq: students } }")]
    found: list[tuple[str, str]] = []
    for key, value in condition.items():
        here = f"{path}.{key}"
        if key in ("and", "or"):
            if not isinstance(value, list) or not value:
                found.append((here, f"{key} needs a list of conditions"))
            else:
                for index, item in enumerate(value):
                    found += problems(item, f"{here}[{index}]")
        elif key == "not":
            found += problems(value, here)
        else:
            found += _field_problems(key, value, here)
    return found


def _field_problems(field: str, value, path: str) -> list[tuple[str, str]]:
    if not isinstance(value, dict) or len(value) != 1:
        return [(path, f"{field} needs exactly one operator, for example {{ eq: value }}; operators: {', '.join(OPERATORS)}")]
    (operator, operand), = value.items()
    if operator not in OPERATORS:
        known = _nearest(operator, [*OPERATORS, *COMBINATORS])
        return [(f"{path}.{operator}", f"unknown operator {operator!r}{known}; operators: {', '.join(OPERATORS)}")]
    problem = _operand_problem(operator, operand)
    return [(f"{path}.{operator}", problem)] if problem else []
