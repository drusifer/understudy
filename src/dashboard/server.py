"""`understudy dashboard`: a console over the runs under a folder (default `.understudy/runs`).

This module is the HTTP side: it routes a request, serves the page files, follows a run's events and, for someone who
holds the access secret, starts, replays and stops runs through `runs.py`. What the page shows about a run (the printed
lines, the stages, the gauges, the rack) is decided in `view.py` and `reads.py`, so unittest covers it; the browser
script only draws what `/api/...` returns and follows `/events/<run>` (server-sent events).

    GET  /                      the page            /api/runs          the runs, newest first
    GET  static files           css, js, fonts      /api/runs/<id>     one run: stages, gauges, printed lines
    GET  /events/<id>           the lines as they are written (server-sent events)
    GET  /api/runs/<id>/jev     the run's Jev reads    /api/sketches, /api/replays, /api/session
    POST /api/start, /api/stop  start (or replay) and stop a run: the secret, a same-origin request, a small JSON body
"""

import contextlib
import hmac
import json
import os
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.dashboard.hold import ACTIONS, GONE, apply_hold
from src.dashboard.reads import jev_reads
from src.dashboard.replay import decisions, replay
from src.dashboard.runs import Launcher, Refused
from src.dashboard.view import describe, list_runs, printed, read_events
from src.paths import ROOT
from src.sketch.sources.capture import CACHE

HERE = Path(__file__).parent
STATIC_TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".woff2": "font/woff2"}
STATIC_NAMES = re.compile(
    r"(page\.html|page\.css|page\.js|controls\.js|replay\.js|decisions\.js|theme-[a-z-]+\.css|fonts/[a-z0-9-]+\.woff2)")
RUN_ROUTE = re.compile(r"/(?P<what>api/runs|events)/(?P<run>run-[0-9A-Za-z-]+)(?P<more>/jev|/replay|/decisions)?")
MAX_STREAMS = 32  # watchers at once; more get a 503 (SEC-001)
IDLE_SECONDS = 600  # a stream with no new line for this long ends (SEC-001)
MAX_BODY = 8192  # bytes of JSON a POST may carry (SEC-006)
DRAIN_LIMIT = 1 << 20  # an oversized body is read (and thrown away) only up to this many bytes before the answer
WRONG_SECRET_PAUSE = 1.0  # seconds a request with a missing or wrong secret waits before it is answered (SEC-005)
SECRET_HEADER = "X-Understudy-Secret"
SECRET_FILE = ROOT / ".understudy" / "dashboard.secret"  # git-ignored, readable by its owner alone (SEC-008)
SECURITY_HEADERS = {  # SEC-003
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
}


@dataclass(frozen=True)
class Console:
    """What a console serves and where it reads: the runs folder, the Jev captures, the project, and (when it can start
    runs) the launcher and the access secret."""

    root: Path
    cache: Path = CACHE
    project: Path = ROOT
    launcher: Launcher | None = None
    secret: str | None = None
    controllable: Callable[[str], bool] | None = None  # whether this console may hold, step and resume a run (by its id)

    def holds(self, presented: str | None) -> bool:
        """Whether the secret presented is the console's (compared in constant time); false when there is none."""
        return bool(self.secret and presented and hmac.compare_digest(presented.encode(), self.secret.encode()))


def route(console: Console, path: str, *, revealed: bool = False, query: str = "") -> tuple[str, object]:
    """What a path asks for: ("json", value), ("refused", (status, message)), ("static", file name), ("events", run
    folder), ("session", None), ("empty", None) or ("missing", None). `revealed` says the caller holds the secret."""
    if path in {"/", "/index.html"}:
        path = "/page.html"
    fixed = {
        "/favicon.ico": ("empty", None), "/api/session": ("session", None), "/api/runs": ("json", list_runs(console.root)),
        "/api/sketches": ("json", console.launcher.list_sketches() if console.launcher else []),
        "/api/replays": ("json", console.launcher.replays() if console.launcher else []),
    }
    if path in fixed:
        return fixed[path]
    match = RUN_ROUTE.fullmatch(path)
    if match:
        directory = console.root / match["run"]
        if directory.is_dir() and not (match["what"] == "events" and match["more"]):
            return _run_answer(console, directory, match, revealed, query)
        return "missing", None
    name = path.removeprefix("/")
    return ("static", name) if STATIC_NAMES.fullmatch(name) else ("missing", None)


