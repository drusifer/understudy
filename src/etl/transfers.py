"""Unpaired transfer candidates (UND-51): is the payee one of the owner's own accounts?

A transfer is money moving between the owner's own bank and card accounts. A payment to a person,
to a payment app such as Venmo or Zelle, or to a merchant is spending, whatever Monarch labelled
it (owner, 2026-10-27). That is a judgment about the payee, so Jev makes it, once per distinct payee.
"""

import asyncio

from src.etl.jev import Jev, JevError

CONCURRENCY = 8
EXTERNAL_ABOVE = 0.7
SPENDING_BELOW = 0.3

INSTRUCTIONS = (
    "Is `payee` an account at one of the owner's own banks or card issuers, "
    "so that the money stays with the owner?"
)
YES = "The payee is a bank, card issuer or account the owner holds, such as one that shares an institution with an entry in `owner_accounts`."
NO = "The payee is a person, a payment app such as Venmo or Zelle, or a merchant, so the money has left the owner."


def _key(merchant: str) -> str:
    return " ".join(merchant.lower().split())


def _decision(probability: float) -> str:
    if probability > EXTERNAL_ABOVE:
        return "external_transfer"
    if probability < SPENDING_BELOW:
        return "spending"
    return "review"


async def _judge(payee: str, records: list[dict], owner_accounts: list[str], jev: Jev, gate: asyncio.Semaphore) -> dict:
    state = {
        "payee": payee,
        "owner_accounts": owner_accounts,
        "payments": {
            "money_out": sum(1 for r in records if r["amount"] < 0),
            "money_in": sum(1 for r in records if r["amount"] > 0),
            "example_amounts": [r["amount"] for r in records[:3]],
        },
    }
    async with gate:
        probability = await jev.decide(state=state, instructions=INSTRUCTIONS, yes=YES, no=NO)
    return {
        "payee_key": _key(payee),
        "payee": payee,
        "decision": _decision(probability),
        "probability": probability,
        "records": len(records),
    }


async def judge_payees(rows: list[dict], owner_accounts: list[str], jev: Jev) -> list[dict]:
    """One decision per distinct payee among the unpaired transfer candidates in `rows`.

    The state Jev sees is the payee, the owner's account names (without numbers) and how many
    payments went each way; Monarch's category label is left out on purpose, since it is the thing
    being doubted.
    """
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(_key(row["merchant"]), []).append(row)
    gate = asyncio.Semaphore(CONCURRENCY)
    tasks = [
        asyncio.ensure_future(_judge(records[0]["merchant"].strip(), records, owner_accounts, jev, gate))
        for _, records in sorted(grouped.items())
    ]
    try:
        return [await task for task in tasks]
    except JevError as error:
        for task in tasks:
            task.cancel()
        raise JevError(f"the transfer payees stage failed: {error}") from error
