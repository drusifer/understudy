"""`understudy run <sketch.yaml>` and `understudy check <sketch.yaml>`.

Exit codes: 0 done, 1 a stage failed after the run started, 2 refused before starting. Every failure ends with
one `understudy: <message>` line saying what to fix; there is never a traceback.
"""

import argparse
import asyncio
import sys
from collections.abc import Mapping
from pathlib import Path

import src.sketch.stages  # noqa: F401 - importing it registers the stages
from src.jev import JevError, TypeSafeJev
from src.paths import OutputPathError
from src.sketch.check import load_checked
from src.sketch.loader import SketchError
from src.sketch.registry import StageFn
from src.sketch.registry import library as registered
from src.sketch.run import run_sketch
from src.sketch.sources.capture import CaptureStore, ReplayError
from src.sketch.sources.reader import Capture, jev_keys

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
        values[name] = value
    return values


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="understudy")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "check"):
        command = commands.add_parser(name)
        command.add_argument("sketch", type=Path)
        command.add_argument("--source", action="append", default=[], metavar="NAME.path=FILE")
        command.add_argument("--with", action="append", default=[], metavar="NAME=VALUE", dest="values")
    run = commands.choices["run"]
    run.add_argument("--out", type=Path, default=DEFAULT_OUT)
    run.add_argument("--replay", nargs="?", const="", default=None, metavar="RUN-ID|DIR")
    return parser


def _capture(args, sketch, store, make_jev) -> Capture:
    if args.replay is not None:
        return Capture.replay(store, sketch, args.replay or None)
    return Capture.live(store, make_jev() if jev_keys(sketch) else None)


def main(  # noqa: PLR0913 - the command line's injection points
    argv=None, *, library: Mapping[str, StageFn] | None = None, make_jev=TypeSafeJev, store: CaptureStore | None = None,
    stdout=None, stderr=None,
) -> int:
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    args = _parser().parse_args(argv)

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
    for path in result.outputs.values():
        stdout.write(f"wrote {path}\n")
    if result.outcome:
        stdout.write(f"outcome: {result.outcome}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
