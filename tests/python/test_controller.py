import asyncio
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from jev_double import JevDouble

from src.etl.controller import run
from src.etl.sources import SourceError
from src.jev import Chosen, JevError
from src.paths import OutputPathError

MONARCH_HEADER = "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags,Owner,Reviewed,Id\n"
CARD, CHECKING = "Platinum Card (...1111)", "Checking (...2222)"


def monarch_row(date, merchant, category, account, amount, ident):
    return f'{date},{merchant},"{category}",{account},{merchant.upper()},,{amount},,Me,,{ident}\n'


MONARCH = MONARCH_HEADER + "".join([
    monarch_row("2025-12-30", "Old Shop", "Restaurant-Restaurant", CARD, "40.00", "m0"),
    monarch_row("2026-02-01", "Store", "Shopping & Retail: General", CARD, "-50.00", "m1"),
    monarch_row("2026-02-15", "Store", "Shopping & Retail: General", CARD, "-45.00", "m2"),
    monarch_row("2026-03-01", "Shoe Shop", "Shopping & Retail: Clothing", CARD, "-30.00", "m3"),
    monarch_row("2026-03-05", "Dunkin'", "Food & Dining: Coffee & Cafes", CARD, "-4.50", "m4"),
    monarch_row("2026-03-06", "Dunkin'", "Food & Dining: Coffee & Cafes", CARD, "-6.70", "m5"),
    monarch_row("2026-03-10", "Shoe Shop", "Shopping & Retail: Clothing", CARD, "30.00", "m6"),
    monarch_row("2026-03-12", "Store", "Shopping & Retail: General", CARD, "45.00", "m7"),
    monarch_row("2026-03-02", "Payment Thank You", "Credit Card Payment", CARD, "500.00", "m8"),
    monarch_row("2026-03-01", "Amex Payment", "Credit Card Payment", CHECKING, "-500.00", "m9"),
    monarch_row("2026-03-04", "Venmo", "Transportation: Transfers", CHECKING, "-600.00", "m10"),
    monarch_row("2026-03-03", "Ridgewood Savings Bank", "Transfer", CHECKING, "-70.00", "m11"),
    monarch_row("2026-03-05", "Employer", "Income: Paychecks", CHECKING, "2000.00", "m12"),
])
AMEX_HEADER = "Date,Description,Card Member,Account #,Amount,Extended Details,Appears On Your Statement As,Reference,Category\n"
AMEX = AMEX_HEADER + "".join(f"{d},{desc},A PERSON,-11111,{amt},,{desc},r{i},Cat\n" for i, (d, desc, amt) in enumerate([
    ("02/01/2026", "STORE", "50.00"), ("02/15/2026", "STORE", "45.00"), ("03/01/2026", "SHOE SHOP", "30.00"),
    ("03/05/2026", "DUNKIN'", "4.50"), ("03/10/2026", "SHOE SHOP", "-30.00"), ("03/12/2026", "STORE", "-45.00"),
    ("03/02/2026", "ELECTRONIC PAYMENT RECEIVED-THANK YOU", "-500.00")]))

WIRE = "Wire transfers and money orders"
FITS = {"Store": 0.9, "Shoe Shop": 0.5, "Dunkin'": 0.95, "Employer": 0.99, "Venmo": 0.05}
CATEGORY = {"Store": "Shopping & Retail: General", "Dunkin'": "Food & Dining: Coffee & Cafes", "Employer": "Income: Paychecks"}
PAYEES = {"Venmo": 0.05, "Ridgewood Savings Bank": 0.93}


def jev(fail=None):
    def noul(state, name, spec):
        if "payee" in state:
            return PAYEES[state["payee"]]
        if name == "fits":
            return FITS[state["merchant"]]
        return 0.9  # the naming rubric passes

    def choice(state, name, spec):
        if name == "category":
            pick = CATEGORY.get(state["merchant"], next(iter(spec.options)))
            return Chosen(pick, 0.8, {pick: 0.8})
        if name == "group":
            return Chosen("Utilities", 0.7, {"Utilities": 0.7})
        if name == "name":
            return Chosen(WIRE, 0.7, {WIRE: 0.7})
        raise AssertionError(name)

    def decide(state, instructions, yes, no):
        return PAYEES[state["payee"]]

    def choose(state, instructions, options):
        pick = "charged_2026-02-15_45.00"
        assert pick in options, options
        return Chosen(pick, 0.8, {pick: 0.8})

    return JevDouble(choice_fn=choice, noul_fn=noul, choose_fn=choose, decide_fn=decide, fail=fail)


