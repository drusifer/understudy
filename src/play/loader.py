"""Read a play file: YAML 1.2, checked against the JSON Schema, built into a `Play`.

ruamel.yaml reads YAML 1.2, so `70:30` stays text; PyYAML would turn it into the number 4230.

A play is written as a stage (props, and files read or written) and a scene of beats. The engine runs it as sources,
sinks and a machine: `engine_view` is the one place that turns the first into the second (ADR in Sprint 28).
"""

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError, meta
from jsonschema import Draft202012Validator
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from src.paths import ROOT
from src.play.inputs import default_text, problems, value_problem
from src.play.model import Candidates, Play, Sink, Source
from src.play.vocabulary import stage_of

SCHEMA = json.loads((ROOT / "schema" / "play.schema.json").read_text(encoding="utf-8"))


class PlayError(Exception):
    """The sketch cannot be used; `problems` holds one line per mistake, each naming the file and the path."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def dotted(parts) -> str:
    """A path such as machine.states.match_orders.blend[0] from jsonschema's path parts."""
    text = ""
    for part in parts:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text or "(top)"


TEMPLATES = Environment(undefined=StrictUndefined, keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)


def _read(path: Path, variables: dict[str, str], lenient: bool) -> tuple[dict, frozenset[str]]:
    """The sketch's YAML, after Jinja2 has filled in `variables`, and the names of the variables the file uses.

    `lenient` fills any variable not given with an empty value, to read the shape of a sketch whose values are not
    known yet (the child of an `each`).
    """
    return _parse(path, _text(path), variables, lenient)


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise PlayError([f"{path}: cannot be read: {error.strerror or error}"]) from error


def _parse(path: Path, text: str, variables: dict[str, str], lenient: bool) -> tuple[dict, frozenset[str]]:
    """What `_read` makes of the file's `text`: render the template, then read the YAML."""
    try:
        used = frozenset(meta.find_undeclared_variables(TEMPLATES.parse(text)))
        given = {**{name: "" for name in used}, **variables} if lenient else variables
        rendered = TEMPLATES.from_string(text).render(given)
    except TemplateSyntaxError as error:
        raise PlayError([f"{path}: line {error.lineno}: {error.message}"]) from error
    except UndefinedError as error:
        name = str(error).split("'")[1] if "'" in str(error) else "a variable"
        hint = f"pass --with {name}=<value>, or write {{{{ {name} | default(…) }}}}"
        raise PlayError([f"{path}: needs a value for {name!r}: {hint}"]) from error
    try:
        document = YAML(typ="safe").load(rendered)
    except YAMLError as error:
        raise PlayError([f"{path}: is not valid YAML: {str(error).splitlines()[0]}"]) from error
    if not isinstance(document, dict):
        raise PlayError([f"{path}: (top): a play is a mapping with a name and a scene"])
    return document, used


@lru_cache(maxsize=256)
def _template(path: str, text: str) -> tuple[dict, frozenset[str]]:
    return _parse(Path(path), text, {}, True)


def _shared_template(path: Path) -> tuple[dict, frozenset[str]]:
    """What `read_template` reads, once per version of the file: the file is read each time (a few microseconds) and its
    text is the cache key, so an edited file is always read again, whatever its modification time says. The document is
    shared, so callers here only read it. A file that cannot be read or parsed is not cached; the error says why each
    time."""
    return _template(str(path), _text(path))


def read_template(path: Path) -> tuple[dict, frozenset[str]]:
    """A sketch file as written, with every `--with` name given an empty value: its document and the names it takes.
    Nothing is checked beyond YAML and Jinja syntax, so a sketch that needs its values can still be listed. The document
    is a copy the caller may change."""
    document, used = _shared_template(Path(path))
    return deepcopy(document), used


def _shape(path: Path, document: dict) -> None:
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        raise PlayError([f"{path}: {dotted(e.absolute_path)}: {e.message}" for e in errors])


