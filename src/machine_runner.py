"""Run a python-statemachine: the one loop the ETL and the sketches share.

The machine decides which stage runs next. Each state names a stage; the loop runs it, sends `ok`, and the
machine's own guards pick the next state. A failed stage tries a `fail` event (the ETL machine has one),
records the failure, removes anything a failed run must not leave behind, and raises.
"""

import json
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import suppress
from pathlib import Path

from statemachine.exceptions import TransitionNotAllowed


class RunRecord:
    """What a run says about itself: stage lines on the console and `run.json` in its folder."""

    def __init__(self, directory: Path, announce: Callable[[str], None] = print, cleanup: Iterable[str] = (), **facts):
        self.directory, self.announce, self.cleanup = directory, announce, tuple(cleanup)
        self.manifest: dict = {"status": "running", "stages": {}, **facts}

    def save(self) -> None:
        (self.directory / "run.json").write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")

    def started(self, name: str) -> None:
        self.announce(f"stage {name}")

    def completed(self, name: str) -> None:
        self.manifest["stages"][name] = "complete"
        self.save()

    def failed(self, name: str, error: Exception) -> None:
        for output in self.cleanup:
            (self.directory / output).unlink(missing_ok=True)
        self.manifest.update(status="failed", failed_stage=name, error=str(error))
        self.save()

    def finished(self, outcome: str | None = None) -> None:
        self.manifest["status"] = "complete"
        if outcome:
            self.manifest["outcome"] = outcome
        self.save()


def current_state(machine) -> str:
    return next(iter(machine.configuration)).id


async def run_machine(
    machine, stages: Mapping[str, Callable[[], Awaitable]], record: RunRecord, publish: Callable[[], None] | None = None,
    outcomes: Mapping[str, str] | None = None,
) -> None:
    """Walk `machine` from its initial state to a final one, running the stage each state names.

    `publish` runs once the machine has ended and before the run is recorded as complete; if it fails, so does the run.
    `outcomes` names what a final state means (`outcome:` in the sketch); the run records the one it ended in.
    """
    while not machine.is_terminated:
        name = current_state(machine)
        if name not in stages:
            raise LookupError(f"the machine enters state {name!r} but no stage is defined for it")
        record.started(name)
        try:
            result = await stages[name]()
        except Exception as error:
            with suppress(TransitionNotAllowed):
                machine.send("fail")
            record.failed(name, error)
            raise
        machine.model.result = result
        machine.send("ok")
        record.completed(name)
    try:
        if publish:
            publish()
    except Exception as error:
        record.failed("publish", error)
        raise
    record.finished((outcomes or {}).get(current_state(machine)))
