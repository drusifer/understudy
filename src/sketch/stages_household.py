"""The household ETL as stages: each step of `src.etl.controller.Household` is a `map` stage a sketch can name.

The steps share one run folder (rows live in its DuckDB file), so the first stage, `map.hydrate`, makes the run's
`Household` and the later ones find it by the folder. Jev comes from the run, like any source's.
"""

from pathlib import Path

from src.etl.controller import Household
from src.sketch.registry import stage

RUNS: dict[Path, Household] = {}


def _household(context) -> Household:
    return RUNS[context.directory]


@stage("map.hydrate")
async def hydrate(context, monarch: str, amex: str, amex_account: str | None = None, since: str | None = None) -> list[dict]:
    """Read the Monarch and Amex exports into JSONL snapshots in the run folder; starts the household run."""
    (context.directory / "inputs").mkdir(exist_ok=True)
    RUNS[context.directory] = Household(
        monarch=Path(monarch), amex=Path(amex), directory=context.directory, jev=context.sources.capture.jev,
        amex_account=amex_account, since=since, announce=context.sources.announce)
    await _household(context).hydrate()
    return []


@stage("map.pair")
async def pair(context) -> list[dict]:
    """Find the period and the Amex card, then pair purchases and transfer legs (SQL)."""
    await _household(context).pair()
    return []


@stage("map.judge_transfers", jev=True)
async def judge_transfers(context) -> list[dict]:
    """Jev judges the payee of each unpaired transfer candidate: Venmo and Zelle are spending."""
    await _household(context).transfers()
    return []


@stage("map.plan_spending")
async def plan_spending(context) -> list[dict]:
    """List the refunds, the merchants and the categories on offer (SQL)."""
    await _household(context).plan_spending()
    return []


@stage("map.link_refunds", jev=True)
async def link_refunds(context) -> list[dict]:
    """Jev chooses the original charge where a refund has several."""
    await _household(context).refunds()
    return []


@stage("map.place_merchants", jev=True)
async def place_merchants(context) -> list[dict]:
    """Jev places each merchant in a category, naming a new one from the MCC list when none fits."""
    await _household(context).categories()
    return []


@stage("map.publish")
async def publish(context) -> list[dict]:
    """Run the final SQL and write `result.jsonl`; the summary's counts go to the run's summary."""
    household = _household(context)
    await household.output()
    context.summary.update(household.facts["summary"])
    return []