def _run_answer(console: Console, directory: Path, match: re.Match, revealed: bool, query: str) -> tuple[str, object]:
    """The answer for one run: a stream of its events, its Jev reads, its replay or its description."""
    if match["what"] == "events":
        return "events", directory
    if match["more"] == "/jev":
        return "json", jev_reads(directory, console.cache, console.project, reveal=revealed)
    if match["more"] in ("/replay", "/decisions"):
        try:
            return "json", decisions(directory) if match["more"] == "/decisions" else replay(directory, _position(query))
        except Refused as refused:
            return "refused", (refused.status, refused.message)
    return "json", describe(directory)


def _position(query: str) -> int | None:
    """The `at` of a replay request (a whole number), None when the request has none; anything else is refused."""
    values = parse_qs(query, keep_blank_values=True).get("at")
    if not values:
        return None
    if not re.fullmatch(r"[0-9]{1,9}", values[0]):
        raise Refused(HTTPStatus.BAD_REQUEST, "at must be a whole number of events")
    return int(values[0])


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


class ConsoleHandler(BaseHTTPRequestHandler):
    """One request. `console`, `poll_seconds` and `places` (the room for event streams) are set by `make_handler`."""

    console: Console
    poll_seconds: float
    places: threading.BoundedSemaphore

    def log_message(self, *_arguments) -> None:
        return

    def handle(self) -> None:
        """Serve the connection; a client that hangs up before its answer is not an error worth a traceback."""
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            super().handle()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", with_charset(content_type))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, value, status: int = HTTPStatus.OK) -> None:
        self._send(status, json.dumps(value).encode(), "application/json")

    def _missing(self, _value=None) -> None:
        self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

    def _holds_secret(self) -> bool:
        return self.console.holds(self.headers.get(SECRET_HEADER))

    def do_GET(self) -> None:  # noqa: N802 - the name http.server calls
        parts = urlparse(self.path)
        kind, value = route(self.console, parts.path, revealed=self._holds_secret(), query=parts.query)
        answers = {"json": self._json, "static": self._static, "empty": self._empty, "events": self._follow, "session": self._session,
                   "refused": self._refused_get}
        answers.get(kind, self._missing)(value)

    def _refused_get(self, refusal: tuple[int, str]) -> None:
        self._json({"problem": refusal[1]}, refusal[0])

    def _session(self, _value) -> None:
        self._json({"controls": self.console.launcher is not None, "holdable": self.console.controllable is not None,
                    "authorized": self._holds_secret()})

    def do_POST(self) -> None:  # noqa: N802 - the name http.server calls
        path = self.path.split("?", 1)[0]
        holding = path.startswith("/api/") and path.removeprefix("/api/") in ACTIONS
        action = self._hold if holding else {"/api/start": self._start, "/api/stop": self._stop}.get(path)
        if action is None or (self.console.controllable is None if holding else self.console.launcher is None):
            return self._missing()
        refusal = self._refusal()
        if refusal:
            return self._json({"problem": refusal[1]}, refusal[0])
        try:
            return self._json(action(self._body()))
        except Refused as refused:
            return self._json({"problem": refused.message}, refused.status)

    def _refusal(self) -> tuple[int, str] | None:
        """Why this POST may not go on (another site, no secret), else None. A wrong secret costs a pause."""
        origin = self.headers.get("Origin")
        if origin and urlparse(origin).netloc != self.headers.get("Host"):
            return HTTPStatus.FORBIDDEN, "that request came from another site"
        if not self._holds_secret():
            time.sleep(WRONG_SECRET_PAUSE)
            return HTTPStatus.UNAUTHORIZED, "this needs the access secret printed where the console was started"
        return None

    def _body(self) -> dict:
        """The JSON object the request carries; raises `Refused` for one too large or not an object."""
        text = self.headers.get("Content-Length") or "0"
        if not text.isdigit():  # a negative or unreadable length would make the read wait for data that never comes
            self.close_connection = True
            raise Refused(HTTPStatus.BAD_REQUEST, "the request has no usable Content-Length")
        length = int(text)
        if length > MAX_BODY:
            self.rfile.read(min(length, DRAIN_LIMIT))  # read what was sent so the client sees the answer, not a reset
            self.close_connection = True
            raise Refused(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "that request is too large")
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            body = None
        if not isinstance(body, dict):
            raise Refused(HTTPStatus.BAD_REQUEST, "the request must be a JSON object")
        return body

    def _start(self, body: dict) -> dict:
        values = body.get("with", {})
        if not isinstance(body.get("sketch"), str) or not isinstance(values, dict):
            raise Refused(400, "start needs a sketch name and an object of values")
        return self.console.launcher.start(body["sketch"], values, body.get("replay"))

    def _stop(self, body: dict) -> dict:
        if not isinstance(body.get("run"), str):
            raise Refused(400, "stop needs the id of a run")
        return self.console.launcher.stop(body["run"])

    def _hold(self, body: dict) -> dict:
        """Pause, step or resume (the last word of the path) a run this console is allowed to control."""
        run = body.get("run")
        if not isinstance(run, str):
            raise Refused(400, "this needs the id of a run")
        if not self.console.controllable(run):
            raise Refused(404, GONE)
        return apply_hold(self.console.root, run, self.path.split("?", 1)[0].removeprefix("/api/"))

    def _static(self, name: str) -> None:
        self._send(HTTPStatus.OK, (HERE / name).read_bytes(), STATIC_TYPES[Path(name).suffix])

    def _empty(self, _value) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _follow(self, directory: Path) -> None:
        """Server-sent events: every printed line, then new ones as they are written, until the run finishes."""
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            if not self.places.acquire(blocking=False):
                self._send(HTTPStatus.SERVICE_UNAVAILABLE, b"too many watchers", "text/plain")
                return
            try:
                stream_events(self, directory, self.poll_seconds)
            finally:
                self.places.release()


