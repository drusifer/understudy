"""A finished run's story played back: the run as it was after event N, from `events.jsonl` alone (ADR-0059).

Everything is worked out with the live view's own functions (the stages, the gauges, the printed lines, the diagram's
lit state), applied to the first N events, so a replay and a live page can never disagree about what a run did. The page
only asks for a position and draws the answer.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.dashboard.chart import overlay
from src.dashboard.runs import Refused
from src.dashboard.view import (
    RUN_STATES,
    _ended,
    _failure_of,
    _seconds,
    gauges_of,
    printed,
    read_json,
    stage_tree,
)

UNREADABLE = 422
UNKNOWN = "-"  # a figure that is only known when the run ends


def read_log(directory: Path) -> list[dict]:
    """Every event of the run, or a `Refused` naming the first line that cannot be read (a replay needs the whole story,
    unlike the live view, which leaves a half-written last line for the next read)."""
    try:
        text = (directory / "events.jsonl").read_text(encoding="utf-8")
    except OSError:
        text = ""
    events = []
    for number, line in enumerate(text.splitlines(), 1):
        try:
            found = json.loads(line)
        except ValueError:
            found = None
        if not isinstance(found, dict):
            raise Refused(UNREADABLE, f"events.jsonl line {number} is not readable")
        events.append(found)
    if not events:
        raise Refused(UNREADABLE, "this run has no events to replay")
    return events


def _state_at(prefix: list[dict], run: dict, at: int, total: int) -> str:
    """What the run was doing after these events: running, paused, failed, stopped or done."""
    kinds = [each.get("event") for each in prefix]
    if "run_finished" in kinds:
        return "done"
    if kinds and kinds[-1] == "stage_failed":
        return "failed"
    if at == total:
        final = RUN_STATES.get(run.get("status", "running"), "running")
        if final != "running":
            return final
    return "paused" if kinds and kinds[-1] == "paused" else "running"


def replay(directory: Path, at: int | None = None) -> dict:
    """The number of events in the run (no `at`), or the run as it was after the first `at` of them."""
    events = read_log(directory)
    if at is None:
        return {"id": directory.name, "events": len(events)}
    if not 0 <= at <= len(events):
        raise Refused(400, f"position {at} is outside the run's {len(events)} events")
    prefix = events[:at]
    run, summary = read_json(directory / "run.json"), read_json(directory / "summary.json")
    started = next((each for each in prefix if each.get("event") == "run_started"), {})
    state = _state_at(prefix, run, at, len(events))
    held = {"stage": prefix[-1].get("stage", "?")} if state == "paused" else None
    failure = _failure_of(run, prefix) if state == "failed" else None
    last_at = prefix[-1].get("at") if prefix else None
    ended = f"paused before {held['stage']}" if held else _ended(state, run, failure, last_at, datetime.now(UTC))
    tube = stage_tree(prefix)
    gauges = gauges_of(summary if at == len(events) else {}, prefix, tube)
    if at < len(events):
        for gauge in gauges:
            if gauge["name"] == "JEV":
                gauge["text"], gauge["about"] = UNKNOWN, "known when the run ends"
    return {
        "id": directory.name, "at": at, "of": len(events), "state": state, "ended": ended, "hold": held, "failure": failure,
        "chart": overlay(started, prefix, state, ended) if "states" in started else None,
        "tube": tube, "gauges": gauges, "lines": [printed(each) for each in prefix], "seconds": round(_seconds(prefix)),
    }
