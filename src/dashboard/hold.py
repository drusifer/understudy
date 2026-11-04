"""Holding, stepping and resuming a run from the console (ADR-0058).

The console never talks to a run's process: it writes the run's `control.json` and the runner reads it before its next
stage. Only a run folder directly under the runs root, whose id has the shape of a run id, is ever written to.
"""

from pathlib import Path

from src.dashboard.runs import Refused
from src.dashboard.view import RUN_ID, read_events
from src.sketch.control import read_control, write_control

ACTIONS = ("pause", "step", "resume")
GONE = "that run was not started by this console, or it has finished"


def apply_hold(root: Path, run_id: str, action: str) -> dict:
    """Do `action` (pause, step or resume) to the run `run_id` under `root`, and say what the control is now."""
    if action not in ACTIONS:
        raise Refused(400, f"{action!r} is not one of {', '.join(ACTIONS)}")
    root = Path(root).resolve()
    folder = (root / run_id).resolve() if RUN_ID.fullmatch(run_id) else None
    if folder is None or folder.parent != root or not folder.is_dir():
        raise Refused(404, GONE)
    if any(each.get("event") == "run_finished" for each in read_events(folder)):
        raise Refused(409, "that run has finished")
    steps = read_control(folder)["steps"]
    if action == "step":
        steps += 1
    mode = "run" if action == "resume" else "hold"
    write_control(folder, mode, steps)
    return {"run": run_id, "mode": mode, "steps": steps}
