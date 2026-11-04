"""Compute one stage of a sketch on its own (ADR-0060).

A rule of a sketch (a stage and the stages it reads) can be tested without running the sketch: no machine, no sinks, no run
folder to publish, no Jev. `read_stage` loads nothing itself; it takes a loaded sketch and returns the rows of one of its
sources, reading a file source from its file as a run does, or from `stubs`, rows the test wrote. A stub also stands in
for any stage source, so the stages behind it (the per-merchant Jev sketches, say) are never run. Whole-sketch runs are
kept for what only a whole run shows.
"""

import tempfile
from collections.abc import Mapping
from pathlib import Path

from src.sketch.model import Sketch
from src.sketch.registry import StageFn
from src.sketch.registry import library as registered
from src.sketch.run import EventedRecord, stage_computer
from src.sketch.sources.capture import CaptureStore
from src.sketch.sources.reader import Capture, Sources


def _silent(line: str) -> None:
    """A fragment says nothing on the console."""


async def read_stage(
    sketch: Sketch, name: str, *, stubs: Mapping[str, list[dict]] | None = None, summary: dict | None = None,
    library: Mapping[str, StageFn] | None = None,
) -> list[dict]:
    """The rows of source `name` of `sketch`, with `stubs` (source name to rows) standing in for the sources they name.

    A stage that notes a figure in the run's summary puts it in `summary` when one is given. A name that is not a
    source of the sketch (the one asked for, or a stub's) is a `KeyError` naming it. The work happens in a temporary
    folder that is gone when the call returns; a stage that calls Jev has no Jev here, so stub it."""
    if name not in sketch.sources:
        raise KeyError(f"{sketch.name} has no source {name!r}")
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        sources = Sources(Capture.live(CaptureStore(directory / "cache"), None), directory.name, _silent)
        record = EventedRecord(directory, _silent)  # a stage source may emit events; they go to the temporary folder
        for stub, rows in (stubs or {}).items():
            sources.provide(sketch, stub, rows)
        sources.compute = stage_computer(
            registered() if library is None else library, record, {}, directory, summary if summary is not None else {}, sources)
        return await sources.read(sketch, name)
