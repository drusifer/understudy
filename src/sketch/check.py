"""Check a loaded sketch as a whole before anything runs (UND-61).

Every mistake is one line: file, the path inside it, what is wrong and, where there is one, the nearest good value.
"""

from difflib import get_close_matches
from pathlib import Path

from src.sketch import conditions
from src.sketch.loader import SketchError, load
from src.sketch.model import Sketch
from src.sketch.vocabulary import COMBINATORS, ON_EMPTY, SINK_PREFIX, SKETCH_PREFIX, STAGES

SHARE_TOLERANCE = 0.001
OPTION_OPERATORS = ("eq", "ne", "in", "not_in")


def _nearest(word, choices) -> str:
    match = get_close_matches(str(word), [str(c) for c in choices], n=1)
    return f" (did you mean {match[0]!r}?)" if match else ""


class _Checker:
    def __init__(self, sketch: Sketch, seen: tuple[Path, ...]):
        self.sketch, self.seen, self.found = sketch, seen, []
        self.states = sketch.machine["states"]

    def problem(self, path: str, message: str) -> None:
        self.found.append(f"{self.sketch.path}: {path}: {message}")

    def run(self) -> list[str]:
        self.sources()
        self.segments()
        self.machine()
        return self.found

    # sources and data ----------------------------------------------------

    def sources(self) -> None:
        for name, source in self.sketch.sources.items():
            if source.kind == "file" and not (source.path and source.path.is_file()):
                self.problem(f"sources.{name}", f"file {source.path} does not exist")
            if source.kind == "jev":
                for key, ref in source.config["state"].items():
                    if ref["from"] not in self.sketch.sources or ref["from"] == name:
                        self.problem(f"sources.{name}.state.{key}.from",
                                     f"{ref['from']!r} is not another source{_nearest(ref['from'], self.sketch.sources)}")

    def segments(self) -> None:
        segments = self.sketch.data.get("segments")
        if segments is None:
            return
        shares = [s.get("share") for s in segments if isinstance(s, dict)]
        if not all(isinstance(s, int | float) and not isinstance(s, bool) for s in shares) or len(shares) != len(segments):
            self.problem("data.segments", "every segment needs a name and a numeric share")
        elif abs(sum(shares) - 1) > SHARE_TOLERANCE:
            self.problem("data.segments", f"shares add up to {sum(shares):g}, not 1")

    # machine -------------------------------------------------------------

    def machine(self) -> None:
        if self.sketch.machine["initial"] not in self.states:
            initial = self.sketch.machine["initial"]
            self.problem("machine.initial", f"state {initial!r} does not exist{_nearest(initial, self.states)}")
        for name, state in self.states.items():
            self.state(name, state)
        self.reaches_a_final_state()

    def state(self, name: str, state: dict) -> None:
        at = f"machine.states.{name}"
        if state.get("final"):
            self.final_state(at, state)
            return
        if ("then" in state) == ("transitions" in state):
            self.problem(at, "a state that is not final needs exactly one of `then` or `transitions`")
        if ("do" in state) == ("blend" in state):
            self.problem(at, "a state needs exactly one of `do` (a stage) or `blend` (deciders)")
        for target_path, target in self.targets(at, state):
            if target not in self.states:
                self.problem(target_path, f"state {target!r} does not exist{_nearest(target, self.states)}")
        for index, transition in enumerate(state.get("transitions", [])):
            if "if" in transition:
                self.condition(transition["if"], f"{at}.transitions[{index}].if")
        if "do" in state:
            self.stage(at, state)
        if "blend" in state:
            self.blend(at, state)
        if state.get("on_empty") is not None and state["on_empty"] not in ON_EMPTY:
            self.problem(f"{at}.on_empty", f"unknown value {state['on_empty']!r}{_nearest(state['on_empty'], ON_EMPTY)}")

    def final_state(self, at: str, state: dict) -> None:
        if "then" in state or "transitions" in state or "do" in state or "blend" in state:
            self.problem(at, "a final state does nothing and goes nowhere")
        for dimension in state.get("returns", {}).get("decider", []):
            if dimension not in self.sketch.outcomes and not self.is_subsketch_file():
                self.problem(f"{at}.returns.decider", f"{dimension!r} is not a declared outcome")

    def is_subsketch_file(self) -> bool:
        return not self.sketch.outcomes

    def targets(self, at: str, state: dict):
        if "then" in state:
            yield f"{at}.then", state["then"]
        for index, transition in enumerate(state.get("transitions", [])):
            yield f"{at}.transitions[{index}].to", transition["to"]

    def reaches_a_final_state(self) -> None:
        finals = {n for n, s in self.states.items() if s.get("final")}
        if not finals:
            self.problem("machine.states", "no state is final, so the machine never ends")
            return
        onward = {n: [t for _, t in self.targets("", s) if t in self.states] for n, s in self.states.items()}
        live = set(finals)
        grew = True
        while grew:
            grew = False
            for name, nexts in onward.items():
                if name not in live and any(n in live for n in nexts):
                    live.add(name)
                    grew = True
        for name in self.states:
            if name not in live:
                self.problem(f"machine.states.{name}", "no path from here reaches a final state")

    # stages ----------------------------------------------------------------

    def stage(self, at: str, state: dict) -> None:
        name = state["do"]
        if name.startswith(SINK_PREFIX):
            sink = name[len(SINK_PREFIX):]
            if sink not in self.sketch.sinks:
                self.problem(f"{at}.do", f"sink {sink!r} is not declared{_nearest(sink, self.sketch.sinks)}")
        elif name.startswith(SKETCH_PREFIX):
            self.subsketch(f"{at}.do", name[len(SKETCH_PREFIX):])
        elif name not in STAGES:
            self.problem(f"{at}.do", f"unknown stage {name!r}{_nearest(name, STAGES)}")
        else:
            self.stage_with(at, name, state.get("with", {}))

    def stage_with(self, at: str, name: str, given: dict) -> None:
        wanted = STAGES[name]
        for key in sorted(set(wanted) - set(given)):
            self.problem(f"{at}.with", f"{name} needs {key!r}")
        for key, value in given.items():
            if key not in wanted:
                self.problem(f"{at}.with.{key}", f"{name} has no {key!r}{_nearest(key, wanted)}")
            elif wanted[key] == "source" and value not in self.sketch.sources:
                self.problem(f"{at}.with.{key}", f"{value!r} is not a source{_nearest(value, self.sketch.sources)}")
            elif wanted[key] == "data" and value not in self.sketch.data:
                self.problem(f"{at}.with.{key}", f"{value!r} is not under data{_nearest(value, self.sketch.data)}")

    def subsketch(self, at: str, file: str) -> None:
        path = (self.sketch.path.parent / f"{file}.yaml").resolve()
        if path in self.seen:
            self.problem(at, f"sketch {file!r} calls itself")
            return
        try:
            child = load(path)
        except SketchError as error:
            self.found.extend(error.problems if path.is_file() else [f"{self.sketch.path}: {at}: no sketch file {path.name}"])
            return
        self.found.extend(_Checker(child, (*self.seen, path)).run())
        returned = next((s.get("returns") for s in child.machine["states"].values() if s.get("final") and s.get("returns")), None)
        if returned is None:
            self.problem(at, f"sketch {file!r} returns nothing, so it cannot be a decider")
            return
        for dimension in returned["decider"]:
            if dimension not in self.sketch.outcomes:
                self.problem(at, f"sketch {file!r} returns {dimension!r}, which is not a declared outcome here")

    # deciders ----------------------------------------------------------------

    def blend(self, at: str, state: dict) -> None:
        for index, entry in enumerate(state["blend"]):
            here = f"{at}.blend[{index}]"
            if "decide" in entry:
                self.tree(entry["decide"], f"{here}.decide")
            elif entry["decider"] not in self.states or not str(self.states[entry["decider"]].get("do", "")).startswith(SKETCH_PREFIX):
                self.problem(f"{here}.decider", f"{entry['decider']!r} is not a state that calls a sketch"
                                                f"{_nearest(entry['decider'], self.states)}")
            if "weight" in entry:
                self.weight(entry["weight"], f"{here}.weight")
        for index, rule in enumerate(state.get("forbid", [])):
            self.condition(rule["when"], f"{at}.forbid[{index}].when")
            self.condition(rule["drop"], f"{at}.forbid[{index}].drop")
            self.options(rule["drop"], f"{at}.forbid[{index}].drop")

    def tree(self, node: dict, at: str) -> None:
        if "drink" in node:
            self.leaf(node["drink"], f"{at}.drink")
            return
        if "if" not in node or "then" not in node:
            self.problem(at, "a decision node is `if` / `then` / `else`, or a leaf with `drink`")
            return
        self.condition(node["if"], f"{at}.if")
        self.tree(node["then"], f"{at}.then")
        if "else" in node:
            self.tree(node["else"], f"{at}.else")

    def leaf(self, rows, at: str) -> None:
        if not isinstance(rows, list) or not rows:
            self.problem(at, "a leaf is a list of weighted rows")
            return
        total = 0.0
        for index, row in enumerate(rows):
            here = f"{at}[{index}]"
            weight = row.get("weight") if isinstance(row, dict) else None
            if not isinstance(weight, int | float) or isinstance(weight, bool) or weight < 0:
                self.problem(here, "a row needs a weight that is a number, 0 or more")
                continue
            total += weight
            for key, value in row.items():
                if key != "weight":
                    self.option(key, value, here)
        if abs(total - 1) > SHARE_TOLERANCE:
            self.problem(at, f"weights add up to {total:g}, not 1")

    def dimension(self, dimension: str, at: str) -> bool:
        """True when the dimension is declared; otherwise records the problem."""
        if dimension in self.sketch.outcomes:
            return True
        self.problem(at, f"{dimension!r} is not a declared outcome{_nearest(dimension, self.sketch.outcomes)}")
        return False

    def option(self, dimension: str, value, at: str) -> None:
        if self.dimension(dimension, f"{at}.{dimension}") and value not in self.sketch.outcomes[dimension]:
            self.problem(f"{at}.{dimension}",
                         f"{value!r} is not an option of {dimension}{_nearest(value, self.sketch.outcomes[dimension])}")

    def options(self, drop: dict, at: str) -> None:
        for dimension, test in drop.items():
            if dimension in COMBINATORS or not self.dimension(dimension, f"{at}.{dimension}"):
                continue
            for operator, operand in (test.items() if isinstance(test, dict) else []):
                for value in (operand if isinstance(operand, list) else [operand]):
                    known = value in self.sketch.outcomes[dimension] or conditions.is_slice(value)
                    if operator in OPTION_OPERATORS and not known:
                        self.problem(f"{at}.{dimension}.{operator}", f"{value!r} is not an option of {dimension}"
                                                                    f"{_nearest(value, self.sketch.outcomes[dimension])}")

    def weight(self, weight, at: str) -> None:
        if isinstance(weight, dict):
            self.condition(weight["if"], f"{at}.if")
            self.weight(weight["then"], f"{at}.then")
            if "else" in weight:
                self.weight(weight["else"], f"{at}.else")

    def condition(self, condition, at: str) -> None:
        for path, message in conditions.problems(condition, at):
            self.problem(path, message)


def check(sketch: Sketch) -> list[str]:
    """Every problem with the sketch, one line each; an empty list means it is ready to run."""
    return _Checker(sketch, (sketch.path.resolve(),)).run()


def load_checked(path: Path, overrides: dict[str, str] | None = None) -> Sketch:
    """Load and check; raise `SketchError` listing every problem."""
    sketch = load(path, overrides)
    problems = check(sketch)
    if problems:
        raise SketchError(problems)
    return sketch
