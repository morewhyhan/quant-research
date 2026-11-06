import importlib.util
import pathlib
import unittest


_FACTOR_PATH = pathlib.Path(__file__).parents[1] / "factors" / "btc-ret24-entry-gate" / "factor.py"
_SPEC = importlib.util.spec_from_file_location("btc_ret24_factor", _FACTOR_PATH)
factor = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(factor)


class BtcRet24FactorTests(unittest.TestCase):
    def test_thresholds_are_branch_specific(self):
        self.assertAlmostEqual(factor.threshold_for("short_new"), 0.015405078725644741)
        self.assertAlmostEqual(factor.threshold_for("buy_1"), -0.030291256167492262)
        self.assertIsNone(factor.threshold_for("short_1"))

    def test_acceptance_is_fail_closed_only_for_gated_branches(self):
        self.assertTrue(factor.accepts("short_1", None))
        self.assertFalse(factor.accepts("short_new", None))
        self.assertFalse(factor.accepts("short_new", 0.0154))
        self.assertTrue(factor.accepts("short_new", 0.015405078725644741))
        self.assertTrue(factor.accepts("buy_1", -0.03))


if __name__ == "__main__":
    unittest.main()
