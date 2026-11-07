"""Read a source for one run: a file, or Jev (live, or replayed from a capture)."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.jev import GatedJev, JevError
from src.play.loader import children, source_children
from src.play.model import Play
from src.play.sources import jev as jev_source
from src.play.sources.capture import CaptureStore, choose_replay, read_capture
from src.play.sources.file import read_rows

NAME_CHARS = 60  # the most of a level's name the log keeps
MAX_LEVELS = 8  # the most levels of one Jev answer the log keeps


def capture_key(sketch: Play, name: str) -> str:
    return f"{sketch.name}.{name}"


def jev_keys(sketch: Play) -> list[str]:
    """Capture keys of every Jev source in the sketch and, recursively, the sketches it calls.

    Files and stage sources are deterministic, so only Jev is captured. A sketch repeated by `each` is left out: its
    keys are named per row, and only the rows know them.
    """
    keys = [capture_key(sketch, n) for n, s in sketch.sources.items() if s.kind == "jev"]
    for name, child in children(sketch).items():
        if "each" not in sketch.machine["states"][name]:
            keys += jev_keys(child)
    return keys


def needs_jev(sketch: Play) -> bool:
    """Whether a live run of the sketch, or of the sketches it calls (from a state or from a stage source), has a Jev source."""
    return bool(jev_keys(sketch)) or any(needs_jev(child) for child in [*children(sketch).values(), *source_children(sketch)])


@dataclass(frozen=True)
class Capture:
    """How a run reads its non-file sources: live (with Jev, capturing) or from a replay folder."""

    store: CaptureStore
    jev: object | None = None
    replay_dir: Path | None = None

    @property
    def mode(self) -> str:
        return "replay" if self.replay_dir else "live"

    @classmethod
    def live(cls, store: CaptureStore, jev=None) -> "Capture":
        return cls(store, jev)

    @classmethod
    def replay(cls, store: CaptureStore, sketch: Play, target: str | None) -> "Capture":
        return cls(store, None, choose_replay(store, target, jev_keys(sketch)))


class Sources:
    """The sources of one run. `read` returns a source's rows; a Jev source is asked once and then remembered."""

    def __init__(self, capture: Capture, run_id: str, announce: Callable[[str], None] = print):
        self.capture, self.run_id, self.announce = capture, run_id, announce
        self.jev = GatedJev(capture.jev) if capture.jev is not None else None
        self.stale = False
        self.emit: Callable[..., None] = lambda *_, **__: None  # replaced by the run: tells the run's log what Jev answered
        self._read: dict[str, list[dict]] = {}
        self._computing: set[str] = set()
        self.compute = self._cannot_compute  # replaced by the run, which holds the stage library

    @staticmethod
    async def _cannot_compute(sketch: Play, name: str) -> list[dict]:  # noqa: ARG004 - the signature the run's `compute` has
        raise LookupError(f"source {name!r} is computed by a stage, but this run has no stages")

    @property
    def jev_requests(self) -> int:
        return self.jev.requests if self.jev else 0

    def provide(self, sketch: Play, name: str, rows: list[dict]) -> None:
        """Stand in for source `name` of `sketch`: reading it gives `rows`, whatever kind of source it is (a test of one
        stage uses this to skip a file, or the stages and Jev reads behind it)."""
        if name not in sketch.sources:
            raise KeyError(f"{sketch.name} has no source {name!r}")
        self._read[capture_key(sketch, name)] = list(rows)

    async def read(self, sketch: Play, name: str) -> list[dict]:
        key = capture_key(sketch, name)
        if key not in self._read:
            source = sketch.sources[name]
            if source.kind == "file":
                if source.config.get("optional") and name not in sketch.variables and not source.path.is_file():
                    self.announce(f"no {name}: {source.path} does not exist, so none are used")
                    self._read[key] = []
                else:
                    self._read[key] = read_rows(source.path)
            elif source.kind == "stage":
                self._read[key] = await self._compute(sketch, name, key)
            else:
                self._read[key] = await self._read_jev(sketch, name, key)
        return self._read[key]

    async def _compute(self, sketch: Play, name: str, key: str) -> list[dict]:
        """A stage source: run its stage once, on first read. The run installs `compute` (it holds the library)."""
        if key in self._computing:
            raise ValueError(f"source {name!r} reads itself, directly or through another source")
        self._computing.add(key)
        try:
            return await self.compute(sketch, name)
        finally:
            self._computing.discard(key)

    async def _state(self, sketch: Play, config: dict) -> dict:
        return {key: await self.read(sketch, ref["from"]) for key, ref in config["state"].items()}

    async def _options(self, sketch: Play, config: dict) -> dict:
        """A Jev source whose `options` come from a source chooses among the values of `key` in its rows (each option is
        its own meaning); a source with `criteria` is returned as it is."""
        if "options" not in config:
            return config
        found = config["options"]
        rows = await self.read(sketch, found["from"])
        return {**config, "criteria": {option: option for option in dict.fromkeys(str(row[found["key"]]) for row in rows)}}

    async def _read_jev(self, sketch: Play, name: str, key: str) -> list[dict]:
        config = await self._options(sketch, sketch.sources[name].config)
        asked = jev_source.request(config, await self._state(sketch, config))
        digest = jev_source.request_hash(asked)
        if self.capture.replay_dir:
            rows, meta = read_capture(self.capture.replay_dir, key)
            if meta["request_hash"] != digest:
                self.stale = True
                self.announce(f"replay of {key} is stale: the sketch or its rubric changed since it was captured")
            self._told(key, rows)
            return rows
        if self.jev is None:
            raise JevError(f"{key} needs Jev, and this run has none")
        rows = await jev_source.read_live(self.jev, config, asked["state"])
        self.capture.store.write(self.run_id, key, rows, digest, config["instructions"],
                                 levels_from_data="options" in sketch.sources[name].config)
        self._told(key, rows)
        return rows

    def _told(self, key: str, rows: list[dict]) -> None:
        """Tell the run's log what Jev answered: the likeliest level and the one after it, and how many it chose among."""
        ranked = sorted(rows, key=lambda row: row["probability"], reverse=True)
        if not ranked:
            return
        after = ranked[1] if len(ranked) > 1 else None
        self.emit("jev_read", source=key, top=str(ranked[0]["level"])[:NAME_CHARS], probability=round(ranked[0]["probability"], 2),
                  next=str(after["level"])[:NAME_CHARS] if after else None,
                  next_probability=round(after["probability"], 2) if after else None, options=len(ranked),
                  levels=[[str(row["level"])[:NAME_CHARS], round(row["probability"], 2)] for row in ranked[:MAX_LEVELS]])
