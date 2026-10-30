"""One run of a sketch: its folder, its stages, its outputs (published last).

    build/runs/run-<stamp>-<id>/   run.json  events.jsonl  summary.json  <sink files>

A sink stage writes `<file>.part`; only when the machine reaches a final state are the parts renamed, so a
failed run publishes nothing. Failed runs keep earlier stage files and `run.json` saying where they stopped.
"""

import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

from src.machine_runner import RunRecord, run_machine
from src.paths import check_writable
from src.sketch.loader import child_path, children, load
from src.sketch.machine import build_machine
from src.sketch.model import Sketch
from src.sketch.registry import StageFn
from src.sketch.sources.capture import CaptureStore
from src.sketch.sources.reader import Capture, Sources
from src.sketch.vocabulary import stage_of


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
        return await self.sources.read(self.sketch, name, self.results)


@dataclass(frozen=True)
class RunResult:
    directory: Path
    outputs: dict[str, Path]
    summary: dict
    outcome: str | None = None  # the `outcome:` of the final state the machine ended in, if it has one


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

    def finished(self, outcome: str | None = None) -> None:
        super().finished(outcome)
        self.emit("run_finished", outcome=outcome or "complete")


def _write_part(directory: Path, file: str, rows) -> None:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TypeError(f"a sink writes the rows of the stage before it, not {type(rows).__name__}")
    lines = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    (directory / f"{file}.part").write_text(lines, encoding="utf-8")


def _stage_function(state: dict, library: Mapping[str, StageFn]) -> StageFn:
    name = "blend" if "blend" in state else ".".join(stage_of(state))
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

    def finished(self, outcome: str | None = None) -> None:
        """The parent's run is not over because a subsketch ended."""


async def _run_each(context: StageContext, library: Mapping[str, StageFn], record: EventedRecord) -> list[dict]:
    """Run the sketch this stage calls once per row of the source named by `each`.

    The row's fields are the child's variables, beside the call's `with`. The result pairs every row with what its
    run output: `[ { input: <row>, output: <what the child returned> }, ... ]`. A row's Jev answers are captured under
    the child's name and the row's position, so each film (say) is asked and replayed on its own.
    """
    state = context.state
    path = child_path(context.sketch, stage_of(state)[1])
    paired = []
    for index, row in enumerate(await context.read(state["each"])):
        child = replace(load(path, variables={**state.get("with", {}), **row}), name=f"{path.stem}[{index}]")
        paired.append({"input": row, "output": await _run_child(context, library, record, child)})
    return paired


async def _run_child(context: StageContext, library: Mapping[str, StageFn], record: EventedRecord, child: Sketch | None = None):
    """Run the sketch this state calls (`do: { sketch: { file: ... } }`) in the same run folder, with the same sources.

    Its result is what its last stage returned: the weighted rows the parent blends.
    """
    child = child or children(context.sketch)[context.name]
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
            kind, target = stage_of(state) or ("blend", "")
            if kind == "sink":
                _write_part(context.directory, sketch.sinks[target].file, context.last)
                return context.last
            if kind == "sketch":
                run = _run_each if "each" in state else _run_child
                result = await run(context, library, record)
            else:
                result = await _stage_function(state, library)(context, **state.get("with", {}))
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

    async def compute(owner: Sketch, name: str) -> list[dict]:
        """Run a stage source's stage (`kind: stage`): the source's `do` and `with`, as a state would have them."""
        config = owner.sources[name].config
        state = {"do": config["do"], "with": config.get("with", {})}
        context = StageContext(owner, name, state, results, None, directory, summary, sources)
        return await _stage_function(state, library)(context, **state["with"])

    sources.compute = compute
    stages = _stages(sketch, library, make_context, results, record)
    machine = build_machine(sketch)
    inner = {name: _remember(stage, last) for name, stage in stages.items()}
    published: dict[str, Path] = {}

    def publish() -> None:
        facts = {"mode": capture.mode, "stale": sources.stale, "jev_requests": sources.jev_requests, **summary}
        published.update(_publish(directory, sketch, facts))

    outcomes = {name: state["outcome"] for name, state in sketch.machine["states"].items() if state.get("outcome")}
    await run_machine(machine, inner, record, publish=publish, outcomes=outcomes)
    if capture.mode == "live":
        capture.store.prune()
    return RunResult(directory, published, summary, record.manifest.get("outcome"))


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
