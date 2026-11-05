"""Check a loaded play as a whole before anything runs (UND-61).

Every mistake is one line: file, the path inside it, what is wrong and, where there is one, the nearest good value.
The checks walk the engine's view of the play (`engine_view` in the loader); `_Checker.outward` turns each path back
into where the play file writes it.
"""

import re
from difflib import get_close_matches
from pathlib import Path

import src.play.stages  # noqa: F401 - importing it registers the stages
from src.play import conditions
from src.play.loader import PlayError, call_values, load, unused_variables
from src.play.model import Play
from src.play.registry import STAGES, Data, Source
from src.play.vocabulary import COMBINATORS, ON_EMPTY, STAGE_TYPES, stage_of

SHARE_TOLERANCE = 0.001
OPTION_OPERATORS = ("eq", "ne", "in", "not_in")
WORDS = {"source": "from", "sources": "from"}  # the engine's name for a `with:` key -> the play's
JEV_FIELDS = ("question", "instructions", "options", "criteria", "state")
PATHS = (  # the engine's path -> the play's, applied in order
    (r"^machine\.initial", "scene.initial"),
    (r"^machine\.states", "scene.beats"),
    (r"\.then$", ".to"),
    (r"\.with\.sources?\b", ".with.from"),
    (r"\.do\.sink\.name$", ".do.write"),
    (r"\.do\.sketch\.file$", ".do.play"),
)


def outward_key(key: str) -> str:
    return WORDS.get(key, key)


def calls_sketch(state: dict) -> bool:
    called = stage_of(state)
    return bool(called) and called[0] == "sketch"


def _nearest(word, choices) -> str:
    match = get_close_matches(str(word), [str(c) for c in choices], n=1)
    return f" (did you mean {match[0]!r}?)" if match else ""