def props_of(document: dict) -> dict[str, dict]:
    """The props a play's stage declares (a typed value each: choice, range, count or switch), by name: every stage
    entry that is not a file, so a wrong kind is reported as a wrong prop."""
    stage = document.get("stage")
    if not isinstance(stage, dict):
        return {}
    return {name: piece for name, piece in stage.items() if not (isinstance(piece, dict) and piece.get("kind") == "file")}


def is_flow(beat: dict) -> bool:
    """A beat in the scene's flow: it says where to go next, or it ends the scene. Any other beat is performed when
    another beat first reads it."""
    return "to" in beat or "transitions" in beat or bool(beat.get("final"))


def engine_view(path: Path, document: dict) -> dict:
    """The play as the engine runs it: the stage's read files and the beats performed when read are its sources, the
    files it writes are its sinks, and the flow beats are its machine's states (`to:` is the machine's next state)."""
    sources, sinks, states = {}, {}, {}
    for name, piece in (document.get("stage") or {}).items():
        if piece.get("kind") != "file":
            continue
        if piece.get("access") == "write":
            sinks[name] = piece["path"]
        else:
            sources[name] = {key: value for key, value in piece.items() if key != "access"}
    stage = document.get("stage") or {}
    wrong = [f"{path}: scene.beats.{name}: {name!r} is also on the stage; a name means one thing in a play"
             for name in document["scene"]["beats"] if name in stage]
    for name, beat in document["scene"]["beats"].items():
        if not is_flow(beat):
            sources[name] = _engine_source(beat)
        elif "jev" in beat.get("do", {}):
            wrong.append(f"{path}: scene.beats.{name}: a Jev beat is performed when another beat reads it, so it has no "
                         "`to:` or `transitions:`")
        else:
            states[name] = _engine_state(beat)
    if wrong:
        raise PlayError(wrong)
    return {"sources": sources, "sinks": sinks, "machine": {"initial": document["scene"]["initial"], "states": states}}


def _engine_state(beat: dict) -> dict:
    state = {key: value for key, value in beat.items() if key not in ("to", "do", "with")}
    if "to" in beat:
        state["then"] = beat["to"]
    if "do" in beat:
        state["do"] = _engine_do(beat["do"])
    if "with" in beat:
        state["with"] = _engine_with(beat["with"])
    return state


def _engine_source(beat: dict) -> dict:
    if "jev" in beat.get("do", {}):
        return {"kind": "jev", **beat["do"]["jev"], **beat.get("with", {})}
    return {"kind": "stage", **_engine_state(beat)}


def _engine_do(do: dict) -> dict:
    ((kind, value),) = do.items()
    if kind == "write":
        return {"sink": {"name": value}}
    if kind == "play":
        return {"sketch": {"file": value.removesuffix(".yaml")}}
    return dict(do)


def _engine_with(given: dict) -> dict:
    """`from:` names the piece an action works on: one name (the engine's `source`) or a list (`sources`)."""
    if "from" not in given:
        return dict(given)
    rest = {key: value for key, value in given.items() if key != "from"}
    return {("sources" if isinstance(given["from"], list) else "source"): given["from"], **rest}


def _source(name: str, value, base: Path, overrides: dict[str, str]) -> Source:
    config = dict(value)
    if name in overrides:
        config = {"kind": "file", "path": overrides[name]}
    if config["kind"] == "file":
        given = Path(config["path"])
        if config.get("optional"):  # read from where you run, like the `--with` value that chooses it
            return Source(name, "file", config, given.absolute())
        return Source(name, "file", config, given if given.is_absolute() else base / given)
    return Source(name, config["kind"], config)


def children(sketch: Play) -> dict[str, Play]:
    """The sketches this one calls (`do: sketch.<file>`), by the name of the state that calls each, loaded from
    beside it with that call's `with`; a missing file is left to `check`. One sketch may be called many times."""
    found = {}
    for name, state in sketch.machine["states"].items():
        called = stage_of(state)
        if called and called[0] == "sketch":
            path = child_path(sketch, called[1])
            if path.is_file():
                found[name] = load(path, variables=call_values(state), lenient="each" in state)
    return found


