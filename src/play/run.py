"""One run of a sketch: its folder, its stages, its outputs (published last).

    .understudy/runs/run-<stamp>-<id>/   run.json  events.jsonl  summary.json  <sink files>

A sink stage writes `<file>.part`; only when the machine reaches a final state are the parts renamed, so a
failed run publishes nothing. Failed runs keep earlier stage files and `run.json` saying where they stopped.
"""

import json
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

from src.machine_runner import RunRecord, run_machine
from src.paths import ROOT, check_writable
from src.play.control import Hold, write_control
from src.play.loader import bound_pieces, child_path, children, load, read_template
from src.play.machine import build_machine
from src.play.model import Play
from src.play.plan import plan
from src.play.registry import StageFn
from src.play.sources.capture import CaptureStore
from src.play.sources.reader import Capture, Sources
from src.play.vocabulary import NOTHING, stage_of


@dataclass
class StageContext:
    """What a stage gets: the sketch, its own state as written, what earlier stages returned, the run folder."""

    sketch: Play
    name: str
    state: dict
    results: dict
    last: object
    directory: Path
    summary: dict = field(default_factory=dict)
    sources: Sources | None = None
    emit: Callable[..., None] | None = None  # records an event in the run's story (`events.jsonl`)

    async def read(self, name: str) -> list[dict]:
        """The rows of one of this sketch's sources."""
        return await self.sources.read(self.sketch, name)


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

    def entered(self, state: str, caused_by: str) -> None:
        self.emit("beat_entered", beat=state, caused_by=caused_by)

    def started(self, name: str) -> None:
        super().started(name)
        self.emit("beat_started", beat=name)

    def completed(self, name: str) -> None:
        super().completed(name)
        self.emit("beat_completed", beat=name)

    def failed(self, name: str, error: Exception) -> None:
        super().failed(name, error)
        self.emit("beat_failed", beat=name, reason=str(error))

    def finished(self, outcome: str | None = None) -> None:
        super().finished(outcome)
        self.emit("run_finished", outcome=outcome or "complete")


def _check_rows(rows) -> None:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TypeError(f"a write writes rows, not {type(rows).__name__}")


def _write_part(directory: Path, file: str, rows) -> None:
    _check_rows(rows)
    lines = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    (directory / f"{file}.part").write_text(lines, encoding="utf-8")


def _stage_function(state: dict, library: Mapping[str, StageFn]) -> StageFn:
    name = ".".join(stage_of(state))
    if name in library:
        return library[name]
    raise LookupError(f"no stage is defined for {name!r}")


class NestedRecord:
    """A subsketch's stages, reported through the parent's record so the one run.json stays the parent's."""

    def __init__(self, parent: EventedRecord, prefix: str):
        self.parent, self.prefix = parent, prefix
        self.outcome: str | None = None

    def entered(self, state: str, caused_by: str) -> None:
        """A subsketch's moves are not told: the parent's story is the top-level machine's."""

    def started(self, name: str) -> None:
        self.parent.started(f"{self.prefix}.{name}")

    def completed(self, name: str) -> None:
        self.parent.emit("beat_completed", beat=f"{self.prefix}.{name}")

    def failed(self, name: str, error: Exception) -> None:
        self.parent.emit("beat_failed", beat=f"{self.prefix}.{name}", reason=str(error))

    def finished(self, outcome: str | None = None) -> None:
        """The parent's run is not over because a subsketch ended; the subsketch's outcome is kept for its caller."""
        self.outcome = outcome


