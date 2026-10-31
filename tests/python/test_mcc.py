import unittest

from src.sketch.mcc import MccError, load_mcc


class MccListTests(unittest.TestCase):
    def test_groups_hold_the_iso_descriptions_and_leave_out_the_reserved_codes(self):
        groups = load_mcc()
        self.assertNotIn("Reserved for private use", groups)
        self.assertGreaterEqual(len(groups), 10)
        self.assertIn("Groceries and supermarkets", groups["Retail outlets"])
        self.assertTrue(all(names == sorted(set(names)) for names in groups.values()))

    def test_every_group_has_a_name_to_offer(self):
        self.assertTrue(all(load_mcc().values()))

    def test_an_unreadable_list_stops_with_a_message_about_the_mcc_list(self):
        def broken():
            raise OSError("data file missing")

        with self.assertRaises(MccError) as caught:
            load_mcc(get_all=broken)
        self.assertIn("MCC list cannot be read", str(caught.exception))
        self.assertIn("data file missing", str(caught.exception))

    def test_an_empty_list_is_refused(self):
        with self.assertRaises(MccError):
            load_mcc(get_all=lambda: [])


if __name__ == "__main__":
    unittest.main()
