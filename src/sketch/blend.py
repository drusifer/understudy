"""Blend deciders, then apply the owner's hard rules (ADR-0041).

Each decider answers with weighted rows over some dimensions (a row names the dimensions it has an opinion
on). The blend works per dimension: the weighted average of the deciders that name that dimension, weights
normalised. `forbid` then drops options and renormalises, and always wins over a preference.
"""

from dataclasses import dataclass

from src.sketch.conditions import holds

Distribution = dict[str, dict[str, float]]  # dimension -> option -> weight; each dimension sums to 1
TOLERANCE = 1e-9


class EmptyResultError(Exception):
    """A forbid rule left an input row with no option in a dimension; the message names the rule and the row."""


@dataclass(frozen=True)
class Opinion:
    """One decider's rows for one input row, and the weight the sketch gives that decider."""

    weight: float
    rows: list[dict]


@dataclass(frozen=True)
class Policy:
    """What happens when a forbid rule empties a dimension: `fail`, `skip` it, or `fallback` to spread
    over the `allowed` options (dimension -> options) that the rule does not drop."""

    on_empty: str = "fail"
    allowed: dict | None = None


def _normalised(options: dict[str, float]) -> dict[str, float]:
    """The options with weight, scaled to add up to 1; empty when none has weight."""
    live = {option: weight for option, weight in options.items() if weight > 0}
    total = sum(live.values())
    return {option: weight / total for option, weight in live.items()}


def marginals(rows: list[dict]) -> Distribution:
    """Per dimension, each option's share of the rows that name the dimension."""
    totals: Distribution = {}
    for row in rows:
        for dimension, option in row.items():
            if dimension != "weight":
                bucket = totals.setdefault(dimension, {})
                bucket[option] = bucket.get(option, 0.0) + row["weight"]
    shares = {dimension: _normalised(options) for dimension, options in totals.items()}
    return {dimension: options for dimension, options in shares.items() if options}


def blend(opinions: list[Opinion]) -> Distribution:
    """The weighted average per dimension across the deciders that name it; a weight of 0 means no say."""
    mixed: Distribution = {}
    named: dict[str, float] = {}
    for opinion in opinions:
        if opinion.weight <= 0:
            continue
        for dimension, options in marginals(opinion.rows).items():
            named[dimension] = named.get(dimension, 0.0) + opinion.weight
            bucket = mixed.setdefault(dimension, {})
            for option, share in options.items():
                bucket[option] = bucket.get(option, 0.0) + opinion.weight * share
    return {d: {o: w / named[d] for o, w in options.items()} for d, options in mixed.items()}


def forbid(distribution: Distribution, rules: list[dict], row: dict, label: str, policy: Policy | None = None) -> Distribution:
    """Drop the options each matching rule forbids and renormalise."""
    policy = policy or Policy()
    result = {d: dict(options) for d, options in distribution.items()}
    for index, rule in enumerate(rules):
        if not holds(rule["when"], row):
            continue
        for dimension in list(result):
            kept = _normalised({o: w for o, w in result[dimension].items() if not holds(rule["drop"], {dimension: o})})
            if kept:
                result[dimension] = kept
            else:
                where = f"forbid rule {index} left {label} with no option for {dimension!r}"
                result = _emptied(result, dimension, rule, policy, where)
    return result


def _emptied(result: Distribution, dimension: str, rule: dict, policy: Policy, where: str) -> Distribution:
    if policy.on_empty == "skip":
        return {d: o for d, o in result.items() if d != dimension}
    if policy.on_empty == "fallback":
        options = [o for o in (policy.allowed or {}).get(dimension, ()) if not holds(rule["drop"], {dimension: o})]
        if options:
            return {**result, dimension: {o: 1 / len(options) for o in options}}
    raise EmptyResultError(where)


def shortlist(distribution: Distribution, best: int) -> Distribution:
    """Keep each dimension's `best` heaviest options (ties keep their order) and renormalise."""
    return {
        dimension: _normalised(dict(sorted(options.items(), key=lambda item: -item[1])[:best]))
        for dimension, options in distribution.items()
    }


def check_sums(distribution: Distribution) -> None:
    """The invariant: every dimension's weights add up to 1."""
    for dimension, options in distribution.items():
        total = sum(options.values())
        if abs(total - 1) > TOLERANCE:
            raise ValueError(f"weights for {dimension!r} add up to {total}, not 1")
