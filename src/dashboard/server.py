"""`understudy dashboard`: a read-only console over the runs under a folder (default `build/runs`).

The server reads each run's `run.json`, `summary.json` and `events.jsonl`; it never starts a run. All logic that
decides what the page shows (the printed lines, the tube, the gauges) lives here, so unittest covers it; the
browser script only draws what `/api/...` returns and follows `/events/<run>` (server-sent events).

    /                      the page            /api/runs          the runs, newest first
    /static files          css, js, fonts      /api/runs/<id>     one run: tube, gauges, printed lines
    /events/<id>           the lines as they are written (server-sent events)
"""

import contextlib
import json
import re
import threading
import time
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
RUN_ID = re.compile(r"run-[0-9A-Za-z-]+")
STATIC_TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".woff2": "font/woff2"}
STATIC_NAMES = re.compile(r"(page\.html|page\.css|page\.js|theme-[a-z-]+\.css|fonts/[a-z0-9-]+\.woff2)")
JEV_FULL_SCALE = 1000  # the JEV gauge reads full at this many requests
ELAPSED_FULL_SCALE = 600  # the ELAPSED gauge reads full at this many seconds
DAY = 86400
AGE_UNITS = (("minutes", 60, 2 * 3600), ("hours", 3600, 2 * DAY))  # unit, seconds per unit, age at which the next unit starts
STALL_SECONDS = 600  # a running run with no new event for this long reads as stalled
RUN_STATES = {"complete": "done", "failed": "failed", "stopped": "stopped"}
MAX_STREAMS = 32  # watchers at once; more get a 503 (SEC-001)
IDLE_SECONDS = 600  # a stream with no new line for this long ends (SEC-001)
SECURITY_HEADERS = {  # SEC-003
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
}
TONES = {"stage_failed": "held", "run_finished": "bold", "run_started": "bold"}


def _read_json(path: Path) -> dict:
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


def printed(event: dict) -> dict:
    """What the printer prints for one event: its text and its tone."""
    kind = event.get("event", "")
    clock = event.get("at", "")[11:19]
    detail = {
        "run_started": lambda: f"=== UNDERSTUDY RUN LOG ===  {event.get('sketch', '')}  ({event.get('mode', '')})",
        "stage_started": lambda: f"  start  {event.get('stage', '')}",
        "stage_completed": lambda: f"  done   {event.get('stage', '')}",
        "stage_failed": lambda: f"  FAILED {event.get('stage', '')}: {event.get('reason', '')}",
        "run_finished": lambda: f"=== {str(event.get('outcome', '')).upper()} ===",
    }.get(kind, lambda: f"  {kind}")()
    return {"text": f"{clock}  {detail}" if clock else detail, "tone": TONES.get(kind, "")}


def _seconds(events: list[dict]) -> float:
    stamps = [datetime.fromisoformat(event["at"]) for event in events if event.get("at")]
    return (stamps[-1] - stamps[0]).total_seconds() if len(stamps) > 1 else 0.0


def gauges_of(run: dict, summary: dict, events: list[dict]) -> list[dict]:
    """Four gauges, each a level from 0 to 1 and the reading, all taken from the run's own files."""
    stages = run.get("stages", {})
    total = len(stages)
    done = sum(1 for each in stages.values() if each == "complete")
    failed = sum(1 for each in events if each.get("event") == "stage_failed")
    requests = int(summary.get("jev_requests", 0))
    seconds = _seconds(events)
    return [
        {"name": "STAGES", "level": done / total if total else 0, "text": f"{done}/{total}", "about": "top-level stages complete"},
        {"name": "FAILED", "level": min(1, failed / total) if total else 0,
         "text": str(failed), "about": "stages that failed (nested too)"},
        {"name": "JEV", "level": min(1, requests / JEV_FULL_SCALE), "text": str(requests), "about": "Jev requests this run made"},
        {"name": "ELAPSED", "level": min(1, seconds / ELAPSED_FULL_SCALE), "text": f"{seconds:.0f}s", "about": "first event to last"},
    ]


