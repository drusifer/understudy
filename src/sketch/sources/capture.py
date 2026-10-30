"""Capture and replay for every non-file source (ADR-0043).

A live read is captured, after it completed, under `.understudy/cache/<run-id>/`:

    <sketch>.<source>.jsonl        the rows
    <sketch>.<source>.meta.json    run id, source, request hash, captured at

`--replay` reads those captures instead of going live, and never falls back to live. It uses one run: the
latest that captured every non-file source (or a named run, or a folder of captures such as the committed
test fixtures), so every source comes from the same moment. The last few runs are kept.
"""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from src.paths import ROOT
from src.sketch.sources.file import read_jsonl

CACHE = ROOT / ".understudy" / "cache"
KEEP = 5


class ReplayError(Exception):
    """A replay cannot start; the message says which source has no capture and what to do."""


class CaptureStore:
    def __init__(self, root: Path = CACHE, keep: int = KEEP):
        self.root, self.keep = Path(root), keep

    def run_dir(self, run_id: str) -> Path:
        return self.root / run_id

    def runs(self) -> list[str]:
        """Saved runs, newest first (run ids start with their timestamp)."""
        return sorted((p.name for p in self.root.iterdir() if p.is_dir()), reverse=True) if self.root.is_dir() else []

    def write(self, run_id: str, key: str, rows: list[dict], request_hash: str) -> None:
        directory = self.run_dir(run_id)
        directory.mkdir(parents=True, exist_ok=True)
        lines = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        (directory / f"{key}.jsonl").write_text(lines, encoding="utf-8")
        meta = {"run_id": run_id, "source": key, "request_hash": request_hash,
                "captured_at": datetime.now(UTC).isoformat(timespec="seconds")}
        (directory / f"{key}.meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    def prune(self) -> None:
        """Keep the newest few runs, dropped together so the samples stay in step."""
        for run_id in self.runs()[self.keep:]:
            shutil.rmtree(self.run_dir(run_id))


def has_capture(directory: Path, key: str) -> bool:
    return (directory / f"{key}.jsonl").is_file() and (directory / f"{key}.meta.json").is_file()


def read_capture(directory: Path, key: str) -> tuple[list[dict], dict]:
    return read_jsonl(directory / f"{key}.jsonl"), json.loads((directory / f"{key}.meta.json").read_text(encoding="utf-8"))


def _missing(directory: Path, keys: list[str]) -> list[str]:
    return [key for key in keys if not has_capture(directory, key)]


def choose_replay(store: CaptureStore, target: str | None, keys: list[str]) -> Path:
    """The folder a replay reads: a named folder, a named run, or the latest run that covers every key."""
    if target:
        folder = Path(target)
        directory = folder if folder.is_dir() else store.run_dir(target)
        if not directory.is_dir():
            raise ReplayError(f"no capture named {target!r}: it is neither a folder nor a saved run")
        missing = _missing(directory, keys)
        if missing:
            raise ReplayError(f"{directory} has no capture of {', '.join(missing)}; do a live run first")
        return directory
    for run_id in store.runs():
        if not _missing(store.run_dir(run_id), keys):
            return store.run_dir(run_id)
    latest = store.runs()
    missing = _missing(store.run_dir(latest[0]), keys) if latest else keys
    raise ReplayError(f"no saved run captured {', '.join(missing)}; do a live run first")