def make_handler(console: Console, poll_seconds: float = 0.5, max_streams: int = MAX_STREAMS):
    """The request handler class for `console`; at most `max_streams` event streams at once."""
    return type("Handler", (ConsoleHandler,), {"console": console, "poll_seconds": poll_seconds,
                                              "places": threading.BoundedSemaphore(max_streams)})


def serve(  # noqa: PLR0913 - the places a console reads from, each overridable for tests
    root: Path, port: int = 4180, host: str = "0.0.0.0", max_streams: int = MAX_STREAMS, cache: Path = CACHE, project: Path = ROOT,
    launcher: Launcher | None = None, secret: str | None = None, controllable: Callable[[str], bool] | None = None,
) -> ThreadingHTTPServer:
    """A server for the runs under `root`; the caller starts and stops it. `controllable` says which runs it may hold."""
    console = Console(Path(root), Path(cache), Path(project), launcher, secret, controllable)
    server = ThreadingHTTPServer((host, port), make_handler(console, max_streams=max_streams))
    server.daemon_threads = True
    return server


def save_secret(path: Path, secret: str) -> None:
    """Write the secret to a file only its owner can read, replacing the last console's."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(secret + "\n")
    path.chmod(0o600)


def announce(stdout, root: Path, port: int, secret: str | None, secret_file: Path) -> None:
    """Say where the console is and where its access secret was saved, and flush (a pipe or a log file would hold the
    lines back). The secret itself is never written to the output: `bobp make` copies output into the team chat (SEC-008)."""
    stdout.write(f"dashboard: listening on 0.0.0.0:{port}  (runs under {root}; Ctrl-C to stop)\n")
    if secret:
        save_secret(secret_file, secret)
        stdout.write(f"access secret for start, replay and stop: saved in {secret_file} (read it there; it changes at every start)\n")
    stdout.flush()


def serve_forever(root: Path, port: int, stdout, launcher: Launcher | None = None, secret: str | None = None) -> None:
    server = serve(root, port, launcher=launcher, secret=secret, controllable=launcher.holds if launcher else None)
    announce(stdout, root, server.server_address[1], secret if launcher else None, SECRET_FILE)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