async def _run_each(context: StageContext, library: Mapping[str, StageFn], record: EventedRecord) -> list[dict]:
    """Perform the play this beat calls once per row of the piece named by `each`.

    The row's fields are the play's props, beside the call's `with`. The result is every row the play wrote, each
    carrying the fields of the row it was played for (a merchant's key, say). A row's Jev answers are captured under the
    play's name and the row's position, so each film (say) is asked and replayed on its own.

    With `reduce: { action: concat, into: <name> }` the iterations run in order as a fold instead: the rows each one
    writes are appended to a running list, which the next one receives as the prop `<name>` (empty to begin with), and
    the result is that list.
    """
    state = context.state
    path = child_path(context.sketch, stage_of(state)[1])
    folding = state.get("reduce")
    carried, running = [], []
    for index, row in enumerate(await context.read(state["each"])):
        values = {**state.get("with", {}), **row, **({folding["into"]: list(running)} if folding else {})}
        child = replace(load(path, variables=values), name=f"{context.name}.{path.stem}[{index}]")
        output = await _run_child(context, library, record, child)
        running += output
        carried += [{**row, **written} for written in output]
    return running if folding else carried


async def _run_child(context: StageContext, library: Mapping[str, StageFn], record: EventedRecord, child: Play | None = None):
    """Perform the play this beat calls (`do: { play: <file>.yaml }`) inside this run.

    The call's `with:` binds the play's stage: a prop gets a value, and a stage file named there gets the rows of the
    caller's piece it names. The play touches no disk: its result is the rows it wrote, or no rows when it ended in a
    final beat with `outcome: none` (a play that finds nothing gives its caller nothing).
    """
    child = child or children(context.sketch)[context.name]
    for name, piece in bound_pieces(context.sketch, child, context.state.get("with", {})).items():
        context.sources.provide(child, name, await context.read(piece))
    results: dict = {}
    last = {"value": None}
    written: dict[str, list[dict]] = {}

    def make_context(name: str, state: dict) -> StageContext:
        return StageContext(child, name, state, results, last["value"], context.directory, context.summary, context.sources,
                            context.emit)

    stages = _stages(child, library, make_context, results, record, written)
    stages = {name: _remember(stage, last) for name, stage in stages.items()}
    nested = NestedRecord(record, child.name)
    outcomes = {name: state["outcome"] for name, state in child.machine["states"].items() if state.get("outcome")}
    await run_machine(build_machine(child), stages, nested, outcomes=outcomes)
    return [] if nested.outcome == NOTHING else [row for rows in written.values() for row in rows]


def _stages(  # noqa: PLR0913 - a beat needs the play, the library, its context, the results, the record, where writes go
    sketch: Play, library: Mapping[str, StageFn], make_context: Callable[[str, dict], StageContext], results: dict,
    record: EventedRecord, written: dict[str, list[dict]] | None = None,
):
    """The flow beats as the machine calls them. `written` collects what a called play writes instead of the disk."""
    stages = {}
    for name, state in sketch.machine["states"].items():
        if state.get("final"):
            continue

        async def stage(name=name, state=state):
            context = make_context(name, state)
            kind, target = stage_of(state)
            if kind == "sink":
                named = state.get("with", {}).get("source")
                rows = await context.read(named) if named else context.last
                if written is None:
                    _write_part(context.directory, sketch.sinks[target].file, rows)
                else:
                    _check_rows(rows)
                    written.setdefault(target, []).extend(rows)
                return rows
            if kind == "sketch":
                run = _run_each if "each" in state else _run_child
                result = await run(context, library, record)
            else:
                result = await _stage_function(state, library)(context, **state.get("with", {}))
            results[name] = result
            return result

        stages[name] = stage
    return stages


def stage_computer(  # noqa: PLR0913 - what a stage source's stage runs against: the library, the record, the run's state
    library: Mapping[str, StageFn], record: EventedRecord, results: dict, directory: Path, summary: dict, sources: Sources,
) -> Callable[[Play, str], Awaitable[list[dict]]]:
    """The function a run gives its `Sources` to compute a stage source (`kind: stage`): the source's `do` and `with`, as
    a state would have them. A run and the fragment harness (`fragment.py`) both use it."""
    async def compute(owner: Play, name: str) -> list[dict]:
        config = owner.sources[name].config
        state = {key: config[key] for key in ("do", "with", "each", "reduce") if key in config}
        state.setdefault("with", {})
        context = StageContext(owner, name, state, results, None, directory, summary, sources, record.emit)
        if "each" in state:
            return await _run_each(context, library, record)
        return await _stage_function(state, library)(context, **state["with"])

    return compute


