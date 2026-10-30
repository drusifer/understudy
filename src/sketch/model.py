"""The sketch as typed objects (the domain terms of docs/DOMAIN.md)."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Source:
    """A named, read-only input. `kind` is `file` or `jev`; `path` is set for a file source."""

    name: str
    kind: str
    config: dict = field(default_factory=dict)
    path: Path | None = None


@dataclass(frozen=True)
class Sink:
    """A named output: a file name inside the run folder."""

    name: str
    file: str


@dataclass(frozen=True)
class Candidates:
    """Options that exist only in data: the values of `key` in the rows of a source, or of a stage's result."""

    source: str
    key: str


@dataclass(frozen=True)
class Sketch:
    """One sketch file, read and shaped; `machine` and `data` stay as written until a stage uses them."""

    path: Path
    name: str
    description: str
    sources: dict[str, Source]
    sinks: dict[str, Sink]
    outcomes: dict[str, tuple[str, ...]]
    data: dict
    machine: dict
    candidates: dict[str, Candidates] = field(default_factory=dict)  # outcomes whose options come from rows
    variables: dict[str, str] = field(default_factory=dict)  # the `--input` values the file was rendered with
    uses: frozenset[str] = frozenset()  # the template variables this file uses
