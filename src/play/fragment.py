"""Compute one stage of a sketch on its own (ADR-0060).

A rule of a sketch (a stage and the stages it reads) can be tested without running the sketch: no machine, no sinks, no run
folder to publish. A `Fragment` takes a loaded sketch and gives the rows of any of its sources, reading a file source from
its file as a run does, or from `stubs`, rows the test wrote. A stub also stands in for any stage source, so the stages
behind it (the per-merchant Jev sketches, say) are never run. Several reads in one `Fragment` share what was computed, and
what Jev was asked. Whole-sketch runs are kept for what only a whole run shows.
"""

import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path

from src.play.model import Play
from src.play.registry import StageFn
from src.play.registry import library as registered
from src.play.run import EventedRecord, stage_computer
from src.play.sources.capture import CaptureStore
from src.play.sources.reader import Capture, Sources


def _silent(line: str) -> None:
    """A fragment says nothing on the console."""


class Fragment:
    """One session over a loaded sketch: `with Fragment(sketch, stubs=...) as session: rows = await session.read(name)`.

    `stubs` (source name to rows) stand in for the sources they name. A stage that notes a figure in the run's summary puts
    it in `summary` when one is given; what the sources say as they are read (an optional file that is missing) goes to
    `announce`. A name that is not a source of the sketch (a stub's, or one read) is a `KeyError` naming it. The work happens
    in a temporary folder that is gone when the session ends. A source that asks Jev uses `jev` (a scripted double in
    tests); with none, it is an error, so stub it."""

    def __init__(  # noqa: PLR0913 - what a fragment takes: the sketch and the few things a test stands in for
        self, sketch: Play, *, stubs: Mapping[str, list[dict]] | None = None, summary: dict | None = None,
        library: Mapping[str, StageFn] | None = None, jev=None, announce: Callable[[str], None] = _silent,
    ):
        self.sketch = sketch
        self.summary = summary if summary is not None else {}
        self._temporary = tempfile.TemporaryDirectory()
        try:
            directory = Path(self._temporary.name)
            self.sources = Sources(Capture.live(CaptureStore(directory / "cache"), jev), directory.name, announce)
            record = EventedRecord(directory, _silent)  # a stage source may emit events; they go to the temporary folder
            for stub, rows in (stubs or {}).items():
                self.sources.provide(sketch, stub, rows)
            self.sources.compute = stage_computer(
                registered() if library is None else library, record, {}, directory, self.summary, self.sources)
        except BaseException:
            self._temporary.cleanup()  # a session that could not start leaves nothing behind
            raise

    def __enter__(self) -> "Fragment":
        return self

    def __exit__(self, *_exc) -> None:
        self._temporary.cleanup()

    async def read(self, name: str) -> list[dict]:
        """The rows of source `name`, computed on first read and kept for the next."""
        if name not in self.sketch.sources:
            raise KeyError(f"{self.sketch.name} has no source {name!r}")
        return await self.sources.read(self.sketch, name)


async def read_stage(sketch: Play, name: str, **options) -> list[dict]:
    """The rows of source `name` of `sketch` in a session of its own; `options` are `Fragment`'s."""
    with Fragment(sketch, **options) as session:
        return await session.read(name)