async def run_sketch(  # noqa: PLR0913 - what a run takes: the sketch, where, its stages, how to announce, capture, pause
    sketch: Play, out: Path, library: Mapping[str, StageFn], announce: Callable[[str], None] = print,
    capture: Capture | None = None, pause: bool = False, on_start: Callable[[Path], None] | None = None,
    stop_at: str | None = None,
) -> RunResult:
    """Run the sketch's machine. Raises whatever a stage raises, after recording the failure. With `pause` the run
    starts held before its first stage, and with `stop_at` it runs up to that beat and holds before it (see `control.py`);
    `on_start` is told the run's folder as soon as it exists."""
    capture = capture or Capture.live(CaptureStore())
    out = Path(out).resolve()
    check_writable(out)
    directory = out / f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    directory.mkdir(parents=True)
    if pause:
        write_control(directory, "hold", 0)
    elif stop_at:
        write_control(directory, "run", 0, stop_at)
    if on_start:
        on_start(directory)
    files = [f for sink in sketch.sinks.values() for f in (sink.file, f"{sink.file}.part")]
    facts = {"with": dict(sketch.variables)}
    if capture.replay_dir:
        facts["replay_of"] = _shown_path(capture.replay_dir)
    record = EventedRecord(directory, announce, cleanup=[*files, "summary.json"], mode=capture.mode, play=sketch.name, **facts)
    record.emit("run_started", play=_shown_path(sketch.path), mode=capture.mode, **({"stop_at": stop_at} if stop_at else {}),
                **_story_of(sketch))
    if capture.replay_dir:
        announce(f"replay: reading captures from {capture.replay_dir}, no live calls")
    sources = Sources(capture, directory.name, announce)
    results: dict = {}
    summary: dict = {}
    last = {"value": None}

    def make_context(name: str, state: dict) -> StageContext:
        return StageContext(sketch, name, state, results, last["value"], directory, summary, sources, record.emit)

    sources.compute = stage_computer(library, record, results, directory, summary, sources)
    stages = _stages(sketch, library, make_context, results, record)
    machine = build_machine(sketch)
    inner = {name: _remember(stage, last) for name, stage in stages.items()}
    published: dict[str, Path] = {}

    def publish() -> None:
        facts = {"mode": capture.mode, "stale": sources.stale, "jev_requests": sources.jev_requests, **summary}
        published.update(_publish(directory, sketch, facts))
        record.manifest["outputs"] = {path.name: _row_count(path) for path in published.values()}

    outcomes = {name: state["outcome"] for name, state in sketch.machine["states"].items() if state.get("outcome")}
    await run_machine(machine, inner, record, publish=publish, outcomes=outcomes, before=Hold(directory, record.emit).before)
    if capture.mode == "live":
        capture.store.prune()
    return RunResult(directory, published, summary, record.manifest.get("outcome"))


def _story_of(sketch: Play) -> dict:
    """The play as the first line of the event stream tells it: its plan (the stage's pieces, the beats, who reads what, and
    the moves between beats), as the file was when the run began."""
    return {"plan": plan(read_template(sketch.path)[0])}


def _shown_path(path: Path) -> str:
    """The sketch's path as a run records it: relative to the project when inside it, else just the file name (SEC-004)."""
    resolved = Path(path).resolve()
    return resolved.relative_to(ROOT).as_posix() if resolved.is_relative_to(ROOT) else resolved.name


def _row_count(path: Path) -> int:
    """Lines in an output file: one JSON record per line."""
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def _remember(stage, last: dict):
    async def remembered():
        last["value"] = await stage()
        return last["value"]
    return remembered


def _publish(directory: Path, sketch: Play, summary: dict) -> dict[str, Path]:
    (directory / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    published = {}
    for name, sink in sketch.sinks.items():
        part = directory / f"{sink.file}.part"
        if part.exists():
            part.replace(directory / sink.file)
            published[name] = directory / sink.file
    return published
