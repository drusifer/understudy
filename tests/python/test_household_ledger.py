import io
import json
import tempfile
import unittest
from pathlib import Path

from src.paths import ROOT
from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

LEDGER = ROOT / "examples" / "household" / "ledger.yaml"
ORACLE = ROOT / "tests" / "fixtures" / "etl" / "household"


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        directory = Path(cls.temporary.name)
        stderr = io.StringIO()
        cls.code = main(
            ["run", str(LEDGER), "--out", str(directory / "out"), "--with", f"monarch={ORACLE / 'monarch.csv'}",
             "--with", f"amex={ORACLE / 'amex.csv'}", "--with", "amex_account=Platinum", "--with", "since=2026-01-01"],
            store=CaptureStore(directory / "cache"), stdout=io.StringIO(), stderr=stderr)
        cls.stderr = stderr.getvalue()
        (folder,) = (directory / "out").iterdir()
        cls.records = lines(folder / "records.jsonl")
        cls.legs = {leg["record_id"]: leg for leg in lines(folder / "legs.jsonl")}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_it_runs(self):
        self.assertEqual((self.code, self.stderr), (0, ""))

    def test_a_charge_in_both_exports_is_one_record_and_the_period_leaves_out_the_old_row(self):
        self.assertEqual(len(self.records), 12)  # the oracle's count: 13 Monarch rows less 1 before the period, 7 Amex merged in
        self.assertEqual(sum(r["match"] == "paired" for r in self.records), 7)
        self.assertNotIn("Old Shop", {r["payee"] for r in self.records})

    def test_the_card_payment_links_to_the_checking_debit(self):
        self.assertEqual((self.legs["m9"]["partner"], self.legs["m10"]["partner"]), ("m10", "m9"))

    def test_venmo_and_the_savings_bank_are_unpaired_transfer_candidates(self):
        unpaired = {leg["payee"] for leg in self.legs.values() if leg["partner"] is None}
        self.assertEqual(unpaired, {"Venmo", "Ridgewood Savings Bank"})


if __name__ == "__main__":
    unittest.main()
