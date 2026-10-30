"""Refunds and their originals (UND-52): Jev chooses only when more than one charge could be it."""

import asyncio

from src.jev import GatedJev, Jev, JevError

CONCURRENCY = 8
INSTRUCTIONS = (
    "Which of these earlier charges did `refund` most likely reverse? "
    "Each option is one charge from the same merchant."
)


def _group(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["refund_id"], []).append(row)
    return grouped


def _options(candidates: list[dict]) -> dict[str, dict]:
    """Option name per candidate: descriptive, and unique even for two identical charges."""
    named: dict[str, dict] = {}
    for candidate in candidates:
        name = f"charged_{candidate['candidate_date']}_{abs(candidate['candidate_amount']):.2f}"
        suffix = 2
        unique = name
        while unique in named:
            unique, suffix = f"{name}_{suffix}", suffix + 1
        named[unique] = candidate
    return named


async def _choose(refund_id: str, rows: list[dict], jev: Jev) -> dict:
    named = _options(rows)
    first = rows[0]
    state = {"refund": {"merchant": first["merchant"], "date": str(first["refund_date"]), "amount": first["refund_amount"]}}
    options = {
        name: f"The charge of {abs(candidate['candidate_amount']):.2f} on {candidate['candidate_date']}."
        for name, candidate in named.items()
    }
    chosen = await jev.choose(state=state, instructions=INSTRUCTIONS, options=options)
    if chosen.option not in named:
        return {"refund_id": refund_id, "candidate_id": None, "status": "off_list", "confidence": None}
    return {
        "refund_id": refund_id,
        "candidate_id": named[chosen.option]["candidate_id"],
        "status": "chosen",
        "confidence": chosen.confidence,
    }


async def decide_refunds(rows: list[dict], jev: Jev) -> list[dict]:
    """One decision per refund, in the order the rows arrive.

    `rows` are the refund_candidates rows. A refund with one original links without asking, one with
    none is marked, and one with several is put to Jev as a Choice among the listed originals; an
    answer that is not one of them links nothing.
    """
    gated = GatedJev(jev, CONCURRENCY)
    grouped = _group(rows)
    tasks: dict[str, asyncio.Task] = {}
    try:
        for refund_id, candidates in grouped.items():
            if candidates[0]["link_status"] == "needs_choice":
                tasks[refund_id] = asyncio.ensure_future(_choose(refund_id, candidates, gated))
        results = {refund_id: await task for refund_id, task in tasks.items()}
    except JevError as error:
        for task in tasks.values():
            task.cancel()
        raise JevError(f"the refund originals stage failed: {error}") from error
    decisions = []
    for refund_id, candidates in grouped.items():
        status = candidates[0]["link_status"]
        if status == "needs_choice":
            decisions.append(results[refund_id])
        elif status == "single":
            decisions.append({"refund_id": refund_id, "candidate_id": candidates[0]["candidate_id"],
                              "status": "single", "confidence": None})
        else:
            decisions.append({"refund_id": refund_id, "candidate_id": None, "status": "no_original", "confidence": None})
    return decisions