def _state_of(run: dict, events: list[dict], now: datetime) -> str:
    """running, done, failed, stopped, stalled (a running run silent for ten minutes) or unreadable (nothing to read)."""
    if not run and not events:
        return "unreadable"
    state = RUN_STATES.get(run.get("status", "running"), "running")
    last = events[-1].get("at") if events else None
    if state == "running" and last and (now - datetime.fromisoformat(last)).total_seconds() > STALL_SECONDS:
        return "stalled"
    return state


def _failure_of(run: dict, events: list[dict]) -> dict | None:
    """The stage and reason a failed run stopped on, and the index of its printed line."""
    if run.get("status") != "failed":
        return None
    line = next((index for index in range(len(events) - 1, -1, -1) if events[index].get("event") == "stage_failed"), None)
    return {"stage": run.get("failed_stage", "?"), "reason": run.get("error", ""), "line": line}


def _ago(seconds: float) -> str:
    """A length of time in the largest unit that keeps it short: minutes, hours or days."""
    for unit, size, until in AGE_UNITS:
        if seconds < until:
            return f"{int(seconds // size)} {unit}"
    return f"{int(seconds // DAY)} days"


def _ended(state: str, run: dict, failure: dict | None, events: list[dict], now: datetime) -> str:
    """One line saying how the run ended (empty while it is still going)."""
    if state == "done":
        done = sum(1 for each in run.get("stages", {}).values() if each == "complete")
        outcome = f", outcome {run['outcome']}" if run.get("outcome") else ""
        return f"done after {done} stages{outcome}"
    if state == "failed" and failure:
        return f"failed at {failure['stage']}: {failure['reason']}"
    if state == "stopped":
        return "stopped before it finished"
    if state == "stalled":
        return f"no new events for {_ago((now - datetime.fromisoformat(events[-1]['at'])).total_seconds())}; the run may have died"
    return "no details for this run" if state == "unreadable" else ""


def describe(directory: Path, now: datetime | None = None) -> dict:
    """One run as the page draws it."""
    now = now or datetime.now(UTC)
    run, summary, events = _read_json(directory / "run.json"), _read_json(directory / "summary.json"), read_events(directory)
    started = next((each for each in events if each.get("event") == "run_started"), {})
    state = _state_of(run, events, now)
    failure = _failure_of(run, events)
    return {
        "id": directory.name,
        "sketch": Path(started.get("sketch", run.get("sketch", "?"))).stem,
        "state": state,
        "ended": _ended(state, run, failure, events, now),
        "failure": failure,
        "summary": {
            "outcome": run.get("outcome"), "mode": run.get("mode", started.get("mode", "")), "stale": summary.get("stale"),
            "seconds": round(_seconds(events)), "with": run.get("with", {}), "outputs": run.get("outputs", {}),
        },
        "mode": run.get("mode", started.get("mode", "")),
        "tube": [{"name": name, "state": stage} for name, stage in run.get("stages", {}).items()],
        "gauges": gauges_of(run, summary, events),
        "lines": [printed(each) for each in events],
        "count": len(events),
    }


def list_runs(root: Path) -> list[dict]:
    """The runs under `root`, newest first (their ids sort by time)."""
    if not root.is_dir():
        return []
    names = sorted((each.name for each in root.iterdir() if each.is_dir() and RUN_ID.fullmatch(each.name)), reverse=True)
    return [_rack_entry(root / name) for name in names]


def _rack_entry(directory: Path) -> dict:
    """One tab of the rack: the run's id, the sketch it ran (or `unreadable`), and its raw status."""
    events, run = read_events(directory), _read_json(directory / "run.json")
    if not events and not run:
        return {"id": directory.name, "sketch": "unreadable", "status": "unreadable"}
    return {"id": directory.name, "sketch": Path(events[0].get("sketch", "") or "?").stem if events else "?",
            "status": run.get("status", "running")}


