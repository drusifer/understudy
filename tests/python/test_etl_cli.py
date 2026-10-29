import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.etl.cli import main
from src.etl.controller import _check_writable, EtlError, ROOT
from src.etl.jev import JevError
from test_controller import Files


class CliTests(unittest.TestCase):
    def test_output_in_a_tracked_source_directory_is_refused_without_starting_the_controller(self):
        # UND-54 AC4 forbids publishing private output inside tracked source folders.
        # The controller is stubbed so this regression never writes into the source tree.
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch("src.etl.cli.run", new_callable=AsyncMock, return_value={"directory": "unused"}) as controller:
                code = main(["--monarch", str(files.monarch), "--amex", str(files.amex), "--out", str(ROOT / "src")],
                            make_jev=object, stdout=stdout, stderr=stderr)
            self.assertEqual(code, 2, "private run output must not be accepted under tracked src/")
            controller.assert_not_awaited()
            self.assertEqual(stdout.getvalue(), "")

    def test_destination_policy_boundaries(self):
        for refused in (ROOT / "data" / "run", ROOT / "tests", ROOT / "docs" / "new-run"):
            with self.subTest(refused=refused), self.assertRaisesRegex(EtlError, "cannot write"):
                _check_writable(refused)
        _check_writable(ROOT / "build" / "runs")
        with tempfile.TemporaryDirectory() as directory:
            _check_writable(Path(directory) / "outside")
            link = Path(directory) / "link"
            link.symlink_to(ROOT / "src")
            with self.assertRaisesRegex(EtlError, "cannot write"):
                _check_writable(link / "run")

    def test_options_reach_the_controller_and_success_is_json(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            stdout, stderr = io.StringIO(), io.StringIO()
            answer = {"directory": str(files.out / "run-example"), "summary": {"records": 12}}
            service = object()
            with patch("src.etl.cli.run", new_callable=AsyncMock, return_value=answer) as controller:
                code = main(["--monarch", str(files.monarch), "--amex", str(files.amex),
                             "--out", str(files.out), "--since", "2026-01-01", "--amex-account", "Platinum"],
                            make_jev=lambda: service, stdout=stdout, stderr=stderr)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue()), answer)
            self.assertEqual(stderr.getvalue(), "")
            options = controller.await_args.kwargs
            self.assertEqual((options["monarch"], options["amex"], options["out"]),
                             (files.monarch, files.amex, files.out))
            self.assertEqual((options["since"], options["amex_account"]), ("2026-01-01", "Platinum"))
            self.assertIs(options["jev"], service)

    def test_a_controller_failure_is_exit_one_with_one_actionable_error_line(self):
        with tempfile.TemporaryDirectory() as directory:
            files = Files(directory)
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch("src.etl.cli.run", new_callable=AsyncMock, side_effect=JevError("Jev unavailable")):
                code = main(["--monarch", str(files.monarch), "--amex", str(files.amex)],
                            make_jev=object, stdout=stdout, stderr=stderr)
            self.assertEqual(code, 1)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "understudy: Jev unavailable\n")

    @unittest.skipIf(os.geteuid() == 0, "root bypasses filesystem write permissions")
    def test_a_read_only_directory_is_refused_before_source_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "read-only"
            out.mkdir()
            out.chmod(0o555)
            try:
                with self.assertRaisesRegex(EtlError, "cannot write"):
                    _check_writable(out / "new-run-parent")
                with patch("src.etl.cli.describe", side_effect=AssertionError("source must not be read")):
                    stderr = io.StringIO()
                    code = main(["--monarch", "missing", "--amex", "missing", "--out", str(out)],
                                make_jev=lambda: self.fail("must refuse before creating Jev"), stderr=stderr)
                self.assertEqual(code, 2)
                self.assertIn("cannot write", stderr.getvalue())
                self.assertEqual(list(out.iterdir()), [])
            finally:
                out.chmod(0o755)

    def test_bad_date_is_refused_before_constructing_jev_or_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out"
            stderr = io.StringIO()
            code = main(["--monarch", "missing", "--amex", "missing", "--since", "bad", "--out", str(output)],
                        make_jev=lambda: self.fail("must refuse before creating Jev"), stderr=stderr)
            self.assertEqual(code, 2)
            self.assertFalse(output.exists())
            self.assertIn("Invalid isoformat", stderr.getvalue())

    def test_missing_input_is_refused_without_a_traceback(self):
        stderr = io.StringIO()
        code = main(["--monarch", "/missing-monarch.csv", "--amex", "/missing-amex.csv"],
                    make_jev=lambda: self.fail("must refuse before creating Jev"), stderr=stderr)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", stderr.getvalue())
