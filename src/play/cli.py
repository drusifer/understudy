"""`understudy run <sketch.yaml>` and `understudy check <sketch.yaml>`.

Exit codes: 0 done, 1 a stage failed after the run started, 2 refused before starting. Every failure ends with
one `understudy: <message>` line saying what to fix; there is never a traceback.
"""

import argparse
import asyncio
import contextlib
import errno
import secrets
import sys
import threading
from collections.abc import Mapping
from pathlib import Path

import src.play.stages  # noqa: F401 - importing it registers the stages
from src.dashboard.runs import Launcher, Refused
from src.dashboard.server import serve_forever
from src.dashboard.view import list_runs
from src.dashboard.watch import Watch
from src.jev import JevError, TypeSafeJev
from src.paths import OutputPathError
from src.play.check import load_checked
from src.play.loader import PlayError
from src.play.registry import StageFn
from src.play.registry import library as registered
from src.play.run import run_sketch
from src.play.sources.capture import CaptureStore, ReplayError
from src.play.sources.reader import Capture, needs_jev

DEFAULT_OUT = Path(".understudy/runs")  # git-ignored and private, beside the captures; `make clean` leaves it alone


def _values(pairs: list[str]) -> dict[str, str]:
    values = {}
    for pair in pairs:
        name, separator, value = pair.partition("=")
        if not name or not separator:
            raise PlayError([f"--with needs <name>=<value>, not {pair!r}"])
        values[name] = str(Path(value).resolve()) if value and not Path(value).is_absolute() and Path(value).is_file() else value
    return values


