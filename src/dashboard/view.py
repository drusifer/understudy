"""What the console shows about a run: everything the page draws is decided here, so unittest covers it.

A run folder holds `run.json`, `summary.json` and `events.jsonl`. This module reads them and answers: the state of the
run, why it failed, the printed lines, the stages and the groups of nested stages, the gauges, the rack entry. It
never writes and it never starts anything. `server.py` serves what it returns; `page.js` only draws it.
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from src.dashboard.chart import overlay
from src.dashboard.spending import read_spending

RUN_ID = re.compile(r"run-[0-9A-Za-z-]+")
DAY = 86400
AGE_UNITS = (("minutes", 60, 2 * 3600), ("hours", 3600, 2 * DAY))  # unit, seconds per unit, age at which the next unit starts
STALL_SECONDS = 600  # a running run with no new event for this long reads as stalled
RUN_STATES = {"complete": "done", "failed": "failed", "stopped": "stopped"}
STAGE_STATES = {"beat_started": "running", "beat_completed": "complete", "beat_failed": "failed"}
TONES = {"beat_failed": "held", "run_finished": "bold", "run_started": "bold"}
TAIL_BYTES = 8192  # how much of the end of `events.jsonl` is read to find the last event


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def read_events(directory: Path) -> list[dict]:
    """The lines of `events.jsonl` so far; a half-written last line is left for the next read."""
    try:
        text = (directory / "events.jsonl").read_text(encoding="utf-8")
    except OSError:
        return []
    events = []
    for line in text.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            break
    return events


def _edge_events(directory: Path) -> tuple[dict, dict]:
    """The first and the last event of a run, reading only the two ends of the file (the rack needs no more)."""
    try:
        with (directory / "events.jsonl").open("rb") as handle:
            first = handle.readline()
            handle.seek(0, 2)
            handle.seek(max(0, handle.tell() - TAIL_BYTES))
            tail = handle.read().splitlines()
    except OSError:
        return {}, {}
    parsed = []
    for raw in (first, *reversed(tail)):
        try:
            parsed.append(json.loads(raw))
        except ValueError:
            parsed.append({})
    return parsed[0], next((each for each in parsed[1:] if each), {})


def printed(event: dict) -> dict:
    """What the printer prints for one event: its text and its tone."""
    kind = event.get("event", "")
    clock = event.get("at", "")[11:19]
    detail = {
        "run_started": lambda: f"=== UNDERSTUDY RUN LOG ===  {event.get('play', '')}  ({event.get('mode', '')})",
        "beat_started": lambda: f"  start  {event.get('beat', '')}",
        "beat_completed": lambda: f"  done   {event.get('beat', '')}",
        "beat_failed": lambda: f"  FAILED {event.get('beat', '')}: {event.get('reason', '')}",
        "run_finished": lambda: f"=== {str(event.get('outcome', '')).upper()} ===",
        "decision": lambda: (f"  decision {event.get('beat', '')}: {event.get('row', '?')} {event.get('dimension', '?')}"
                             f" = {event.get('pick', '?')} ({event.get('probability', '?')})"),
    }.get(kind, lambda: f"  {kind}")()
    return {"text": f"{clock}  {detail}" if clock else detail, "tone": TONES.get(kind, ""), "stage": event.get("beat", ""),
            "event": kind}


def _seconds(events: list[dict]) -> float:
    stamps = [datetime.fromisoformat(event["at"]) for event in events if event.get("at")]
    return (stamps[-1] - stamps[0]).total_seconds() if len(stamps) > 1 else 0.0


def _split_nested(stage: str) -> tuple[str, int | None, str]:
    """`readings.judge_payee[3].decide` is stage `decide`, iteration 3, of group `readings.judge_payee`;
    `weather_change.judge` is stage `judge` of group `weather_change` (no iterations)."""
    if "[" in stage:
        group, _, rest = stage.partition("[")
        number, _, child = rest.partition("].")
        return group, int(number), child
    group, _, child = stage.partition(".")
    return group, None, child


def _group_view(name: str, group: dict) -> dict:
    stages = group["stages"]
    failed = any(each["failed"] for each in stages.values())
    running = any(each["started"] - each["completed"] - each["failed"] > 0 for each in stages.values())
    iterations = group["iterations"]
    return {
        "name": name,
        "state": "failed" if failed else "running" if running else "complete",
        "done": sum(1 for each in iterations.values() if each["started"] == each["completed"]),
        "seen": len(iterations),
        "stages": [{"name": child, "started": each["started"], "completed": each["completed"]} for child, each in stages.items()],
    }


def _count_nested(groups: dict, stage: str, state: str) -> None:
    """Count one start, completion or failure of a nested stage in its group, its stage and its iteration."""
    name, iteration, child = _split_nested(stage)
    group = groups.setdefault(name, {"iterations": {}, "stages": {}})
    counts = group["stages"].setdefault(child, {"started": 0, "completed": 0, "failed": 0})
    counts[{"running": "started", "complete": "completed", "failed": "failed"}[state]] += 1
    if iteration is not None and state != "failed":
        turns = group["iterations"].setdefault(iteration, {"started": 0, "completed": 0})
        turns["started" if state == "running" else "completed"] += 1


def stage_tree(events: list[dict]) -> list[dict]:
    """The stages of a run from its events: each top-level stage with its state and the groups of nested stages that ran
    inside it (a name with a dot is nested; `[n]` marks one iteration of a child sketch)."""
    top: dict[str, dict] = {}
    current: dict | None = None
    for event in events:
        state, stage = STAGE_STATES.get(event.get("event", "")), event.get("beat")
        if not state or not stage:
            continue
        if "." not in stage:
            current = top.setdefault(stage, {"name": stage, "state": state, "groups": {}})
            current["state"] = state
        elif current is not None:
            _count_nested(current["groups"], stage, state)
    return [{"name": each["name"], "state": each["state"], "groups": [_group_view(n, g) for n, g in each["groups"].items()]}
            for each in top.values()]


def gauges_of(summary: dict, events: list[dict], tube: list[dict] | None = None) -> list[dict]:
    """Four gauges from the run's own files. A needle is drawn only when the run knows what full scale is (`level` is a
    fraction of counts it has seen); the Jev requests and the elapsed time have no full scale, so `level` is None."""
    tube = stage_tree(events) if tube is None else tube
    seen = len(tube)
    done = sum(1 for each in tube if each["state"] == "complete")
    failed = sum(1 for each in tube if each["state"] == "failed")
    requests = int(summary.get("jev_requests", 0))
    return [
        {"name": "BEATS", "level": done / seen if seen else 0, "text": f"{done}/{seen}",
         "about": "beats of the scene's flow complete, of those started"},
        {"name": "FAILED", "level": failed / seen if seen else 0, "text": str(failed),
         "about": "beats of the scene's flow that failed, of those started"},
        {"name": "JEV", "level": None, "text": str(requests), "about": "Jev requests this run made"},
        {"name": "ELAPSED", "level": None, "text": f"{_seconds(events):.0f}s", "about": "first event to last"},
    ]


def _state_of(run: dict, last_at: str | None, now: datetime, last_event: str | None = None, first: dict | None = None) -> str:
    """running, paused (held before a beat, however long ago), done, failed, stopped, stalled (a running run silent
    for ten minutes) or unreadable (nothing to read, or a log that does not start by naming its play)."""
    if (not run and not last_at) or (first and first.get("event") == "run_started" and "play" not in first):
        return "unreadable"
    state = RUN_STATES.get(run.get("status", "running"), "running")
    if state == "running" and last_event == "paused":
        return "paused"
    if state == "running" and last_at and (now - datetime.fromisoformat(last_at)).total_seconds() > STALL_SECONDS:
        return "stalled"
    return state


def _failure_of(run: dict, events: list[dict]) -> dict | None:
    """The stage and reason a failed run stopped on, and the index of its printed line."""
    if run.get("status") != "failed":
        return None
    line = next((index for index in range(len(events) - 1, -1, -1) if events[index].get("event") == "beat_failed"), None)
    return {"stage": run.get("failed_beat", "?"), "reason": run.get("error", ""), "line": line}


def _ago(seconds: float) -> str:
    """A length of time in the largest unit that keeps it short: minutes, hours or days."""
    for unit, size, until in AGE_UNITS:
        if seconds < until:
            return f"{int(seconds // size)} {unit}"
    return f"{int(seconds // DAY)} days"


def _ended(state: str, run: dict, failure: dict | None, last_at: str | None, now: datetime) -> str:
    """One line saying how the run ended (empty while it is still going)."""
    if state == "done":
        done = sum(1 for each in run.get("beats", {}).values() if each == "complete")
        outcome = f", outcome {run['outcome']}" if run.get("outcome") else ""
        return f"done after {done} beats{outcome}"
    if state == "failed" and failure:
        return f"failed at {failure['stage']}: {failure['reason']}"
    if state == "stopped":
        return "stopped before it finished"
    if state == "stalled" and last_at:
        return f"no new events for {_ago((now - datetime.fromisoformat(last_at)).total_seconds())}; the run may have died"
    return "no details for this run" if state == "unreadable" else ""


def step_details(events: list[dict]) -> dict[str, dict]:
    """What each completed beat said it read, made and wrote (names, rows and keys; no values), from the log alone. A beat
    logged before the log said so is there with nothing in it."""
    return {each["beat"]: {key: each[key] for key in ("read", "made", "wrote") if key in each}
            for each in events if each.get("event") == "beat_completed" and "beat" in each}


def describe(directory: Path, now: datetime | None = None, view: str = "auto") -> dict:
    """One run as the page draws it; `view` is how much of its plan the diagram shows (`auto`, `flow` or `all`)."""
    now = now or datetime.now(UTC)
    run, summary, events = read_json(directory / "run.json"), read_json(directory / "summary.json"), read_events(directory)
    started = next((each for each in events if each.get("event") == "run_started"), {})
    last_at = events[-1].get("at") if events else None
    state = _state_of(run, last_at, now, events[-1].get("event") if events else None, events[0] if events else {})
    held = {"stage": events[-1].get("beat", "?")} if state == "paused" else None
    failure = _failure_of(run, events)
    tube = stage_tree(events)
    mode = run.get("mode", started.get("mode", ""))
    ended = f"paused before {held['stage']}" if held else _ended(state, run, failure, last_at, now)
    asked = started.get("stop_at")
    if ended and asked and not any(each.get("event") == "paused" and each.get("beat") == asked for each in events):
        ended += f"; never reached {asked}, the beat it was to hold before"
    return {
        "id": directory.name,
        "sketch": Path(started.get("play", run.get("play", "?"))).stem,
        "state": state,
        "ended": ended,
        "hold": held,
        "failure": failure,
        "summary": {
            "outcome": run.get("outcome"), "mode": mode, "stale": summary.get("stale"),
            "seconds": round(_seconds(events)), "with": run.get("with", {}), "outputs": run.get("outputs", {}),
        },
        "mode": mode,
        "story": "plan" in started,
        "chart": overlay(started, events, state, ended, view) if "plan" in started else None,
        "steps": step_details(events),
        "spending": read_spending(directory),
        "tube": tube,
        "gauges": gauges_of(summary, events, tube),
        "lines": [printed(each) for each in events],
        "failures": [index for index, each in enumerate(events) if each.get("event") == "beat_failed"],
        "count": len(events),
    }


def list_runs(root: Path, now: datetime | None = None) -> list[dict]:
    """The runs under `root`, newest first (their ids sort by time), each as one tab of the rack."""
    if not root.is_dir():
        return []
    now = now or datetime.now(UTC)
    names = sorted((each.name for each in root.iterdir() if each.is_dir() and RUN_ID.fullmatch(each.name)), reverse=True)
    return [_rack_entry(root / name, now) for name in names]


def _rack_entry(directory: Path, now: datetime) -> dict:
    """One tab of the rack: the run's id, the sketch it ran (or `unreadable`) and its state."""
    first, last = _edge_events(directory)
    run = read_json(directory / "run.json")
    state = _state_of(run, last.get("at"), now, last.get("event"), first)
    sketch = "unreadable" if state == "unreadable" else Path(first.get("play", "") or run.get("play", "") or "?").stem
    return {"id": directory.name, "sketch": sketch, "state": state}