def source_children(sketch: Play) -> list[Play]:
    """The sketches this one calls from a stage source (`kind: stage` with `do: { sketch: ... }`), loaded as `children` are."""
    found = []
    for source in sketch.sources.values():
        called = stage_of(source.config) if source.kind == "stage" else None
        if called and called[0] == "sketch" and child_path(sketch, called[1]).is_file():
            found.append(load(child_path(sketch, called[1]), variables=call_values(source.config), lenient="each" in source.config))
    return found


def call_values(state: dict) -> dict:
    """The values a state's call gives its sketch: its `with`, and the name a folding `each` passes its running list
    under (empty until the run), so a child that does not use the name is caught by the unused-name check."""
    return {**state.get("with", {}), **({state["reduce"]["into"]: []} if "reduce" in state else {})}


def child_path(sketch: Play, file: str) -> Path:
    """The file a `do: { sketch: { file: ... } }` names, beside the sketch that calls it."""
    return sketch.path.parent / f"{file}.yaml"


def unused_variables(sketch: Play, how: str = "--with") -> list[tuple[Play, str, list[str]]]:
    """Per file of the sketch and the sketches it calls: the names given to it (`--with` or a call's `with`)
    that the file does not use, as (sketch, how it was given, names)."""
    found = []
    unused = sorted(set(sketch.variables) - sketch.uses)
    if unused:
        found.append((sketch, how, unused))
    for child in children(sketch).values():
        found += unused_variables(child, "with")
    return found


def _declared_inputs(path: Path, given: dict[str, str]) -> dict[str, dict]:
    """The sketch's `inputs:` (read before its values are known, as the console lists it), refused when a declaration is
    wrong or a value given for one is outside its limits. A file that cannot be read at all is left to `load`."""
    try:
        document, _ = _shared_template(path)
    except PlayError:
        return {}
    declared = props_of(document)
    found = [f"{path}: {problem}" for name, spec in declared.items() for problem in problems(name, spec)]
    found += [f"{path}: {problem}" for name, text in given.items() if name in declared
              and (problem := value_problem(name, declared[name], text))]
    if found:
        raise PlayError(found)
    return deepcopy(declared)  # the sketch keeps these; the shared document must not change under another caller


def load(
    path: Path, overrides: dict[str, str] | None = None, variables: dict[str, str] | None = None, *, lenient: bool = False,
) -> Play:
    """The sketch at `path`. `overrides` replaces a source with a file for this run only.

    The file is a Jinja2 template: `variables` (`--with` on the command line, `with` on a call) fill it in before
    it is read as YAML.
    """
    path = Path(path)
    overrides = overrides or {}
    variables = variables or {}
    declared = _declared_inputs(path, variables)
    effective = {**{name: default_text(spec) for name, spec in declared.items()}, **variables}
    document, uses = _read(path, effective, lenient)
    _shape(path, document)
    engine = engine_view(path, document)
    unknown = sorted(set(overrides) - {n for n, s in engine["sources"].items() if s.get("kind") == "file"})
    if unknown:
        raise PlayError([f"{path}: --source names {', '.join(unknown)}, which is not a file on the play's stage"])
    base = path.resolve().parent
    return Play(
        path=path,
        name=document["name"],
        description=document.get("description", "").strip(),
        sources={n: _source(n, v, base, overrides) for n, v in engine["sources"].items()},
        sinks={n: Sink(n, v) for n, v in engine["sinks"].items()},
        outcomes={n: tuple(v) for n, v in document.get("outcomes", {}).items() if isinstance(v, list)},
        candidates={n: Candidates(v["from"], v["key"]) for n, v in document.get("outcomes", {}).items() if isinstance(v, dict)},
        data=document.get("data", {}),
        machine=engine["machine"],
        inputs=declared,
        variables=variables,
        uses=uses,
    )
