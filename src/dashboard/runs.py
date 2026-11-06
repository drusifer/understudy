"""Start, replay and stop runs from the console (UND-79). The one part of the console that does anything.

A `Launcher` knows one folder of sketches and the folder of runs the console watches. It starts `understudy run` as
a child process (an argument list, no shell, its own session), at most one per sketch and four in all, after the same
check `understudy check` makes; it stops only the children it started. Every refusal is a `Refused` with an HTTP
status and a sentence the page shows. Who may call it is decided in `server.py` (the access secret); what may be run
is decided here (only a sketch inside the folder, only names the sketch takes, only files inside the project).
"""

import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path

from src.dashboard.chart import plan_layout
from src.dashboard.view import RUN_ID, read_json
from src.paths import ROOT
from src.play.inputs import problems as input_problems
from src.play.inputs import value_problem
from src.play.loader import PlayError, props_of, read_template
from src.play.plan import plan
from src.play.sources.capture import CACHE

MAX_CHILDREN = 4
SETTLE_SECONDS = 1.5  # a run that dies within this long is reported as a failed start, with the reason it printed
FIND_RUN_SECONDS = 2.0  # how long to look for the folder a new run makes
STOP_SECONDS = 3.0  # SIGTERM, then this long, then SIGKILL
COMMAND = (sys.executable, "-m", "src.play.cli")
TAIL_LINES = 20


class Refused(Exception):  # noqa: N818 - a refusal, not an error: the page shows its message
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


class _Child:
    """A started process and the last lines it printed on stderr (they say why a run could not start)."""

    def __init__(self, argv: list[str], **options):
        self.process = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, **options)
        self.pid = self.process.pid
        self.stderr_tail: deque[str] = deque(maxlen=TAIL_LINES)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        for line in self.process.stderr:
            self.stderr_tail.append(line.rstrip())

    def poll(self):
        return self.process.poll()

    def wait(self, timeout: float | None = None):
        return self.process.wait(timeout)

    @property
    def returncode(self):
        return self.process.returncode


def _environment() -> dict[str, str]:
    """The console's environment (so a run finds `TYPESAFE_API_KEY` as it would from a terminal) plus the code's location."""
    return {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(ROOT), os.environ.get("PYTHONPATH", "")]))}


def _run_check(argv: list[str], project: Path) -> list[str]:
    """Run `understudy check`; its problems, one per line, or nothing when the sketch passes."""
    done = subprocess.run(argv, cwd=project, env=_environment(), capture_output=True, text=True, timeout=60, check=False)
    return [] if done.returncode == 0 else [line for line in done.stderr.splitlines() if line.strip()] or ["the check failed"]


def _file_defaults(document: dict) -> dict[str, dict]:
    """What the page says about each file a play reads: the `default` path it uses when none is given (None when it has
    none, so one must be given), and whether it is `optional`."""
    stage = document.get("stage")
    return {name: {"default": piece.get("path"), "optional": bool(piece.get("optional"))}
            for name, piece in (stage.items() if isinstance(stage, dict) else [])
            if isinstance(piece, dict) and piece.get("kind") == "file" and piece.get("access", "read") == "read"}


def _files_read(document: dict) -> set[str]:
    """The stage files a play reads: each can be given a path when it is started (`--with <name>=<file>`)."""
    stage = document.get("stage")
    return {name for name, piece in (stage.items() if isinstance(stage, dict) else [])
            if isinstance(piece, dict) and piece.get("kind") == "file" and piece.get("access", "read") == "read"}


def _called_files(path: Path, document: dict) -> set[Path]:
    """The play files this one calls (`do: { play: <file>.yaml }`), from its beats."""
    scene = document.get("scene")
    beats = scene.get("beats") if isinstance(scene, dict) else None
    called = set()
    for beat in (beats.values() if isinstance(beats, dict) else []):
        do = beat.get("do") if isinstance(beat, dict) else None
        if isinstance(do, dict) and isinstance(do.get("play"), str):
            called.add((path.parent / do["play"]).resolve())
    return called


