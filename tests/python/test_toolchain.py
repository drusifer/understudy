import unittest

import duckdb

import sqlmesh


class ToolchainTest(unittest.TestCase):
    def test_pinned_elt_dependencies_import(self):
        self.assertEqual(duckdb.__version__, "1.5.6")
        self.assertEqual(sqlmesh.__version__, "0.236.3")


if __name__ == "__main__":
    unittest.main()
