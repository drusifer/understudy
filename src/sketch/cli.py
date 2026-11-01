"""`understudy run <sketch.yaml>` and `understudy check <sketch.yaml>`.

Exit codes: 0 done, 1 a stage failed after the run started, 2 refused before starting. Every failure ends with
one `understudy: <message>` line saying what to fix; there is never a traceback.
"""

import argparse
import asyncio
import errno
import secrets
import sys
from collections.abc import Mapping
from pathlib import Path

import src.sketch.stages  # noqa: F401 - importing it registers the stages
from src.dashboard.runs import Launcher, Refused
from src.dashboard.server import serve_forever
from src.dashboard.view import list_runs
from src.jev import JevError, TypeSafeJev
from src.paths import OutputPathError
from src.sketch.check import load_checked
from src.sketch.loader import SketchError
from src.sketch.registry import StageFn
from src.sketch.registry import library as registered
from src.sketch.run import run_sketch
from src.sketch.sources.capture import CaptureStore, ReplayError
from src.sketch.sources.reader import Capture, needs_jev

DEFAULT_OUT = Path("build/runs")


def _overrides(pairs: list[str]) -> dict[str, str]:
    overrides = {}
    for pair in pairs:
        name, _, path = pair.partition("=")
        name = name.removesuffix(".path")
        if not name or not path:
            raise SketchError([f"--source needs <name>.path=<file>, not {pair!r}"])
        overrides[name] = path
    return overrides


def _values(pairs: list[str]) -> dict[str, str]:
    values = {}
    for pair in pairs:
        name, separator, value = pair.partition("=")
        if not name or not separator:
            raise SketchError([f"--with needs <name>=<value>, not {pair!r}"])
        values[name] = str(Path(value).resolve()) if value and not Path(value).is_absolute() and Path(value).is_file() else value
    return values


EXAMPLES = """examples:
  understudy check examples/household/household.yaml --with monarch=in/monarch.csv --with amex=in/amex.csv --with amex_account=Platinum
  understudy run tests/fixtures/coffee/coffee_week.yaml --replay=tests/fixtures/coffee/replay
  understudy dashboard                    watch runs under build/runs, and start sketches from examples/ (see the access secret file)
  understudy runs                         the runs under build/runs, newest first

A failure is one `understudy: <message>` line; exit 0 is done, 1 a stage failed after the run began, 2 refused before it began."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="understudy", description="Run a sketch of how you decide, and watch what it did.",
                                     epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")
    descriptions = {
        "run": "run a sketch and write its outputs into a folder of runs",
        "check": "check a sketch and everything it names, and run nothing",
    }
    for name, summary in descriptions.items():
        command = commands.add_parser(name, help=summary, description=summary)
        command.add_argument("sketch", type=Path, help="the sketch file (YAML)")
        command.add_argument("--source", action="append", default=[], metavar="NAME.path=FILE",
                             help="read this file for the file source NAME, for this run only")
        command.add_argument("--with", action="append", default=[], metavar="NAME=VALUE", dest="values",
                             help="give the sketch a value it uses (a file name, a date, a weight); repeat for each")
    dashboard = commands.add_parser("dashboard", help="serve the console: watch runs, and start, replay and stop them",
                                    description="Serve the console on this machine's port (every network interface). It watches "
                                    "the runs under RUNS and, for someone with the access secret, starts sketches from --sketches.")
    dashboard.add_argument("runs", type=Path, nargs="?", default=DEFAULT_OUT, metavar="RUNS", help="the folder of runs to watch")
    dashboard.add_argument("--port", type=int, default=4180, help="the port to listen on (default 4180)")
    dashboard.add_argument("--sketches", type=Path, default=Path("examples"), metavar="DIR",
                           help="the folder of sketches the console may start (default examples)")
    listing = commands.add_parser("runs", help="list the runs in a folder, newest first, with how each ended",
                                  description="List the runs in a folder, newest first, with the sketch and how each ended.")
    listing.add_argument("folder", type=Path, nargs="?", default=DEFAULT_OUT, help="the folder of runs (default build/runs)")
    run = commands.choices["run"]
    run.add_argument("--out", type=Path, default=DEFAULT_OUT, metavar="FOLDER",
                     help="the folder to make the run's folder in (default build/runs)")
    run.add_argument("--replay", nargs="?", const="", default=None, metavar="RUN-ID|DIR",
                     help="read the captured Jev answers of a run or folder instead of calling Jev (no key, no network)")
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
    stdout=None, stderr=None,
) -> int:
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    args = _parser().parse_args(argv)
    if args.command == "dashboard":
        return _dashboard(args, stdout, stderr)
    if args.command == "runs":
        return _runs(args, stdout)

    def fail(message: str, code: int) -> int:
        stderr.write(f"understudy: {message}\n")
        return code

    try:
        sketch = load_checked(args.sketch, _overrides(args.source), _values(args.values))
    except SketchError as error:
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
    try:
        stages = registered() if library is None else library
        result = asyncio.run(run_sketch(sketch, args.out, stages, lambda line: stdout.write(line + "\n"), capture))
    except OutputPathError as error:
        return fail(str(error), 2)
    except Exception as error:
        return fail(str(error) or type(error).__name__, 1)
    stdout.write(f"run: {result.directory.name}\nwatch it: understudy dashboard {args.out}\n")
    for path in result.outputs.values():  # the outputs and the outcome stay last: scripts read the last line
        stdout.write(f"wrote {path}\n")
    if result.outcome:
        stdout.write(f"outcome: {result.outcome}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
