import tempfile
import unittest
from pathlib import Path

from src.paths import ROOT, OutputPathError, check_writable


class DestinationPolicyTests(unittest.TestCase):
    def test_private_output_is_refused_in_data_and_tracked_folders(self):
        for refused in (ROOT / "data" / "run", ROOT / "tests", ROOT / "docs" / "new-run"):
            with self.subTest(refused=refused), self.assertRaisesRegex(OutputPathError, "cannot write"):
                check_writable(refused)

    def test_ignored_and_outside_folders_pass(self):
        check_writable(ROOT / "build" / "runs")
        check_writable(ROOT / ".understudy" / "cache")
        with tempfile.TemporaryDirectory() as directory:
            check_writable(Path(directory) / "outside")

    def test_a_symlink_into_a_tracked_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "link"
            link.symlink_to(ROOT / "src")
            with self.assertRaisesRegex(OutputPathError, "cannot write"):
                check_writable(link / "run")

    def test_a_file_is_not_a_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "file"
            target.write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(OutputPathError, "not a directory"):
                check_writable(target)


if __name__ == "__main__":
    unittest.main()
