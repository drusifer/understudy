"""Typed inputs: what a sketch declares under `inputs:` and what a value for one may be (ADR-0053).

    mood:     { kind: choice, options: [fun, serious], default: fun }
    weight:   { kind: range, min: 0, max: 1, step: 0.1, default: 0.3 }
    tickets:  { kind: count, min: 1, max: 10, default: 2 }
    evenings: { kind: switch, default: "on" }

Values reach the template as text (a switch is `on` or `off`). Both the command line and the console check a value
against its declaration with `value_problem`, so a limit means the same everywhere.
"""

import re

# A number is plain ASCII digits (a sign and a decimal point at most), so the run gets exactly the text that was checked:
# not `1e2`, `nan`, `0x5`, a padded or non-ASCII digit string (Switch, Sprint 24 phase 4).
PLAIN_NUMBER = re.compile(r"-?[0-9]+(\.[0-9]+)?")
PLAIN_WHOLE = re.compile(r"-?[0-9]+")

KINDS = ("choice", "range", "count", "switch")
SWITCH = ("on", "off")
_TOLERANCE = 1e-9
_STEP_TOLERANCE = 1e-6  # a value is on a step when it is this close to a whole number of steps from the minimum


def problems(name: str, spec) -> list[str]:
    """What is wrong with one declaration, as sentences that name the input (empty when it is right)."""
    at = f"input {name!r}: "
    if not isinstance(spec, dict) or spec.get("kind") not in KINDS:
        kind = spec.get("kind") if isinstance(spec, dict) else spec
        return [f"{at}unknown kind {kind!r}; the kinds are {', '.join(KINDS)}"]
    if "default" not in spec:
        return [f"{at}needs a default"]
    return [f"{at}{problem}" for problem in _DECLARATION[spec["kind"]](spec)]


def default_text(spec: dict) -> str:
    """The value an input has when it is left alone, as the text a template sees."""
    return _text(spec["default"])


def value_problem(name: str, spec: dict, text: str) -> str | None:
    """None when `text` is a value the input allows, else a sentence naming the input and the limit."""
    problem = _VALUE[spec["kind"]](spec, str(text))
    return f"input {name!r}: {problem}" if problem else None


def _text(value) -> str:
    return str(int(value)) if isinstance(value, float) and value == int(value) and abs(value) >= 1 else str(value)


def _number(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _choice(spec: dict) -> list[str]:
    options = spec.get("options")
    if not isinstance(options, list) or not options:
        return ["a choice needs at least one option"]
    names = [str(option) for option in options]
    return [] if str(spec["default"]) in names else [f"default {str(spec['default'])!r} is not one of {', '.join(names)}"]


def _range(spec: dict) -> list[str]:
    low, high, step = spec.get("min"), spec.get("max"), spec.get("step")
    if not all(_number(each) for each in (low, high, step)):
        return ["a range needs a min, a max and a step, all numbers"]
    if high <= low:
        return ["max must be above min"]
    if step <= 0:
        return ["step must be above 0"]
    if not _number(spec["default"]) or not low <= spec["default"] <= high:
        return [f"default {_text(spec['default'])} is outside {_text(low)} to {_text(high)}"]
    return []


def _count(spec: dict) -> list[str]:
    low, high, default = spec.get("min"), spec.get("max"), spec["default"]
    if not (isinstance(low, int) and isinstance(high, int)) or isinstance(low, bool) or isinstance(high, bool):
        return ["a count needs a min and a max, both whole numbers"]
    if high <= low:
        return ["max must be above min"]
    if not isinstance(default, int) or isinstance(default, bool):
        return ["default must be a whole number"]
    return [] if low <= default <= high else [f"default {default} is outside {low} to {high}"]


def _switch(spec: dict) -> list[str]:
    return [] if spec["default"] in SWITCH else ["default must be on or off"]


def _choice_value(spec: dict, text: str) -> str | None:
    names = [str(option) for option in spec["options"]]
    return None if text in names else f"{text} is not one of {', '.join(names)}"


def _range_value(spec: dict, text: str) -> str | None:
    if not PLAIN_NUMBER.fullmatch(text):
        return f"{text} is not a number"
    value = float(text)
    low, high, step = spec["min"], spec["max"], spec["step"]
    if not low - _TOLERANCE <= value <= high + _TOLERANCE:
        return f"{text} is outside {_text(low)} to {_text(high)}"
    steps = (value - low) / step
    if abs(steps - round(steps)) > _STEP_TOLERANCE:
        return f"{text} is not a multiple of {_text(step)} from {_text(low)}"
    return None


def _count_value(spec: dict, text: str) -> str | None:
    if not PLAIN_WHOLE.fullmatch(text):
        return f"{text} is not a whole number"
    return None if spec["min"] <= int(text) <= spec["max"] else f"{text} is outside {spec['min']} to {spec['max']}"


def _switch_value(spec: dict, text: str) -> str | None:  # noqa: ARG001 - every kind's check takes its declaration
    return None if text in SWITCH else f"{text} is not on or off"


_DECLARATION = {"choice": _choice, "range": _range, "count": _count, "switch": _switch}
_VALUE = {"choice": _choice_value, "range": _range_value, "count": _count_value, "switch": _switch_value}
