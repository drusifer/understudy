"""A `kind: jev` source: a rubric and the data Jev reads go in, a probability per level comes out.

`instructions` and `criteria` (level -> what it means) are the rubric Jev reads; `state` is a plain dict built
from other sources. Reading the source returns one row per level, in the rubric's order: {level, probability}.
Jev only chooses among the levels the sketch lists (ADR-0013).
"""

import hashlib
import json


def request(config: dict, state: dict) -> dict:
    """Everything Jev is asked, so a capture can tell whether the sketch or rubric changed since."""
    return {"instructions": config["instructions"], "criteria": dict(config["criteria"]), "state": state}


def request_hash(asked: dict) -> str:
    return hashlib.sha256(json.dumps(asked, sort_keys=True).encode("utf-8")).hexdigest()


async def read_live(jev, config: dict, state: dict) -> list[dict]:
    chosen = await jev.choose(state=state, instructions=config["instructions"], options=dict(config["criteria"]))
    return [{"level": level, "probability": chosen.probabilities.get(level, 0.0)} for level in config["criteria"]]