class Files:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.monarch = self.directory / "monarch.csv"
        self.amex = self.directory / "amex.csv"
        self.out = self.directory / "out"
        self.monarch.write_text(MONARCH, encoding="utf-8")
        self.amex.write_text(AMEX, encoding="utf-8")


def go(files, double=None, **options):
    return asyncio.run(run(monarch=files.monarch, amex=files.amex, out=files.out, jev=double or jev(),
                           announce=lambda message: None, **options))


def records(result):
    return [json.loads(line) for line in Path(result["directory"], "result.jsonl").read_text().splitlines()]


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.files = Files(cls.temporary.name)
        cls.result = go(cls.files)
        cls.records = {r["record_id"]: r for r in records(cls.result)}
        cls.summary = json.loads(Path(cls.result["directory"], "summary.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def kinds(self):
        counts = {}
        for record in self.records.values():
            counts[record["kind"]] = counts.get(record["kind"], 0) + 1
        return counts

    def test_the_result_is_one_jsonl_record_per_transaction_in_the_period(self):
        self.assertEqual(len(self.records), 12)  # 13 Monarch rows less the one before the period, 7 Amex rows merged in
        self.assertNotIn("m0", {r["source_rows"]["monarch"]["Id"] for r in self.records.values()
                                if r["source_rows"]["monarch"] is not None})

    def test_every_kind_is_found(self):
        self.assertEqual(self.kinds(), {"purchase": 6, "transfer": 2, "external_transfer": 1, "refund": 2, "credit": 1})

    def test_a_purchase_in_both_files_is_one_record_with_both_source_rows(self):
        paired = [r for r in self.records.values() if r["match_status"] == "paired" and r["merchant"] == "Dunkin'"]
        self.assertEqual(len(paired), 1)
        self.assertIsNotNone(paired[0]["source_rows"]["monarch"])
        self.assertIsNotNone(paired[0]["source_rows"]["amex"])
        self.assertEqual(paired[0]["category_confidence"], 0.8)
        single = next(r for r in self.records.values() if r["merchant"] == "Dunkin'" and r["match_status"] == "monarch_only")
        self.assertIsNone(single["source_rows"]["amex"])

    def test_the_card_payment_is_a_transfer_linked_to_the_checking_debit_and_kept(self):
        legs = [r for r in self.records.values() if r["kind"] == "transfer"]
        self.assertEqual({r["merchant"] for r in legs}, {"Payment Thank You", "Amex Payment"})
        self.assertEqual({r["transfer_partner_id"] for r in legs}, {r["record_id"] for r in legs})

    def test_venmo_is_spending_and_gets_an_mcc_named_category_a_savings_payee_is_an_external_transfer(self):
        venmo = next(r for r in self.records.values() if r["merchant"] == "Venmo")
        self.assertEqual((venmo["kind"], venmo["category"], venmo["category_source"]), ("purchase", WIRE, "new"))
        savings = next(r for r in self.records.values() if r["merchant"] == "Ridgewood Savings Bank")
        self.assertEqual((savings["kind"], savings["category"]), ("external_transfer", None))

    def test_refunds_link_to_their_originals_one_by_rule_one_by_jev(self):
        refunds = {r["merchant"]: r for r in self.records.values() if r["kind"] == "refund"}
        self.assertEqual(refunds["Shoe Shop"]["refund_link_status"], "single")
        self.assertEqual(refunds["Store"]["refund_link_status"], "chosen")
        original = self.records[refunds["Store"]["refund_original_id"]]
        self.assertEqual((original["amount"], original["transaction_date"]), (-45.0, "2026-02-15"))
        self.assertEqual(refunds["Store"]["refund_confidence"], 0.8)

    def test_an_unsure_merchant_goes_to_review_without_a_category(self):
        shoes = [r for r in self.records.values() if r["merchant"] == "Shoe Shop" and r["kind"] == "purchase"]
        self.assertEqual((shoes[0]["category"], shoes[0]["category_status"]), (None, "review"))

    def test_the_summary_counts_without_naming_transactions(self):
        s = self.summary
        self.assertEqual(s["sources"]["monarch"]["rows_before_period"], 1)
        self.assertEqual(s["records"], 12)
        self.assertEqual(s["transfers"]["paired_legs"], 2)
        self.assertEqual(s["transfers"]["paired_leg_amount"], 1000)
        self.assertEqual(s["net_spending"], 661.2)
        self.assertEqual(s["transfers"]["external"], {"Ridgewood Savings Bank": 1})
        self.assertEqual(s["refunds"], {"single": 1, "chosen": 1, "unlinked": 0, "no_original": 0})
        self.assertEqual([c["category"] for c in s["categories"]["new"]], [WIRE])
        self.assertGreater(s["jev"]["requests"], 0)
        self.assertNotIn("Amex Payment", json.dumps(s))

    def test_a_rerun_with_the_same_files_and_answers_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            files.out = Path(os.path.relpath(files.out))
            again = go(files)
            for name in ("result.jsonl", "summary.json"):
                self.assertEqual(Path(again["directory"], name).read_bytes(), Path(self.result["directory"], name).read_bytes())


class FailureTests(unittest.TestCase):
    def test_an_output_stage_failure_removes_the_staged_result(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            with patch("src.etl.controller._summary", side_effect=RuntimeError("summary failed")):
                with self.assertRaisesRegex(RuntimeError, "summary failed"):
                    go(files)
            (run_dir,) = files.out.iterdir()
            for name in ("result.jsonl", "result.jsonl.part", "summary.json"):
                self.assertFalse((run_dir / name).exists())
            self.assertEqual(json.loads((run_dir / "run.json").read_text())["failed_stage"], "output")

    def test_a_jev_failure_stops_the_run_and_leaves_no_result(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            with self.assertRaises(JevError):
                go(files, double=jev(fail=JevError("Jev could not be reached")))
            runs = list(files.out.iterdir())
            self.assertEqual(len(runs), 1)
            self.assertFalse((runs[0] / "result.jsonl").exists())
            self.assertFalse((runs[0] / "summary.json").exists())
            self.assertEqual(json.loads((runs[0] / "run.json").read_text())["status"], "failed")

    def test_a_missing_file_stops_before_anything_is_created(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            files.amex.unlink()
            with self.assertRaises(SourceError):
                go(files)
            self.assertFalse(files.out.exists())

    def test_an_output_path_that_cannot_be_written_is_refused_before_reading_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            files.out.write_text("not a directory")
            with self.assertRaises(OutputPathError) as caught:
                go(files)
            self.assertIn("cannot write", str(caught.exception))


class ScaleTests(unittest.TestCase):
    def test_4700_pairs_reuse_one_merchant_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            files.monarch.write_text(MONARCH_HEADER + "".join(
                monarch_row("2026-02-01", "Store", "Shopping & Retail: General", CARD, f"-{i}.00", f"m{i}")
                for i in range(1, 4701)), encoding="utf-8")
            files.amex.write_text(AMEX_HEADER + "".join(
                f"02/01/2026,STORE,A PERSON,-11111,{i}.00,,STORE,r{i},Cat\n"
                for i in range(1, 4701)), encoding="utf-8")
            started = time.monotonic()
            result = go(files)
            self.assertEqual(len(records(result)), 4700)
            self.assertEqual(result["summary"]["purchases_merged"], 4700)
            self.assertEqual(result["summary"]["jev"], {"requests": 1, "category_decisions_reused": 4699})
            print(f"Synthetic 4,700-pair controller run: {time.monotonic() - started:.2f}s")


if __name__ == "__main__":
    unittest.main()
