import unittest

import duckdb


class ToolchainTest(unittest.TestCase):
    def test_pinned_dependencies_import(self):
        self.assertEqual(duckdb.__version__, "1.5.6")


if __name__ == "__main__":
    unittest.main()
