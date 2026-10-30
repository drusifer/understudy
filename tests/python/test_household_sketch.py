import io
import json
import tempfile
import unittest
from pathlib import Path

from test_controller import jev

from src.paths import ROOT
from src.sketch.cli import main
from src.sketch.sources.capture import CaptureStore

HOUSEHOLD = ROOT / "examples" / "household" / "household.yaml"
ORACLE = ROOT / "tests" / "fixtures" / "etl" / "household"


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class HouseholdSketchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        directory = Path(cls.temporary.name)
        stdout, stderr = io.StringIO(), io.StringIO()
        cls.code = main(
            ["run", str(HOUSEHOLD), "--out", str(directory / "out"),
             "--with", f"monarch={ORACLE / 'monarch.csv'}", "--with", f"amex={ORACLE / 'amex.csv'}"],
            make_jev=jev, store=CaptureStore(directory / "cache"), stdout=stdout, stderr=stderr)
        cls.stderr = stderr.getvalue()
        (cls.folder,) = (directory / "out").iterdir()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_the_sketch_runs_to_its_final_state(self):
        self.assertEqual((self.code, json.loads((self.folder / "run.json").read_text())["status"]), (0, "complete"), self.stderr)

    def test_the_records_are_the_etls_records(self):
        self.assertEqual(lines(self.folder / "result.jsonl"), lines(ORACLE / "expected" / "result.jsonl"))

    def test_the_summary_numbers_are_the_etls_numbers(self):
        expected = json.loads((ORACLE / "expected" / "summary.json").read_text())
        found = json.loads((self.folder / "summary.json").read_text())
        self.assertEqual({key: found[key] for key in expected}, expected)