class _Checker:
    def __init__(self, sketch: Play, seen: tuple[Path, ...]):
        self.sketch, self.seen, self.found = sketch, seen, []
        self.states = sketch.machine["states"]
        self.known = set(sketch.outcomes) | set(sketch.candidates)  # every outcome, declared or read from rows

    def problem(self, path: str, message: str) -> None:
        self.found.append(f"{self.sketch.path}: {self.outward(path)}: {message}")

    def outward(self, path: str) -> str:
        """Where the play file writes the thing at the engine's `path`: a source is a stage file or a beat."""
        found = re.match(r"^sources\.([^.\[]+)(.*)$", path)
        if found:
            name, rest = found.groups()
            source = self.sketch.sources.get(name)
            if source is not None and source.kind == "file":
                path = f"stage.{name}{rest}"
            elif source is not None and source.kind == "jev" and rest.lstrip(".").startswith(JEV_FIELDS):
                path = f"scene.beats.{name}.with{rest}"
            else:
                path = f"scene.beats.{name}{rest}"
        for pattern, replacement in PATHS:
            path = re.sub(pattern, replacement, path)
        return path

    def run(self) -> list[str]:
        self.sources()
        self.candidate_sources()
        self.segments()
        self.machine()
        return self.found

    # sources and data ----------------------------------------------------

    def may_be_missing(self, source) -> bool:
        """An optional file source may be missing unless the value that chooses it (`optional: <name>`) was given."""
        chosen_by = source.config.get("optional")
        return bool(chosen_by) and chosen_by not in self.sketch.variables

    def sources(self) -> None:
        for name, source in self.sketch.sources.items():
            if source.kind == "file" and not (source.path and source.path.is_file()) and not self.may_be_missing(source):
                typed = source.config.get("path", "") if isinstance(source.config, dict) else ""
                said = f"file {typed} does not exist (looked for {source.path})" if typed and typed != str(source.path) \
                    else f"file {source.path} does not exist"
                self.problem(f"sources.{name}", said)
            if source.kind == "stage":
                self.stage_source(name, source.config)
            if source.kind == "jev":
                for key, ref in source.config["state"].items():
                    if ref["from"] not in self.sketch.sources or ref["from"] == name:
                        self.problem(f"sources.{name}.state.{key}.from",
                                     f"{ref['from']!r} is not another piece{_nearest(ref['from'], self.sketch.sources)}")

    def stage_source(self, name: str, config: dict) -> None:
        """A beat performed when read: only a library action (`map` or `reduce`), and it must not read itself."""
        at = f"sources.{name}"
        kind = next(iter(config["do"]))
        if kind == "sink" or (kind == "sketch" and "each" not in config):
            self.problem(f"{at}.do", "a beat without `to:` is a `map` or `reduce` action, a Jev question, or a play "
                                     "repeated with `each`; give it `to:` to put it in the scene's flow")
            return
        if "each" in config:
            self.each(at, config)
        if "reduce" in config:
            self.reduce(at, config)
        self.stage(at, config)
        stack = [(name, config)]
        seen = {name}
        while stack:
            _, current = stack.pop()
            reads = [*(current.get("with") or {}).values(), current.get("each")]
            for param in (value for value in reads if isinstance(value, str)):
                if param == name:
                    self.problem(f"{at}.with", f"beat {name!r} reads itself, directly or through another beat")
                    return
                if param in self.sketch.sources and param not in seen and self.sketch.sources[param].kind == "stage":
                    seen.add(param)
                    stack.append((param, self.sketch.sources[param].config))

    def candidate_sources(self) -> None:
        """An outcome read from rows names a piece or a beat whose result holds them."""
        for dimension, candidates in self.sketch.candidates.items():
            if candidates.source not in self.sketch.sources and candidates.source not in self.states:
                known = [*self.sketch.sources, *self.states]
                self.problem(f"outcomes.{dimension}.from",
                             f"{candidates.source!r} is not a piece or a beat{_nearest(candidates.source, known)}")

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
            self.problem("machine.initial", f"beat {initial!r} is not in the scene's flow{_nearest(initial, self.states)}")
        for name, state in self.states.items():
            self.state(name, state)
        self.reaches_a_final_state()
        self.one_writer()

    def one_writer(self) -> None:
        """Each written file is written by one beat."""
        writers: dict[str, str] = {}
        for name, state in self.states.items():
            called = stage_of(state)
            if called and called[0] == "sink":
                if called[1] in writers:
                    self.problem(f"machine.states.{name}.do.sink.name",
                                 f"{called[1]!r} is already written by beat {writers[called[1]]!r}; a file has one writer")
                writers.setdefault(called[1], name)

    def state(self, name: str, state: dict) -> None:
        at = f"machine.states.{name}"
        if state.get("final"):
            self.final_state(at, state)
            return
        if "then" in state and "transitions" in state:
            self.problem(at, "a beat has `to:` or `transitions:`, not both")
        if "do" not in state:
            self.problem(at, "a beat that is not final needs `do` (the action it performs)")
        for target_path, target in self.targets(at, state):
            if target not in self.states:
                self.problem(target_path, f"beat {target!r} is not in the scene's flow{_nearest(target, self.states)}")
        for index, transition in enumerate(state.get("transitions", [])):
            if "if" in transition:
                self.condition(transition["if"], f"{at}.transitions[{index}].if")
        if "each" in state:
            self.each(at, state)
        if "reduce" in state:
            self.reduce(at, state)
        if "do" in state:
            self.stage(at, state)

    def final_state(self, at: str, state: dict) -> None:
        if "then" in state or "transitions" in state or "do" in state:
            self.problem(at, "a final beat does nothing and goes nowhere")
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
            self.problem("machine.states", "no beat is final, so the scene never ends")
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
                self.problem(f"machine.states.{name}", "no path from here reaches a final beat")

    # stages ----------------------------------------------------------------

    def each(self, at: str, state: dict) -> None:
        """`each: <piece>` repeats a play for every row of a piece."""
        self.readable(f"{at}.each", state["each"])
        if not calls_sketch(state):
            self.problem(at, "`each` repeats a play, so `do` must be `play: <file>.yaml`")

    def reduce(self, at: str, state: dict) -> None:
        """`reduce` folds the iterations of an `each`; on its own it has nothing to fold."""
        if "each" not in state:
            self.problem(f"{at}.reduce", "`reduce` folds the iterations of an `each`, and this beat has none")

    def readable(self, at: str, name) -> None:
        """A name a beat reads: a file the stage reads, or a beat performed when read. Not a written file, and not a
        beat in the scene's flow (it may not have been performed when the read happens)."""
        if name in self.sketch.sources:
            return
        if name in self.sketch.sinks:
            self.problem(at, f"{name!r} is a file the play writes (`access: write`); no beat reads it")
        elif name in self.states:
            self.problem(at, f"{name!r} is a beat in the scene's flow; a beat reads stage files and beats without `to:`")
        else:
            self.problem(at, f"{name!r} is not a piece{_nearest(name, self.sketch.sources)}")

    def stage(self, at: str, state: dict) -> None:
        kind, target = stage_of(state)
        name = f"{kind}.{target}"
        if kind == "sink":
            if target not in self.sketch.sinks:
                self.problem(f"{at}.do.sink.name", f"{target!r} is not a file the stage writes (`access: write`)"
                                                   f"{_nearest(target, self.sketch.sinks)}")
            named = (state.get("with") or {}).get("source")
            if named is not None:
                self.readable(f"{at}.with.source", named)
        elif kind == "sketch":
            self.subsketch(f"{at}.do.sketch.file", target, call_values(state), "each" in state)
        elif name not in STAGES:
            self.problem(f"{at}.do.{kind}.{STAGE_TYPES[kind]}",
                         f"unknown action {name!r}{_nearest(name, STAGES)}")
        else:
            self.stage_with(at, name, state.get("with", {}))
            if name == "reduce.blend":
                self.blend(f"{at}.with", state["with"])

    def stage_with(self, at: str, name: str, given: dict) -> None:
        """The `with:` keys must be the parameters the stage's function declares (see `registry`)."""
        wanted = STAGES[name].params
        shown = [outward_key(key) for key in wanted]
        for key in sorted(key for key, param in wanted.items() if param.required and key not in given):
            self.problem(f"{at}.with", f"{name} needs {outward_key(key)!r}")
        for key, value in given.items():
            if key not in wanted:
                self.problem(f"{at}.with.{outward_key(key)}", f"{name} has no {outward_key(key)!r}{_nearest(key, shown)}")
            else:
                self.param(f"{at}.with.{key}", wanted[key].kind, value)

    def param(self, at: str, kind: type, value) -> None:
        if kind is Source:
            self.readable(at, value)
        elif kind is Data and value not in self.sketch.data:
            self.problem(at, f"{value!r} is not under data{_nearest(value, self.sketch.data)}")
        elif kind in (str, int, float) and (isinstance(value, bool) or not isinstance(value, kind)):
            self.problem(at, f"{value!r} must be a {kind.__name__}")

    def subsketch(self, at: str, file: str, given: dict, each: bool) -> None:
        path = (self.sketch.path.parent / f"{file}.yaml").resolve()
        if path in self.seen:
            self.problem(at, f"play {file}.yaml calls itself")
            return
        try:
            child = load(path, variables=given, lenient=each)
        except PlayError as error:
            self.found.extend(error.problems if path.is_file() else
                              [f"{self.sketch.path}: {self.outward(at)}: no play file {path.name}"])
            return
        self.found.extend(_Checker(child, (*self.seen, path)).run())
        declared = next((s.get("outputs") for s in child.machine["states"].values() if s.get("final") and s.get("outputs")), None)
        if declared is None:
            self.problem(at, f"play {file}.yaml declares no outputs, so its weights cannot be blended")
            return
        for dimension in declared:
            if dimension not in self.known and not each:  # a loop's outputs are paired with rows, not blended
                self.problem(at, f"play {file}.yaml outputs {dimension!r}, which is not a declared outcome here")

    # deciders ----------------------------------------------------------------

    def blend(self, at: str, given: dict) -> None:
        """The `with:` of `reduce: { action: blend }`: its entries, `forbid` rules and `on_empty` policy."""
        on_empty = given.get("on_empty")
        if on_empty is not None and on_empty not in ON_EMPTY:
            self.problem(f"{at}.on_empty", f"unknown value {on_empty!r}{_nearest(on_empty, ON_EMPTY)}")
        for index, entry in enumerate(given.get("entries", [])):
            here = f"{at}.entries[{index}]"
            if "decide" in entry:
                self.tree(entry["decide"], f"{here}.decide")
            elif entry["from"] not in self.states or not calls_sketch(self.states[entry["from"]]):
                self.problem(f"{here}.from", f"{entry['from']!r} is not a beat that performs a play"
                                             f"{_nearest(entry['from'], self.states)}")
            if "weight" in entry:
                self.weight(entry["weight"], f"{here}.weight")
        for index, rule in enumerate(given.get("forbid", [])):
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


def check(sketch: Play) -> list[str]:
    """Every problem with the sketch, one line each; an empty list means it is ready to run."""
    found = _Checker(sketch, (sketch.path.resolve(),)).run()
    for unread, how, names in unused_variables(sketch):
        for name in names:
            found.append(f"{unread.path}: {how} {name}: the file does not use it{_nearest(name, unread.uses)}"
                         f"; it uses: {', '.join(sorted(unread.uses)) or 'nothing'}")
    return found


def load_checked(path: Path, overrides: dict[str, str] | None = None, variables: dict[str, str] | None = None) -> Play:
    """Load and check; raise `PlayError` listing every problem."""
    sketch = load(path, overrides, variables)
    problems = check(sketch)
    if problems:
        raise PlayError(problems)
    return sketch
