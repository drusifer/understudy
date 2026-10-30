"""The owner's machine, as a python-statemachine (ADR-0040).

The sketch writes states, `then` and guarded `transitions`; python-statemachine only knows events and named
guards, so each stage completing is the event `ok` and each `if` becomes a guard that evaluates the explicit
YAML condition against the stage's result.
"""

import json

from statemachine.io import load

from src.sketch.conditions import holds
from src.sketch.model import Sketch


def _guard(condition: dict):
    def guard(self, *args, **kwargs):  # noqa: ARG001 - python-statemachine passes event data we do not use
        return isinstance(self.result, dict) and holds(condition, self.result)
    return guard


def _state(sketch: Sketch, name: str, state: dict, guards: dict) -> dict:
    entry: dict = {}
    if name == sketch.machine["initial"]:
        entry["initial"] = True
    if state.get("final"):
        entry["final"] = True
        return entry
    transitions = [{"event": "ok", "target": state["then"]}] if "then" in state else []
    for index, transition in enumerate(state.get("transitions", [])):
        item = {"event": "ok", "target": transition["to"]}
        if "if" in transition:
            guards[f"guard_{name}_{index}"] = _guard(transition["if"])
            item["cond"] = f"guard_{name}_{index}"
        transitions.append(item)
    entry["transitions"] = transitions
    return entry


def build_machine(sketch: Sketch):
    """A started machine for one run; `machine.model.result` holds the last stage's result for the guards."""
    guards: dict = {}
    states = {name: _state(sketch, name, state, guards) for name, state in sketch.machine["states"].items()}
    machine_class = load(json.dumps({"name": "sketch", "states": states}), format="yaml")
    model = type("Model", (), {"result": None, **guards})()
    return machine_class(model)
