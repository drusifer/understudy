"""The owner's decide trees and weights.

A tree is `if` / `then` / `else` over conditions; a leaf is `drink`, a list of weighted rows:

    drink:
      - { temp: iced, size: large,  weight: 0.5 }
      - { temp: hot,  size: medium, weight: 0.5 }

A weight is a number, or the same `if` / `then` / `else` (no expression language, ADR-0044).
"""

from src.play.blend import Distribution, Opinion, Policy, blend, check_sums, forbid, shortlist
from src.play.conditions import holds


def leaf_rows(tree: dict, row: dict) -> list[dict]:
    """The weighted rows of the leaf this input row reaches; none when no branch applies."""
    node = tree
    while "drink" not in node:
        node = node["then"] if holds(node["if"], row) else node.get("else")
        if node is None:
            return []
    return [dict(item) for item in node["drink"]]


def weight_of(weight, row: dict) -> float:
    """A weight evaluated for one input row; an `if` with no matching branch and no `else` is 0."""
    while isinstance(weight, dict):
        weight = weight["then"] if holds(weight["if"], row) else weight.get("else", 0)
    return float(weight)


def decide_input(
    state: dict, row: dict, deciders: dict[str, list[dict]], *, allowed: dict | None = None, story: list | None = None,
) -> Distribution:
    """The weights per dimension for one input row, from a `blend` stage's entries and `forbid` rules.

    `state` is the stage as written; `deciders` holds the rows each named decider (a subsketch) returned. A list
    given as `story` gets one entry per dimension: its options with their final weight (0.0 when removed), what
    removed each, the pick and the pick's weight.
    """
    opinions = [
        Opinion(
            weight_of(entry.get("weight", 1), row),
            leaf_rows(entry["decide"], row) if "decide" in entry else deciders[entry["from"]],
        )
        for entry in state["blend"]
    ]
    label = f"{row.get('segment', 'the input row')}"
    policy = Policy(state.get("on_empty", "fail"), allowed)
    mixed = blend(opinions)
    removed: dict = {}
    result = forbid(mixed, state.get("forbid", []), row, label, policy, removed)
    if "shortlist" in state:
        result = shortlist(result, state["shortlist"], removed)
    check_sums(result)
    if story is not None:
        for dimension, options in result.items():
            pick = max(options, key=options.get)
            story.append({
                "dimension": dimension, "pick": pick, "probability": round(options[pick], 6),
                "options": [{"name": name, "weight": round(options.get(name, 0.0), 6),
                             "removed_by": removed.get((dimension, name))}
                            for name in mixed.get(dimension, options)],
            })
    return result
