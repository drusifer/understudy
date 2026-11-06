"""Holding a run between its stages (ADR-0058).

The console and the runner share one small file in the run's folder, `control.json`: `{"mode": "run" | "hold", "steps": n}`.
The console writes it (atomically); the runner reads it before each stage. In `hold` the runner waits before the next
stage, saying `paused`; each step the console adds to `steps` lets exactly one stage through (`resumed`), and `run` lets
everything through. A file that is missing, too big or not what is described here means `run`, so a bad file never
wedges a run. A stage already running is never interrupted.

A run can also be held before one named beat (`stop_at`, UND-112): it goes at full speed until it reaches that beat and
waits there as if held. The runner never writes the file: the console's next pause, step or resume writes it without
`stop_at`, which is how the beat is spent.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

CONTROL = "control.json"
MAX_BYTES = 1024
MAX_BEAT = 200  # characters in the name of a beat to hold before
POLL = 0.2  # seconds between looks at the file while held
RUN = {"mode": "run", "steps": 0}


def read_control(directory: Path) -> dict:
    """The control in `directory`, or `run` when there is none or it is not valid."""
    try:
        path = Path(directory) / CONTROL
        if path.stat().st_size > MAX_BYTES:
            return dict(RUN)
        found = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(RUN)
    return _valid(found) or dict(RUN)


def _valid(found) -> dict | None:
    """The control `found` says, or None when it is not one: a mode, a count of steps, and perhaps a beat to hold before."""
    if not isinstance(found, dict):
        return None
    steps, stop = found.get("steps"), found.get("stop_at")
    if found.get("mode") not in ("run", "hold") or not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
        return None
    if "stop_at" in found and not (isinstance(stop, str) and 0 < len(stop) <= MAX_BEAT):
        return None
    return {"mode": found["mode"], "steps": steps, **({"stop_at": stop} if "stop_at" in found else {})}


def write_control(directory: Path, mode: str, steps: int, stop_at: str | None = None) -> None:
    """Replace the control in `directory` in one move, so the runner never reads half of it. `stop_at` names a beat the
    run holds before, whatever its mode; the next write (a pause, step or resume) leaves it out, which spends it."""
    if mode not in ("run", "hold") or steps < 0 or (stop_at is not None and not 0 < len(stop_at) <= MAX_BEAT):
        raise ValueError(f"not a control: {mode!r}, {steps!r}, {stop_at!r}")
    directory = Path(directory)
    temporary = directory / f"{CONTROL}.tmp"
    temporary.write_text(json.dumps({"mode": mode, "steps": steps, **({"stop_at": stop_at} if stop_at else {})}), encoding="utf-8")
    temporary.replace(directory / CONTROL)


class Hold:
    """The runner's gate: `await hold.before(stage)` returns when the stage may start."""

    def __init__(self, directory: Path, emit: Callable[..., None], sleep: Callable[[float], Awaitable] = asyncio.sleep):
        self.directory, self.emit, self.sleep = Path(directory), emit, sleep
        self.taken = 0  # steps this run has used

    async def before(self, stage: str) -> None:
        announced = False
        while True:
            control = read_control(self.directory)
            if control["mode"] == "run" and control.get("stop_at") != stage:
                break
            if control["steps"] > self.taken:
                self.taken += 1
                break
            if not announced:
                self.emit("paused", beat=stage)
                announced = True
            await self.sleep(POLL)
        if announced:
            self.emit("resumed", beat=stage)
