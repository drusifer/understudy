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
