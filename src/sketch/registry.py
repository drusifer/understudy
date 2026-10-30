"""Stages register themselves here, and the signature of the function is the contract of the YAML.

    @stage("etl.split_by_share")
    async def split_by_share(context, source: Source, field: str, segments: Data) -> list[dict]: ...

declares the stage `etl.split_by_share` that a sketch writes as

    do: etl.split_by_share
    with: { source: sales, field: drinks, segments: segments }

Each parameter is a `with:` key; a parameter with no default is required. Its annotation says what the value is:
`Source` names a source of the sketch, `Data` names a key under `data`, and `str`, `int` or `float` is a plain value.
`understudy check` reads the same signature, so the file and the code cannot disagree.
"""

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

StageFn = Callable[..., Awaitable]


class Source(str):
    """A `with:` value that names one of the sketch's sources."""


class Data(str):
    """A `with:` value that names a key under the sketch's `data`."""


@dataclass(frozen=True)
class Param:
    """One `with:` key of a stage: what its value must be, and whether the sketch must give it."""

    kind: type
    required: bool


@dataclass(frozen=True)
class Stage:
    name: str
    run: StageFn
    params: dict[str, Param]


STAGES: dict[str, Stage] = {}


def describe(name: str, run: StageFn) -> Stage:
    """The stage a function declares: its parameters after `context`, by name, annotation and default."""
    params = {}
    for parameter in list(inspect.signature(run).parameters.values())[1:]:
        kind = parameter.annotation if parameter.annotation is not inspect.Parameter.empty else str
        params[parameter.name] = Param(kind, parameter.default is inspect.Parameter.empty)
    return Stage(name, run, params)


def library() -> dict[str, StageFn]:
    """Every registered stage's function, by name."""
    return {name: registered.run for name, registered in STAGES.items()}


def stage(name: str) -> Callable[[StageFn], StageFn]:
    """Register the decorated function as the stage `name`."""
    def register(run: StageFn) -> StageFn:
        STAGES[name] = describe(name, run)
        return run
    return register