class Launcher:
    def __init__(  # noqa: PLR0913 - the places a launcher touches, each replaceable by a test
        self, sketches: Path, runs: Path, *, project: Path = ROOT, cache: Path = CACHE, spawn: Callable | None = None,
        check: Callable[[list[str]], list[str]] | None = None, kill: Callable[[int, int], None] = os.killpg,
        find_run: Callable | None = None, settle: float = SETTLE_SECONDS, max_children: int = MAX_CHILDREN,
    ):
        self.sketches, self.runs, self.project, self.cache = Path(sketches), Path(runs), Path(project), Path(cache)
        self.spawn = spawn or _Child
        self.check = check or (lambda argv: _run_check(argv, self.project))
        self.kill, self.settle, self.max_children = kill, settle, max_children
        self.find_run = find_run or self._find_run
        self._children: dict[str, dict] = {}
        self._lock = threading.Lock()
        if not self.sketches.is_dir():
            raise Refused(400, f"{self.sketches} is not a folder of sketches")
        if not self.list_sketches():
            raise Refused(400, f"no sketches found in {self.sketches}")

    # -- what can be run --------------------------------------------------------------------------------------

    def list_sketches(self) -> list[dict]:
        """Each sketch file under the folder that is not only called by another, with what the page needs to show it."""
        scanned = []
        inside = self.sketches.resolve()
        for path in sorted(each for each in self.sketches.rglob("*.yaml") if each.resolve().is_relative_to(inside)):
            relative = path.relative_to(self.sketches).as_posix()
            try:
                document, uses = read_template(path)
            except PlayError as error:
                scanned.append({"path": path, "file": relative, "name": path.stem, "description": "", "with": [], "files": {},
                                "inputs": [], "ok": False, "problem": error.problems[0].removeprefix(f"{path}: "), "called": set()})
                continue
            declared = props_of(document)
            wrong = [problem for name, spec in declared.items() for problem in input_problems(name, spec)]
            valid = isinstance(document.get("scene"), dict) and "name" in document and not wrong
            scanned.append({"path": path, "file": relative, "name": str(document.get("name", path.stem)),
                            "description": " ".join(str(document.get("description", "")).split()),
                            "with": sorted((uses - set(declared)) | _files_read(document)),
                            "files": _file_defaults(document),
                            "inputs": [] if wrong else [{**spec, "name": name, "label": spec.get("label", name)}
                                                        for name, spec in declared.items()],
                            "ok": valid,
                            "problem": wrong[0] if wrong else "" if valid else "not a play: it needs a name and a scene",
                            "called": _called_files(path, document) if valid else set()})
        children = set().union(*(each["called"] for each in scanned)) if scanned else set()
        return [{key: value for key, value in each.items() if key not in {"path", "called"}}
                for each in scanned if each["path"].resolve() not in children]

    def plan(self, name: str) -> dict:
        """The pieces and beats of the listed play `name`, laid out for the page to draw. Only a play `list_sketches`
        offers has a plan; any other name is refused, so no path from the client is ever opened."""
        path, _entry = self._sketch(name)
        return plan_layout(plan(read_template(path)[0]))

    def replays(self) -> list[dict]:
        """The captured runs a replay can read, newest first, each with the name of the play that made it (`play`; empty when
        its run folder is gone). A capture is read only by the play that made it, so the page offers a play its own."""
        if not self.cache.is_dir():
            return []
        ids = sorted((each.name for each in self.cache.iterdir() if each.is_dir() and RUN_ID.fullmatch(each.name)), reverse=True)
        return [{"id": each, "play": str(read_json(self.runs / each / "run.json").get("play", ""))} for each in ids]

    # -- start and stop ---------------------------------------------------------------------------------------

    def start(self, sketch: str, values: dict, replay: str | None = None, hold: object = False, hold_at: object = None) -> dict:
        """Start the listed play `sketch`. `hold` starts it held before its first beat; `hold_at` names a beat of its flow to
        hold before instead. Either way this console steps the run (it is the one that started it)."""
        path, entry = self._sketch(sketch)
        arguments = self._values(entry, values)
        folder = self._replay(replay)
        flags = self._hold_arguments(path, hold, hold_at)
        with self._lock:
            self._reap()
            if sketch in self._children:
                known = self._children[sketch]["run"]
                raise Refused(409, f"already running{f' as {known}' if known else ''}")
            if len(self._children) >= self.max_children:
                raise Refused(409, f"at most {self.max_children} runs at once")
            problems = self.check([*COMMAND, "check", str(path), *arguments])
            if problems:
                raise Refused(400, "\n".join(problems))
            before = {each.name for each in self.runs.iterdir()} if self.runs.is_dir() else set()
            argv = [*COMMAND, "run", str(path), *arguments, *flags, "--out", str(self.runs),
                    *([f"--replay={folder}"] if folder else [])]
            child = self.spawn(argv, cwd=str(self.project), env=_environment(), start_new_session=True)
            self._settle(child)
            run = self.find_run(sketch, before)
            self._children[sketch] = {"child": child, "run": run}
            return {"started": True, "run": run}

    def holds(self, run_id: str) -> bool:
        """Whether this launcher started the run `run_id` and it is still going (the runs it may hold, step and resume)."""
        with self._lock:
            self._reap()
            return bool(RUN_ID.fullmatch(run_id)) and any(each["run"] == run_id for each in self._children.values())

    def stop(self, run_id: str) -> dict:
        """End a run this console started, and mark its run `stopped` (the killed process cannot)."""
        with self._lock:
            self._reap()
            found = next((each for each in self._children.values() if RUN_ID.fullmatch(run_id) and each["run"] == run_id), None)
            if found is None:
                raise Refused(404, "that run was not started by this console, or it has finished")
            child = found["child"]
            self.kill(child.pid, signal.SIGTERM)
            try:
                child.wait(STOP_SECONDS)
            except subprocess.TimeoutExpired:
                self.kill(child.pid, signal.SIGKILL)
            self._mark_stopped(run_id)
            return {"stopped": True, "run": run_id}

    # -- helpers ----------------------------------------------------------------------------------------------

    def _sketch(self, name: str) -> tuple[Path, dict]:
        """The listed sketch `name` names, as its resolved path inside the sketches folder."""
        resolved = (self.sketches / name).resolve()
        listed = {each["file"]: each for each in self.list_sketches()}
        inside = resolved.is_relative_to(self.sketches.resolve())
        entry = listed.get(resolved.relative_to(self.sketches.resolve()).as_posix()) if inside else None
        if entry is None or not entry["ok"] or resolved.suffix != ".yaml" or not resolved.is_file():
            raise Refused(403, f"{name!r} is not a sketch in the sketches folder")
        return resolved, entry

    def _hold_arguments(self, path: Path, hold: object, hold_at: object) -> list[str]:
        """The flags that start a run held (nothing when it is not), after checking the choice: `hold` a yes or no, `hold_at`
        a beat of the play's flow that is not final, and not both."""
        if not isinstance(hold, bool) or not (hold_at is None or isinstance(hold_at, str)):
            raise Refused(400, "hold is yes or no, and hold_at is the name of a beat")
        if hold and hold_at is not None:
            raise Refused(400, "choose hold or hold_at, not both")
        if hold_at is not None:
            nodes = plan(read_template(path)[0])["nodes"]
            flow = [each["id"] for each in nodes if each["kind"] == "beat" and each["flow"] and not each["final"]]
            if hold_at not in flow:
                raise Refused(400, f"{hold_at!r} is not a beat the run can hold before; the flow has: {', '.join(flow)}")
            return ["--by-console", "--stop-at", hold_at]
        return ["--by-console", "--pause"] if hold else []

    def _values(self, entry: dict, values: dict) -> list[str]:
        """The `--with name=value` arguments for the values given, refusing a name the sketch does not take, a value over
        several lines, and a value that names an existing file outside the project (SEC-006)."""
        declared = {each["name"]: each for each in entry["inputs"]}
        takes = [*(each["name"] for each in entry["inputs"]), *entry["with"]]
        unknown = sorted(set(values) - set(takes))
        if unknown:
            raise Refused(400, f"unknown name {', '.join(unknown)}; this sketch takes: {', '.join(takes) or 'nothing'}")
        arguments = []
        for name, value in values.items():
            text = str(value)
            if name in declared and (problem := value_problem(name, declared[name], text)):
                raise Refused(400, problem)
            if "\n" in text or "\r" in text:
                raise Refused(400, f"{name}: a value must be a single line")
            candidate = (self.project / text) if text else None
            if candidate is not None and candidate.exists() and not candidate.resolve().is_relative_to(self.project.resolve()):
                raise Refused(400, f"{name}: that file is outside the project")
            arguments += ["--with", f"{name}={text}"]
        return arguments

    def _replay(self, replay: str | None) -> Path | None:
        if replay is None:
            return None
        if replay not in {each["id"] for each in self.replays()}:
            raise Refused(400, f"no captured run {replay!r}")
        return self.cache / replay

    def _settle(self, child) -> None:
        """Wait a moment: a run that dies at once did not start, and says why in its last line."""
        deadline = time.monotonic() + self.settle
        while time.monotonic() < deadline and child.poll() is None:
            time.sleep(0.05)
        code = child.poll()
        if code not in (None, 0):
            tail = [line for line in getattr(child, "stderr_tail", []) if line.strip()]
            raise Refused(400, f"could not start: {tail[-1] if tail else f'the run stopped at once (exit {code})'}")

    def _find_run(self, _sketch: str, before: set[str]) -> str | None:
        """The folder the new run made, once it appears."""
        deadline = time.monotonic() + FIND_RUN_SECONDS
        while time.monotonic() < deadline:
            names = [each.name for each in self.runs.iterdir() if each.is_dir()] if self.runs.is_dir() else []
            fresh = sorted(name for name in names if name not in before)
            if fresh:
                return fresh[-1]
            time.sleep(0.1)
        return None

    def _reap(self) -> None:
        for sketch in [name for name, each in self._children.items() if each["child"].poll() is not None]:
            del self._children[sketch]

    def _mark_stopped(self, run_id: str) -> None:
        manifest = self.runs / run_id / "run.json"
        data = read_json(manifest)  # empty when the run was killed before its first stage finished: it never wrote one
        if data.get("status", "running") == "running":
            data = {"beats": {}, **data, "status": "stopped"}
            temporary = manifest.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            temporary.replace(manifest)
