"""Holding a run between its stages (ADR-0058).

The console and the runner share one small file in the run's folder, `control.json`: `{"mode": "run" | "hold", "steps": n}`.
The console writes it (atomically); the runner reads it before each stage. In `hold` the runner waits before the next
stage, saying `paused`; each step the console adds to `steps` lets exactly one stage through (`resumed`), and `run` lets
everything through. A file that is missing, too big or not what is described here means `run`, so a bad file never
wedges a run. A stage already running is never interrupted.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

CONTROL = "control.json"
MAX_BYTES = 1024
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
    if not isinstance(found, dict):
        return dict(RUN)
    steps = found.get("steps")
    if found.get("mode") not in ("run", "hold") or not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
        return dict(RUN)
    return {"mode": found["mode"], "steps": steps}


def write_control(directory: Path, mode: str, steps: int) -> None:
    """Replace the control in `directory` in one move, so the runner never reads half of it."""
    if mode not in ("run", "hold") or steps < 0:
        raise ValueError(f"not a control: {mode!r}, {steps!r}")
    directory = Path(directory)
    temporary = directory / f"{CONTROL}.tmp"
    temporary.write_text(json.dumps({"mode": mode, "steps": steps}), encoding="utf-8")
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
            if control["mode"] == "run":
                break
            if control["steps"] > self.taken:
                self.taken += 1
                break
            if not announced:
                self.emit("paused", stage=stage)
                announced = True
            await self.sleep(POLL)
        if announced:
            self.emit("resumed", stage=stage)
