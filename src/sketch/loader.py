"""Read a sketch file: YAML 1.2, checked against the JSON Schema, built into a `Sketch`.

ruamel.yaml reads YAML 1.2, so `70:30` stays text; PyYAML would turn it into the number 4230.
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from src.paths import ROOT
from src.sketch.model import Sink, Sketch, Source
from src.sketch.vocabulary import SKETCH_PREFIX

SCHEMA = json.loads((ROOT / "schema" / "decision_sketch.schema.json").read_text(encoding="utf-8"))


class SketchError(Exception):
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


def _read(path: Path) -> dict:
    try:
        document = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SketchError([f"{path}: cannot be read: {error.strerror or error}"]) from error
    except YAMLError as error:
        raise SketchError([f"{path}: is not valid YAML: {str(error).splitlines()[0]}"]) from error
    if not isinstance(document, dict):
        raise SketchError([f"{path}: (top): a sketch is a mapping with a name and a machine"])
    return document


def _shape(path: Path, document: dict) -> None:
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        raise SketchError([f"{path}: {dotted(e.absolute_path)}: {e.message}" for e in errors])


def _source(name: str, value, base: Path, overrides: dict[str, str]) -> Source:
    config = {"kind": "file", "path": value} if isinstance(value, str) else dict(value)
    if name in overrides:
        config = {"kind": "file", "path": overrides[name]}
    if config["kind"] == "file":
        given = Path(config["path"])
        return Source(name, "file", config, given if given.is_absolute() else base / given)
    return Source(name, config["kind"], config)


def children(sketch: Sketch) -> dict[str, Sketch]:
    """The sketches this one calls (`do: sketch.<file>`), loaded from beside it; a missing file is left to `check`."""
    found = {}
    for state in sketch.machine["states"].values():
        called = str(state.get("do", ""))
        if called.startswith(SKETCH_PREFIX):
            file = called.removeprefix(SKETCH_PREFIX)
            path = sketch.path.parent / f"{file}.yaml"
            if path.is_file():
                found[file] = load(path)
    return found


def load(path: Path, overrides: dict[str, str] | None = None) -> Sketch:
    """The sketch at `path`. `overrides` replaces a source with a file for this run only."""
    path = Path(path)
    overrides = overrides or {}
    document = _read(path)
    _shape(path, document)
    unknown = sorted(set(overrides) - set(document.get("sources", {})))
    if unknown:
        raise SketchError([f"{path}: --source names {', '.join(unknown)}, which the sketch does not declare"])
    base = path.resolve().parent
    return Sketch(
        path=path,
        name=document["name"],
        description=document.get("description", "").strip(),
        sources={n: _source(n, v, base, overrides) for n, v in document.get("sources", {}).items()},
        sinks={n: Sink(n, v if isinstance(v, str) else v["path"]) for n, v in document.get("sinks", {}).items()},
        outcomes={n: tuple(v) for n, v in document.get("outcomes", {}).items()},
        data=document.get("data", {}),
        machine=document["machine"],
    )