EXAMPLES = """examples:
  understudy check examples/household/household.yaml --with monarch=in/monarch.csv --with amex=in/amex.csv --with amex_account=Platinum
  understudy run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay
  understudy run <play> --watch --pause     start held, with a console on this machine to step it (secret file)
  understudy dashboard                    watch runs under .understudy/runs; start plays from examples/ (access secret file)
  understudy runs                         the runs under .understudy/runs, newest first

A failure is one `understudy: <message>` line; exit 0 is done, 1 a beat failed after the run began, 2 refused before it began."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="understudy", description="Perform a play of how you decide, and watch what it did.",
                                     epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")
    descriptions = {
        "run": "run a play and write its outputs into a folder of runs",
        "check": "check a play and every play it calls, and run nothing",
    }
    for name, summary in descriptions.items():
        command = commands.add_parser(name, help=summary, description=summary)
        command.add_argument("sketch", type=Path, metavar="play", help="the play file (YAML)")
        command.add_argument("--with", action="append", default=[], metavar="NAME=VALUE", dest="values",
                             help="give the play a prop (a date, a weight) or a stage file its path; repeat for each")
    dashboard = commands.add_parser("dashboard", help="serve the console: watch runs, and start, replay and stop them",
                                    description="Serve the console on this machine's port (every network interface). It watches "
                                    "the runs under RUNS and, for someone with the access secret, starts plays from --plays.")
    dashboard.add_argument("runs", type=Path, nargs="?", default=DEFAULT_OUT, metavar="RUNS", help="the folder of runs to watch")
    dashboard.add_argument("--port", type=int, default=4180, help="the port to listen on (default 4180)")
    dashboard.add_argument("--plays", type=Path, default=Path("examples"), metavar="DIR", dest="sketches",
                           help="the folder of plays the console may start (default examples)")
    listing = commands.add_parser("runs", help="list the runs in a folder, newest first, with how each ended",
                                  description="List the runs in a folder, newest first, with the play and how each ended.")
    listing.add_argument("folder", type=Path, nargs="?", default=DEFAULT_OUT, help="the folder of runs (default .understudy/runs)")
    run = commands.choices["run"]
    run.add_argument("--out", type=Path, default=DEFAULT_OUT, metavar="FOLDER",
                     help="the folder to make the run's folder in (default .understudy/runs)")
    run.add_argument("--replay", nargs="?", const="", default=None, metavar="RUN-ID|DIR",
                     help="read the captured Jev answers of a run or folder instead of calling Jev (no key, no network)")
    run.add_argument("--watch", action="store_true",
                     help="open a console on this machine for this run, where you can pause, step and resume it")
    run.add_argument("--pause", action="store_true", help="start the run held before its first beat (needs --watch)")
    run.add_argument("--stop-at", metavar="BEAT", default=None,
                     help="run up to this beat of the scene's flow and hold before it (needs --watch)")
    run.add_argument("--by-console", action="store_true", help=argparse.SUPPRESS)  # a console that started this run steps it
    run.add_argument("--port", type=int, default=0, help="the port --watch listens on (default: any free one)")
    return parser


def _capture(args, sketch, store, make_jev) -> Capture:
    if args.replay is not None:
        return Capture.replay(store, sketch, args.replay or None)
    return Capture.live(store, make_jev() if needs_jev(sketch) else None)


def _dashboard(args, stdout, stderr) -> int:
    """Start the console; every way it can fail to start is one line and exit 2."""
    try:
        if args.runs.exists() and not args.runs.is_dir():
            raise Refused(400, f"{args.runs} is not a folder of runs")
        args.runs.mkdir(parents=True, exist_ok=True)
        launcher = Launcher(args.sketches, args.runs)
        serve_forever(args.runs, args.port, stdout, launcher, secrets.token_urlsafe(32))
    except Refused as refusal:
        stderr.write(f"understudy: {refusal.message}\n")
        return 2
    except OSError as error:
        busy = error.errno == errno.EADDRINUSE
        stderr.write(f"understudy: port {args.port} is already in use; choose another with --port\n" if busy
                     else f"understudy: cannot start the console: {error.strerror or error}\n")
        return 2
    return 0


def _runs(args, stdout) -> int:
    """The runs in a folder, newest first: id, sketch and how each ended."""
    runs = list_runs(args.folder)
    if not runs:
        stdout.write(f"no runs in {args.folder}\n")
    for each in runs:
        stdout.write(f"{each['id']}  {each['sketch']}  {each['state']}\n")
    return 0


def main(  # noqa: PLR0911, PLR0913 - the command line's injection points
    argv=None, *, library: Mapping[str, StageFn] | None = None, make_jev=TypeSafeJev, store: CaptureStore | None = None,
    stdout=None, stderr=None, hold_open=None,
) -> int:
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    hold_open = hold_open or _until_interrupted
    args = _parser().parse_args(argv)
    if args.command == "dashboard":
        return _dashboard(args, stdout, stderr)
    if args.command == "runs":
        return _runs(args, stdout)

    def fail(message: str, code: int) -> int:
        stderr.write(f"understudy: {message}\n")
        return code

    if message := _needs_watch(args):
        return fail(message, 2)

    try:
        sketch = load_checked(args.sketch, {}, _values(args.values))
        _require_stop_beat(sketch, getattr(args, "stop_at", None))
    except PlayError as error:
        for problem in error.problems[:-1]:
            stderr.write(f"understudy: {problem}\n")
        return fail(error.problems[-1], 2)
    if args.command == "check":
        stdout.write(f"ok: {sketch.name}\n")
        return 0
    try:
        capture = _capture(args, sketch, store or CaptureStore(), make_jev)
    except (ReplayError, JevError) as error:
        return fail(str(error), 2)
    watch = None
    if args.watch:
        try:
            watch = Watch(args.out, args.port, stdout)
        except OSError as error:
            busy = error.errno == errno.EADDRINUSE
            return fail(f"port {args.port} is already in use; choose another with --port" if busy
                        else f"cannot start the console: {error.strerror or error}", 2)
    try:
        plan = (sketch, capture, registered() if library is None else library)
        return _execute(args, plan, (stdout, stderr), watch)
    finally:
        if watch:
            stdout.write(f"the run is over; the console stays at {watch.address} until you press Ctrl-C\n")
            stdout.flush()
            hold_open()
            watch.close()


def _needs_watch(args) -> str | None:
    """The refusal for a hold flag given with nothing to step the run (a console of its own or one that started it)."""
    if getattr(args, "watch", False) or getattr(args, "by_console", False):
        return None
    flag = next((name for name, given in (("--pause", getattr(args, "pause", False)), ("--stop-at", getattr(args, "stop_at", None)))
                 if given), None)
    return f"{flag} needs --watch" if flag else None


def _require_stop_beat(sketch, beat: str | None) -> None:
    """Refuse `--stop-at beat` unless it names a beat in the scene's flow that is not final."""
    states = sketch.machine["states"]
    if beat is None or (beat in states and not states[beat].get("final")):
        return
    flow = ", ".join(name for name, state in states.items() if not state.get("final"))
    raise PlayError([f"--stop-at: {beat!r} is not a beat the run holds before (the flow has: {flow})"])


def _execute(args, plan, streams, watch) -> int:
    """Run the sketch and say what it made; every way it can fail is one line and its exit code. `plan` is the sketch,
    its capture and the stages that run it."""
    sketch, capture, stages = plan
    stdout, stderr = streams
    try:
        result = asyncio.run(run_sketch(sketch, args.out, stages, lambda line: stdout.write(line + "\n"), capture,
                                        pause=args.pause, on_start=watch.started if watch else None, stop_at=args.stop_at))
    except OutputPathError as error:
        stderr.write(f"understudy: {error}\n")
        return 2
    except Exception as error:
        stderr.write(f"understudy: {str(error) or type(error).__name__}\n")
        return 1
    stdout.write(f"run: {result.directory.name}\nwatch it: understudy dashboard {args.out}\n")
    for path in result.outputs.values():  # the outputs and the outcome stay last: scripts read the last line
        stdout.write(f"wrote {path}\n")
    if result.outcome:
        stdout.write(f"outcome: {result.outcome}\n")
    return 0


def _until_interrupted() -> None:
    """Keep a watching console open after its run ends, until Ctrl-C."""
    with contextlib.suppress(KeyboardInterrupt):
        threading.Event().wait()


if __name__ == "__main__":
    sys.exit(main())
