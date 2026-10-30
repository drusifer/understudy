"""One run of a sketch: its folder, its stages, its outputs (published last).

    build/runs/run-<stamp>-<id>/   run.json  events.jsonl  summary.json  <sink files>

A sink stage writes `<file>.part`; only when the machine reaches a final state are the parts renamed, so a
failed run publishes nothing. Failed runs keep earlier stage files and `run.json` saying where they stopped.
"""

import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from src.machine_runner import RunRecord, run_machine
from src.paths import check_writable
from src.sketch.loader import children
from src.sketch.machine import build_machine
from src.sketch.model import Sketch
from src.sketch.sources.capture import CaptureStore
from src.sketch.sources.reader import Capture, Sources
from src.sketch.stages import StageFn
from src.sketch.vocabulary import SINK_PREFIX, SKETCH_PREFIX


@dataclass
class StageContext:
    """What a stage gets: the sketch, its own state as written, what earlier stages returned, the run folder."""

    sketch: Sketch
    name: str
    state: dict
    results: dict
    last: object
    directory: Path
    summary: dict = field(default_factory=dict)
    sources: Sources | None = None

    async def read(self, name: str) -> list[dict]:
        """The rows of one of this sketch's sources."""
        return await self.sources.read(self.sketch, name)


@dataclass(frozen=True)
class RunResult:
    directory: Path
    outputs: dict[str, Path]
    summary: dict


class EventedRecord(RunRecord):
    """The run record, plus `events.jsonl`: one JSON line per run event (the later dashboard reads it)."""

    def emit(self, kind: str, **fields) -> None:
        line = {"event": kind, "at": datetime.now(UTC).isoformat(timespec="seconds"), **fields}
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as events:
            events.write(json.dumps(line) + "\n")

    def started(self, name: str) -> None:
        super().started(name)
        self.emit("stage_started", stage=name)

    def completed(self, name: str) -> None:
        super().completed(name)
        self.emit("stage_completed", stage=name)

    def failed(self, name: str, error: Exception) -> None:
        super().failed(name, error)
        self.emit("stage_failed", stage=name, reason=str(error))

    def finished(self) -> None:
        super().finished()
        self.emit("run_finished", outcome="complete")


def _write_part(directory: Path, file: str, rows) -> None:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TypeError(f"a sink writes the rows of the stage before it, not {type(rows).__name__}")
    lines = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    (directory / f"{file}.part").write_text(lines, encoding="utf-8")


def _stage_function(state: dict, library: Mapping[str, StageFn]) -> StageFn:
    name = "blend" if "blend" in state else state["do"]
    if name in library:
        return library[name]
    raise LookupError(f"no stage is defined for {name!r}")


class NestedRecord:
    """A subsketch's stages, reported through the parent's record so the one run.json stays the parent's."""

    def __init__(self, parent: EventedRecord, prefix: str):
        self.parent, self.prefix = parent, prefix

    def started(self, name: str) -> None:
        self.parent.started(f"{self.prefix}.{name}")

    def completed(self, name: str) -> None:
        self.parent.emit("stage_completed", stage=f"{self.prefix}.{name}")

    def failed(self, name: str, error: Exception) -> None:
        self.parent.emit("stage_failed", stage=f"{self.prefix}.{name}", reason=str(error))

    def finished(self) -> None:
        """The parent's run is not over because a subsketch ended."""


async def _run_child(context: StageContext, library: Mapping[str, StageFn], record: EventedRecord):
    """Run the sketch this stage calls (`do: sketch.<file>`) in the same run folder, with the same sources.

    Its result is what its last stage returned: the decider's rows the parent blends.
    """
    child = children(context.sketch)[context.state["do"].removeprefix(SKETCH_PREFIX)]
    results: dict = {}
    last = {"value": None}

    def make_context(name: str, state: dict) -> StageContext:
        return StageContext(child, name, state, results, last["value"], context.directory, context.summary, context.sources)

    stages = {name: _remember(stage, last) for name, stage in _stages(child, library, make_context, results, record).items()}
    await run_machine(build_machine(child), stages, NestedRecord(record, child.name))
    return last["value"]


def _stages(
    sketch: Sketch, library: Mapping[str, StageFn], make_context: Callable[[str, dict], StageContext], results: dict,
    record: EventedRecord,
):
    stages = {}
    for name, state in sketch.machine["states"].items():
        if state.get("final"):
            continue

        async def stage(name=name, state=state):
            context = make_context(name, state)
            called = state.get("do", "")
            if called.startswith(SINK_PREFIX):
                file = sketch.sinks[called.removeprefix(SINK_PREFIX)].file
                _write_part(context.directory, file, context.last)
                return context.last
            if called.startswith(SKETCH_PREFIX):
                result = await _run_child(context, library, record)
            else:
                result = await _stage_function(state, library)(context)
            results[name] = result
            return result

        stages[name] = stage
    return stages


async def run_sketch(
    sketch: Sketch, out: Path, library: Mapping[str, StageFn], announce: Callable[[str], None] = print,
    capture: Capture | None = None,
) -> RunResult:
    """Run the sketch's machine. Raises whatever a stage raises, after recording the failure."""
    capture = capture or Capture.live(CaptureStore())
    out = Path(out).resolve()
    check_writable(out)
    directory = out / f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    directory.mkdir(parents=True)
    files = [f for sink in sketch.sinks.values() for f in (sink.file, f"{sink.file}.part")]
    record = EventedRecord(directory, announce, cleanup=[*files, "summary.json"], mode=capture.mode, sketch=sketch.name)
    record.emit("run_started", sketch=str(sketch.path), mode=capture.mode)
    if capture.replay_dir:
        announce(f"replay: reading captures from {capture.replay_dir}, no live calls")
    sources = Sources(capture, directory.name, announce)
    results: dict = {}
    summary: dict = {}
    last = {"value": None}

    def make_context(name: str, state: dict) -> StageContext:
        return StageContext(sketch, name, state, results, last["value"], directory, summary, sources)

    stages = _stages(sketch, library, make_context, results, record)
    machine = build_machine(sketch)
    inner = {name: _remember(stage, last) for name, stage in stages.items()}
    published: dict[str, Path] = {}

    def publish() -> None:
        facts = {"mode": capture.mode, "stale": sources.stale, "jev_requests": sources.jev_requests, **summary}
        published.update(_publish(directory, sketch, facts))

    await run_machine(machine, inner, record, publish=publish)
    if capture.mode == "live":
        capture.store.prune()
    return RunResult(directory, published, summary)


def _remember(stage, last: dict):
    async def remembered():
        last["value"] = await stage()
        return last["value"]
    return remembered


def _publish(directory: Path, sketch: Sketch, summary: dict) -> dict[str, Path]:
    (directory / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    published = {}
    for name, sink in sketch.sinks.items():
        part = directory / f"{sink.file}.part"
        if part.exists():
            part.replace(directory / sink.file)
            published[name] = directory / sink.file
    return published
