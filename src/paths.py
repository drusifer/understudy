"""Where understudy writes: the project root and the one rule for private output.

Private output (real transactions, captures of real sources) stays out of tracked folders and
`data/`; ignored folders such as `build/` and paths outside the project are fine.
"""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OutputPathError(Exception):
    """The output folder cannot be used; the message says why."""


def _check_destination_policy(out: Path) -> None:
    resolved = out.resolve()
    if not resolved.is_relative_to(ROOT):
        return
    if resolved.is_relative_to(ROOT / "data"):
        raise OutputPathError(f"cannot write to {out}: private output does not belong in data/")
    ignored = subprocess.run(["git", "check-ignore", "-q", str(resolved)], cwd=ROOT, check=False).returncode == 0
    if not ignored:
        raise OutputPathError(
            f"cannot write to {out}: it is inside the project and not git-ignored (use build/ or a path outside)")


def check_writable(out: Path) -> None:
    """Refuse before reading anything when the run could not be written, changing nothing."""
    if out.exists() and not out.is_dir():
        raise OutputPathError(f"cannot write to {out}: it is not a directory")
    _check_destination_policy(out)
    nearest = out
    while not nearest.exists():
        nearest = nearest.parent
    if not nearest.is_dir() or not os.access(nearest, os.W_OK):
        raise OutputPathError(f"cannot write to {out}")
