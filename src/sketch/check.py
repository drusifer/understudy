"""Check a loaded sketch as a whole before anything runs (UND-61).

Every mistake is one line: file, the path inside it, what is wrong and, where there is one, the nearest good value.
"""

from difflib import get_close_matches
from pathlib import Path

import src.sketch.stages  # noqa: F401 - importing it registers the stages
from src.sketch import conditions
from src.sketch.loader import SketchError, load, unused_variables
from src.sketch.model import Sketch
from src.sketch.registry import STAGES, Data, Source
from src.sketch.vocabulary import COMBINATORS, ON_EMPTY, STAGE_TYPES, stage_of

SHARE_TOLERANCE = 0.001
OPTION_OPERATORS = ("eq", "ne", "in", "not_in")


def calls_sketch(state: dict) -> bool:
    called = stage_of(state)
    return bool(called) and called[0] == "sketch"


def _nearest(word, choices) -> str:
    match = get_close_matches(str(word), [str(c) for c in choices], n=1)
    return f" (did you mean {match[0]!r}?)" if match else ""


class _Checker:
    def __init__(self, sketch: Sketch, seen: tuple[Path, ...]):
        self.sketch, self.seen, self.found = sketch, seen, []
        self.states = sketch.machine["states"]
        self.known = set(sketch.outcomes) | set(sketch.candidates)  # every outcome, declared or read from rows

    def problem(self, path: str, message: str) -> None:
        self.found.append(f"{self.sketch.path}: {path}: {message}")

    def run(self) -> list[str]:
        self.sources()
        self.candidate_sources()
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

    def candidate_sources(self) -> None:
        """An outcome read from rows names a source or a state whose result holds them."""
        for dimension, candidates in self.sketch.candidates.items():
            if candidates.source not in self.sketch.sources and candidates.source not in self.states:
                known = [*self.sketch.sources, *self.states]
                self.problem(f"outcomes.{dimension}.from",
                             f"{candidates.source!r} is neither a source nor a state{_nearest(candidates.source, known)}")

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
        if "each" in state:
            self.each(at, state)
        if "do" in state:
            self.stage(at, state)
        if "blend" in state:
            self.blend(at, state)
        if state.get("on_empty") is not None and state["on_empty"] not in ON_EMPTY:
            self.problem(f"{at}.on_empty", f"unknown value {state['on_empty']!r}{_nearest(state['on_empty'], ON_EMPTY)}")

    def final_state(self, at: str, state: dict) -> None:
        if "then" in state or "transitions" in state or "do" in state or "blend" in state:
            self.problem(at, "a final state does nothing and goes nowhere")
        for dimension in state.get("outputs", []):
            if dimension not in self.known and not self.is_subsketch_file():
                self.problem(f"{at}.outputs", f"{dimension!r} is not a declared outcome")

    def is_subsketch_file(self) -> bool:
        return not self.known

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

    def each(self, at: str, state: dict) -> None:
        """`each: <source>` repeats a sketch for every row of a source."""
        if state["each"] not in self.sketch.sources:
            self.problem(f"{at}.each", f"{state['each']!r} is not a source{_nearest(state['each'], self.sketch.sources)}")
        if not calls_sketch(state):
            self.problem(at, "`each` repeats a sketch, so `do` must be `sketch: { file: ... }`")

    def stage(self, at: str, state: dict) -> None:
        kind, target = stage_of(state)
        name = f"{kind}.{target}"
        if kind == "sink":
            if target not in self.sketch.sinks:
                self.problem(f"{at}.do.sink.name", f"sink {target!r} is not declared{_nearest(target, self.sketch.sinks)}")
        elif kind == "sketch":
            self.subsketch(f"{at}.do.sketch.file", target, state.get("with", {}), "each" in state)
        elif name not in STAGES:
            self.problem(f"{at}.do.{kind}.{STAGE_TYPES[kind]}",
                         f"unknown stage {name!r}{_nearest(name, [n for n in STAGES if n != 'blend'])}")
        else:
            self.stage_with(at, name, state.get("with", {}))

    def stage_with(self, at: str, name: str, given: dict) -> None:
        """The `with:` keys must be the parameters the stage's function declares (see `registry`)."""
        wanted = STAGES[name].params
        for key in sorted(key for key, param in wanted.items() if param.required and key not in given):
            self.problem(f"{at}.with", f"{name} needs {key!r}")
        for key, value in given.items():
            if key not in wanted:
                self.problem(f"{at}.with.{key}", f"{name} has no {key!r}{_nearest(key, wanted)}")
            else:
                self.param(f"{at}.with.{key}", wanted[key].kind, value)

    def param(self, at: str, kind: type, value) -> None:
        if kind is Source and value not in self.sketch.sources:
            self.problem(at, f"{value!r} is not a source{_nearest(value, self.sketch.sources)}")
        elif kind is Data and value not in self.sketch.data:
            self.problem(at, f"{value!r} is not under data{_nearest(value, self.sketch.data)}")
        elif kind in (str, int, float) and (isinstance(value, bool) or not isinstance(value, kind)):
            self.problem(at, f"{value!r} must be a {kind.__name__}")

    def subsketch(self, at: str, file: str, given: dict, each: bool) -> None:
        path = (self.sketch.path.parent / f"{file}.yaml").resolve()
        if path in self.seen:
            self.problem(at, f"sketch {file!r} calls itself")
            return
        try:
            child = load(path, variables=given, lenient=each)
        except SketchError as error:
            self.found.extend(error.problems if path.is_file() else [f"{self.sketch.path}: {at}: no sketch file {path.name}"])
            return
        self.found.extend(_Checker(child, (*self.seen, path)).run())
        declared = next((s.get("outputs") for s in child.machine["states"].values() if s.get("final") and s.get("outputs")), None)
        if declared is None:
            self.problem(at, f"sketch {file!r} declares no outputs, so its weights cannot be blended")
            return
        for dimension in declared:
            if dimension not in self.known and not each:  # a loop's outputs are paired with rows, not blended
                self.problem(at, f"sketch {file!r} outputs {dimension!r}, which is not a declared outcome here")

    # deciders ----------------------------------------------------------------

    def blend(self, at: str, state: dict) -> None:
        for index, entry in enumerate(state["blend"]):
            here = f"{at}.blend[{index}]"
            if "decide" in entry:
                self.tree(entry["decide"], f"{here}.decide")
            elif entry["from"] not in self.states or not calls_sketch(self.states[entry["from"]]):
                self.problem(f"{here}.from", f"{entry['from']!r} is not a state that calls a sketch"
                                             f"{_nearest(entry['from'], self.states)}")
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
        if dimension in self.known:
            return True
        self.problem(at, f"{dimension!r} is not a declared outcome{_nearest(dimension, self.known)}")
        return False

    def option(self, dimension: str, value, at: str) -> None:
        """An option of a declared outcome; the options of one read from rows are known only when it runs."""
        if self.dimension(dimension, f"{at}.{dimension}") and dimension in self.sketch.outcomes \
                and value not in self.sketch.outcomes[dimension]:
            self.problem(f"{at}.{dimension}",
                         f"{value!r} is not an option of {dimension}{_nearest(value, self.sketch.outcomes[dimension])}")

    def options(self, drop: dict, at: str) -> None:
        for dimension, test in drop.items():
            if dimension in COMBINATORS or not self.dimension(dimension, f"{at}.{dimension}") \
                    or dimension in self.sketch.candidates:
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
    found = _Checker(sketch, (sketch.path.resolve(),)).run()
    for unread, how, names in unused_variables(sketch):
        for name in names:
            found.append(f"{unread.path}: {how} {name}: the file does not use it{_nearest(name, unread.uses)}"
                         f"; it uses: {', '.join(sorted(unread.uses)) or 'nothing'}")
    return found


def load_checked(path: Path, overrides: dict[str, str] | None = None, variables: dict[str, str] | None = None) -> Sketch:
    """Load and check; raise `SketchError` listing every problem."""
    sketch = load(path, overrides, variables)
    problems = check(sketch)
    if problems:
        raise SketchError(problems)
    return sketch