def route(root: Path, path: str) -> tuple[str, object]:
    """What a path asks for: ("json", value), ("static", file name), ("events", run folder) or ("missing", None)."""
    if path in {"/", "/index.html"}:
        path = "/page.html"
    if path == "/favicon.ico":
        return "empty", None
    if path == "/api/runs":
        return "json", list_runs(root)
    for prefix, kind in (("/api/runs/", "json"), ("/events/", "events")):
        if path.startswith(prefix):
            name = path.removeprefix(prefix)
            directory = root / name
            if not (RUN_ID.fullmatch(name) and directory.is_dir()):
                return "missing", None
            return kind, describe(directory) if kind == "json" else directory
    name = path.removeprefix("/")
    return ("static", name) if STATIC_NAMES.fullmatch(name) else ("missing", None)


def stream_events(handler: BaseHTTPRequestHandler, directory: Path, poll_seconds: float) -> None:
    """Answer one request with a server-sent event stream of the run in `directory`."""
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-store")
    for name, value in SECURITY_HEADERS.items():
        handler.send_header(name, value)
    handler.end_headers()
    for chunk in follow(directory, poll_seconds):
        handler.wfile.write(chunk)
        handler.wfile.flush()


def with_charset(content_type: str) -> str:
    """Text types say they are UTF-8; others are sent as they are."""
    return f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type


def follow(directory: Path, poll_seconds: float, idle_seconds: float = IDLE_SECONDS):
    """The chunks of a server-sent event stream: each printed line once, a tick while waiting, an end marker last.

    The stream also ends when no new line has come for `idle_seconds`, so a run that crashed without `run_finished`
    does not hold a server thread forever (SEC-001).
    """
    sent = 0
    last_news = time.monotonic()
    while True:
        events = read_events(directory)
        for each in events[sent:]:
            yield f"data: {json.dumps(printed(each))}\n\n".encode()
        if len(events) > sent:
            last_news = time.monotonic()
        sent = len(events)
        if any(each.get("event") == "run_finished" for each in events) or time.monotonic() - last_news > idle_seconds:
            yield b"event: end\ndata: {}\n\n"
            return
        yield b": tick\n\n"
        time.sleep(poll_seconds)


def make_handler(root: Path, poll_seconds: float = 0.5, max_streams: int = MAX_STREAMS):
    """The request handler class serving the runs under `root`; at most `max_streams` event streams at once."""
    places = threading.BoundedSemaphore(max_streams)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_arguments) -> None:
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", with_charset(content_type))
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _security_headers(self) -> None:
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)

        def _json(self, value) -> None:
            self._send(HTTPStatus.OK, json.dumps(value).encode(), "application/json")

        def _missing(self, _value=None) -> None:
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

        def do_GET(self) -> None:  # noqa: N802 - the name http.server calls
            kind, value = route(root, self.path.split("?", 1)[0])
            answers = {"json": self._json, "static": self._static, "empty": self._empty, "events": self._follow}
            answers.get(kind, self._missing)(value)

        def _static(self, name: str) -> None:
            self._send(HTTPStatus.OK, (HERE / name).read_bytes(), STATIC_TYPES[Path(name).suffix])

        def _empty(self, _value) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()

        def _follow(self, directory: Path) -> None:
            """Server-sent events: every printed line, then new ones as they are written, until the run finishes."""
            with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                if not places.acquire(blocking=False):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, b"too many watchers", "text/plain")
                    return
                try:
                    stream_events(self, directory, poll_seconds)
                finally:
                    places.release()

    return Handler


def serve(root: Path, port: int = 4180, host: str = "0.0.0.0", max_streams: int = MAX_STREAMS) -> ThreadingHTTPServer:
    """A server for the runs under `root`; the caller starts and stops it."""
    server = ThreadingHTTPServer((host, port), make_handler(root, max_streams=max_streams))
    server.daemon_threads = True
    return server


def serve_forever(root: Path, port: int, stdout) -> None:
    server = serve(root, port)
    stdout.write(f"dashboard: listening on 0.0.0.0:{server.server_address[1]}  (runs under {root}; Ctrl-C to stop)\n")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
