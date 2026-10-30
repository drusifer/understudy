"""The ETL controller: the stages in order, each gated on the one before (stages.yaml).

hydrate    page each export from its source server into a JSONL snapshot
pair       find the period and the Amex card, run the SQL that pairs purchases and transfer legs
transfers  Jev judges the payee of each unpaired transfer candidate (Venmo and Zelle are spending)
plan_spending  run the SQL that lists refunds, merchants and the offered categories
refunds    Jev chooses the original charge where there are several
categories Jev places each merchant, naming a new category from the MCC list when none fits
output     run the final SQL, write result.jsonl and summary.json

A failed stage stops the run; nothing is published as a result. Rows live in DuckDB, the rules are
SQL (SQLMesh), and Jev only judges (ADR-0038).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
from statemachine.io import load

from src.etl import sources
from src.etl.categorize import place_merchants
from src.etl.decisions import store
from src.etl.hydrate import hydrate
from src.etl.mcc import load_mcc
from src.etl.pairing import detect_amex_account, first_date
from src.etl.refunds import decide_refunds
from src.etl.transfers import judge_payees
from src.jev import GatedJev
from src.machine_runner import RunRecord, run_machine
from src.paths import ROOT, check_writable

SQLMESH = Path(sys.executable).parent / "sqlmesh"
MACHINE = load(Path(__file__).with_name("stages.yaml"))

TRANSFER_JUDGMENT = {"payee_key": "VARCHAR", "payee": "VARCHAR", "decision": "VARCHAR", "probability": "DOUBLE"}
REFUND_CHOICE = {"refund_id": "VARCHAR", "candidate_id": "VARCHAR", "status": "VARCHAR", "confidence": "DOUBLE"}
MERCHANT_CATEGORY = {
    "merchant_key": "VARCHAR", "merchant": "VARCHAR", "category": "VARCHAR", "source": "VARCHAR",
    "status": "VARCHAR", "fit_probability": "DOUBLE", "confidence": "DOUBLE", "suggestion": "VARCHAR",
}
NEW_CATEGORY = {
    "category": "VARCHAR", "mcc_group": "VARCHAR", "rubric_probability": "DOUBLE", "merchants": "BIGINT", "records": "BIGINT",
}


class EtlError(Exception):
    """The run cannot continue; the message says why."""


def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _mask(name: str) -> str:
    """An account name without its number."""
    return re.sub(r"\s*\(\.\.\.\d+\)", "", name).strip()


class _Run:
    """One run: its folder, its database and what the stages hand to each other."""

    def __init__(self, directory: Path, announce):
        self.directory = directory
        self.database = directory / "run.duckdb"
        self.project = directory / "sqlmesh"
        self.environment = {**os.environ, "UNDERSTUDY_ETL_DATABASE": str(self.database)}
        self.record = RunRecord(directory, announce, cleanup=("result.jsonl", "result.jsonl.part", "summary.json"))

    def rows(self, sql: str) -> list[dict]:
        with duckdb.connect(str(self.database), read_only=True) as connection:
            cursor = connection.execute(sql)
            names = [column[0] for column in cursor.description]
            return [{n: _plain(v) for n, v in zip(names, row, strict=True)} for row in cursor.fetchall()]

    def write(self, table: str, columns: dict, rows: list[dict]) -> None:
        with duckdb.connect(str(self.database)) as connection:
            store(connection, table, columns, rows)

    def plan(self, *selects: str) -> None:
        # Model fixtures run separately via test-etl, with their synthetic account and period.
        command = [str(SQLMESH), "plan", "dev", "--auto-apply", "--skip-tests"]
        for select in selects:
            command += ["--select-model", select]
        result = subprocess.run(command, cwd=self.project, env=self.environment, capture_output=True, text=True, check=False)
        with (self.directory / "sqlmesh.log").open("a", encoding="utf-8") as log:
            log.write(f"=== {' '.join(selects)}\n{result.stdout}\n{result.stderr}\n")
        if result.returncode:
            raise EtlError(f"SQLMesh failed for {', '.join(selects)}; see {self.directory / 'sqlmesh.log'}")


class Household:
    """One household run: the two exports, the run folder and what each step hands the next. The steps are methods,
    run in order by `run` here and as stages by the household sketch (`src/sketch/stages_household.py`)."""

    def __init__(self, *, monarch: Path, amex: Path, directory: Path, jev, amex_account: str | None = None,  # noqa: PLR0913
                 since: str | None = None, announce=print):
        self.monarch, self.amex = Path(monarch), Path(amex)
        self.amex_account, self.since, self.announce = amex_account, since, announce
        self.state, self.gated = _Run(directory, announce), GatedJev(jev)
        self.monarch_jsonl, self.amex_jsonl = directory / "inputs" / "monarch.jsonl", directory / "inputs" / "amex.jsonl"
        self.found: dict = {}
        self.facts: dict = {}

    async def hydrate(self):
        await hydrate("monarch", self.monarch, self.monarch_jsonl)
        await hydrate("amex", self.amex, self.amex_jsonl)

    async def pair(self):
        state, found = self.state, self.found
        start = self.since or first_date(self.amex_jsonl)
        if start is None:
            raise EtlError("the Amex file has no dated rows, so there is no period to run")
        self.facts["period_start"] = start
        found.update(detect_amex_account(self.monarch_jsonl, self.amex_jsonl, override=self.amex_account, since=start))
        shutil.copytree(ROOT / "sqlmesh", state.project, ignore=shutil.ignore_patterns("logs", ".cache", "*.pyc"))
        state.environment.update(
            UNDERSTUDY_ETL_MONARCH_JSONL=str(self.monarch_jsonl), UNDERSTUDY_ETL_AMEX_JSONL=str(self.amex_jsonl),
            UNDERSTUDY_ETL_AMEX_ACCOUNT=found["account"], UNDERSTUDY_ETL_PERIOD_START=start)
        with duckdb.connect(str(state.database)) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS etl__dev")
            store(connection, "etl__dev.transfer_judgment", TRANSFER_JUDGMENT, [])
            store(connection, "etl__dev.refund_choice", REFUND_CHOICE, [])
            store(connection, "etl__dev.merchant_category", MERCHANT_CATEGORY, [])
        state.plan("+etl.transfer_pairs", "etl.period_scope")

    async def transfers(self):
        state = self.state
        unpaired = state.rows("""SELECT record_id, transaction_date, amount, merchant, account
                                 FROM etl__dev.transfer_pairs WHERE transfer_status = 'unpaired' ORDER BY record_id""")
        accounts = sorted({_mask(r["account"]) for r in state.rows(
            "SELECT DISTINCT account FROM etl__dev.raw_monarch WHERE account IS NOT NULL")})
        self.facts["transfer_decisions"] = await judge_payees(unpaired, accounts, self.gated)
        state.write("etl__dev.transfer_judgment", TRANSFER_JUDGMENT, [
            {k: d[k] for k in TRANSFER_JUDGMENT} for d in self.facts["transfer_decisions"]])

    async def plan_spending(self):
        self.state.plan("+etl.refund_candidates", "+etl.merchant_candidates", "etl.offered_categories")

    async def refunds(self):
        state = self.state
        needing = state.rows("""SELECT * FROM etl__dev.refund_candidates WHERE link_status = 'needs_choice'
                                ORDER BY refund_date, refund_id, candidate_rank""")
        self.facts["refund_decisions"] = await decide_refunds(needing, self.gated)
        state.write("etl__dev.refund_choice", REFUND_CHOICE, self.facts["refund_decisions"])

    async def categories(self):
        state = self.state
        mcc = load_mcc()  # stops here, before any naming, when the list cannot be read
        merchants = state.rows("SELECT * FROM etl__dev.merchant_candidates ORDER BY merchant_key")
        categories = [r["category"] for r in state.rows("SELECT category FROM etl__dev.offered_categories ORDER BY category")]
        self.facts["placement"] = await place_merchants(merchants, categories, self.gated, mcc, announce=self.announce)
        state.write("etl__dev.merchant_category", MERCHANT_CATEGORY, [
            {k: p[k] for k in MERCHANT_CATEGORY} for p in self.facts["placement"]["placements"]])
        state.write("etl__dev.new_category", NEW_CATEGORY, [
            {k: c[k] for k in NEW_CATEGORY} for c in self.facts["placement"]["new_categories"]])

    async def output(self):
        self.facts["summary"] = _publish(self.state, self.facts, self.found, self.gated)


async def run(*, monarch: Path, amex: Path, out: Path, jev, amex_account: str | None = None,  # noqa: PLR0913 - keyword-only entry point
              since: str | None = None, announce=print) -> dict:
    """Run the ETL over the two exports and return {"directory": <run folder>, "summary": {...}}."""
    out = Path(out).resolve()
    check_writable(out)
    for source, path in (("monarch", monarch), ("amex", amex)):
        sources.describe(Path(path), source)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    run_dir = out / f"run-{stamp}-{uuid.uuid4().hex[:8]}"
    (run_dir / "inputs").mkdir(parents=True)
    household = Household(monarch=monarch, amex=amex, directory=run_dir, jev=jev, amex_account=amex_account,
                          since=since, announce=announce)
    stages = {name: getattr(household, name) for name in
              ("hydrate", "pair", "transfers", "plan_spending", "refunds", "categories", "output")}
    await run_machine(MACHINE(), stages, household.state.record)
    return {"directory": str(run_dir), "summary": household.facts["summary"]}


def _publish(state: _Run, facts: dict, found: dict, gated: GatedJev) -> dict:
    """Run the final SQL, then write summary.json and result.jsonl (the last step, so a failure publishes no result)."""
    state.plan("+etl.final_records")
    partial = state.directory / "result.jsonl.part"
    _copy_result(state, partial)
    summary = _summary(state, facts, found, gated)
    (state.directory / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    partial.replace(state.directory / "result.jsonl")
    return summary


def _copy_result(state: _Run, destination: Path) -> None:
    """Write the final records as JSONL in a fixed order, so a repeat run is byte-identical."""
    destination_sql = str(destination).replace("'", "''")
    with duckdb.connect(str(state.database)) as connection:
        connection.execute(f"""COPY (
          SELECT f.record_id, transaction_date, amount, f.merchant, account, kind, transfer_partner_id,
                 refund_original_id, refund_link_status, f.category, category_source, category_status,
                 match_status, pair_method,
                 CASE WHEN kind IN ('purchase', 'refund', 'credit') THEN m.confidence END AS category_confidence,
                 CASE WHEN refund_link_status = 'chosen' THEN r.confidence END AS refund_confidence,
                 {{'monarch': TRY_CAST(monarch_raw AS JSON), 'amex': TRY_CAST(amex_raw AS JSON)}} AS source_rows
          FROM etl__dev.final_records AS f
          LEFT JOIN etl__dev.merchant_category AS m
            ON m.merchant_key = regexp_replace(lower(trim(f.merchant)), '\\s+', ' ', 'g')
          LEFT JOIN etl__dev.refund_choice AS r ON r.refund_id = f.record_id
          ORDER BY transaction_date NULLS LAST, f.record_id
        ) TO '{destination_sql}' (FORMAT JSON)""")


def _summary(state: _Run, facts: dict, found: dict, gated: GatedJev) -> dict:
    """Counts only: no transaction text, no account numbers."""
    count = lambda sql: {r["k"]: r["n"] for r in state.rows(sql)}  # noqa: E731
    scope = {r["source"]: {k: r[k] for k in ("rows_read", "rows_in_period", "rows_before_period", "rows_without_date")}
             for r in state.rows("SELECT * FROM etl__dev.period_scope")}
    kinds = count("SELECT kind AS k, count(*) AS n FROM etl__dev.final_records GROUP BY 1")
    pairing = count("SELECT match_status AS k, count(*) AS n FROM etl__dev.purchase_pairs GROUP BY 1")
    refunds = count("SELECT refund_link_status AS k, count(*) AS n FROM etl__dev.final_records "
                    "WHERE kind = 'refund' GROUP BY 1")
    statuses = count("SELECT category_status AS k, count(*) AS n FROM etl__dev.final_records "
                     "WHERE category_status IS NOT NULL GROUP BY 1")
    by_decision: dict[str, dict[str, int]] = {"external_transfer": {}, "spending": {}, "review": {}}
    for d in facts["transfer_decisions"]:
        by_decision[d["decision"]][d["payee"]] = d["records"]
    placement = facts["placement"]
    placed = sum(1 for p in placement["placements"] if p["status"] == "placed")
    money = state.rows("""SELECT
        coalesce(-sum(amount) FILTER (WHERE kind IN ('purchase', 'refund')), 0) AS net_spending,
        coalesce(sum(abs(amount)) FILTER (WHERE kind = 'transfer'), 0) AS paired_leg_amount,
        coalesce(sum(abs(amount)) FILTER (WHERE kind = 'external_transfer'), 0) AS external_amount
        FROM etl__dev.final_records""")[0]
    candidate_totals = {r["decision"]: {"records": r["records"], "amount": r["amount"]} for r in state.rows("""
        SELECT j.decision, count(*) AS records, sum(abs(t.amount)) AS amount
        FROM etl__dev.transfer_pairs AS t JOIN etl__dev.transfer_judgment AS j
          ON j.payee_key = regexp_replace(lower(trim(t.merchant)), '\\s+', ' ', 'g')
        WHERE t.transfer_status = 'unpaired' GROUP BY j.decision""")}
    return {
        "period": {"start": facts["period_start"], "amex_account": found["source"]},
        "sources": scope,
        "records": sum(kinds.values()),
        "net_spending": money["net_spending"],
        "kinds": dict(sorted(kinds.items())),
        "purchases_merged": pairing.get("paired", 0),
        "transfers": {
            "paired_legs": kinds.get("transfer", 0),
            "paired_leg_amount": money["paired_leg_amount"],
            "external_amount": money["external_amount"],
            "candidate_totals": candidate_totals,
            "external": by_decision["external_transfer"],
            "judged_spending": by_decision["spending"],
            "for_review": by_decision["review"],
        },
        "refunds": {k: refunds.get(k, 0) for k in ("single", "chosen", "unlinked", "no_original")},
        "categories": {
            "merchants_asked": len(placement["placements"]),
            "merchants_placed": placed,
            "merchants_for_review": len(placement["placements"]) - placed,
            "records_by_status": dict(sorted(statuses.items())),
            "new": [{k: c[k] for k in ("category", "mcc_group", "merchants", "records")}
                    for c in placement["new_categories"]],
        },
        "jev": {
            "requests": gated.requests,
            "category_decisions_reused": placement["records_covered"] - len(placement["placements"]),
        },
        "review": {
            "unpaired_amex_rows": pairing.get("amex_only", 0),
            "unpaired_monarch_rows": pairing.get("monarch_only", 0),
            "invalid_rows": pairing.get("invalid_key", 0),
            "refunds_unlinked": refunds.get("unlinked", 0),
        },
    }
