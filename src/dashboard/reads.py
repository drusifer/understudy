"""The Jev list: what Jev was asked in a run and how sure it was, from the run's captured answers (UND-78).

A capture holds, for each read, the levels and their probabilities and (since Sprint 22) the rubric's question; the text
Jev read is never stored, only hashed, so nothing private can appear here. Captures are kept for the last few live runs
only; a replayed run reads the capture folder it replayed, named in its `run.json` as `replay_of`.
"""

import json
from pathlib import Path

from src.dashboard.view import read_json
from src.paths import ROOT

REVIEW_THRESHOLD = 0.7  # a read whose top level is below this is flagged for the owner (the household's own rule)
NONE_LEVEL = "none_of_these"


def _capture_dir(directory: Path, run: dict, cache: Path, project: Path) -> Path | None:
    """The folder holding this run's captures: its own (live) or the one it replayed (inside the project only)."""
    if run.get("mode") == "replay":
        folder = (project / str(run.get("replay_of", "?"))).resolve()
        return folder if folder.is_relative_to(project.resolve()) and folder.is_dir() else None
    folder = cache / directory.name
    return folder if folder.is_dir() else None


def _hide_names(rows: list[dict]) -> list[dict]:
    """Level names that came from the owner's data (a charge named by its date and amount) are shown as `option N`; the
    sketch's own `none_of_these` keeps its name so a flag still makes sense (SEC-007)."""
    return [row if row["level"] == NONE_LEVEL else {**row, "level": f"option {number}"} for number, row in enumerate(rows, 1)]


def _one_read(folder: Path, key: str) -> dict:
    rows = [json.loads(line) for line in (folder / f"{key}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    meta = json.loads((folder / f"{key}.meta.json").read_text(encoding="utf-8"))
    if meta.get("levels_from_data") is not False:  # data-derived, or a capture too old to say: do not send the names
        rows = _hide_names(rows)
    ranked = sorted(rows, key=lambda row: row["probability"], reverse=True)
    top = ranked[0] if ranked else {"level": "", "probability": 0.0}
    second = ranked[1]["probability"] if len(ranked) > 1 else 0.0
    return {
        "source": key, "levels": [[row["level"], row["probability"]] for row in rows], "top": top["level"],
        "probability": top["probability"], "margin": top["probability"] - second,
        "flagged": top["probability"] < REVIEW_THRESHOLD or top["level"] == NONE_LEVEL,
        "instructions": meta.get("instructions"), "captured_at": meta.get("captured_at", ""),
    }


def jev_reads(directory: Path, cache: Path, project: Path = ROOT) -> dict:
    """The reads of one run, and the two figures the gauges need: the last read's confidence and asked against reused."""
    run, summary = read_json(directory / "run.json"), read_json(directory / "summary.json")
    folder = _capture_dir(directory, run, cache, project)
    if folder is None:
        asked = int(summary.get("jev_requests", 0))
        note = "captures no longer kept for this run" if asked or run.get("mode") == "replay" else "this run did not ask Jev"
        return {"kept": False, "note": note, "reads": [], "missing": [], "confidence": None, "asked": asked, "reused": 0}
    jsonl = {path.name.removesuffix(".jsonl") for path in folder.glob("*.jsonl")}
    metas = {path.name.removesuffix(".meta.json") for path in folder.glob("*.meta.json")}
    reads = sorted((_one_read(folder, key) for key in jsonl & metas), key=lambda read: (read["captured_at"], read["source"]))
    replayed = run.get("mode") == "replay"
    return {
        "kept": True, "note": "", "reads": reads, "missing": sorted(jsonl ^ metas),
        "confidence": reads[-1]["probability"] if reads else None,
        "asked": 0 if replayed else int(summary.get("jev_requests", len(reads))), "reused": len(reads) if replayed else 0,
    }
