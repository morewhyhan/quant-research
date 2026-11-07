import importlib.util
import pathlib
import unittest


_FACTOR_PATH = pathlib.Path(__file__).parents[1] / "factors" / "btc-ret24-entry-gate" / "factor.py"
_SPEC = importlib.util.spec_from_file_location("btc_ret24_factor", _FACTOR_PATH)
factor = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(factor)

_CANDIDATE_PATH = pathlib.Path(__file__).parents[1] / "factors" / "btc-ret24-entry-gate" / "candidate_short1.py"
_CANDIDATE_SPEC = importlib.util.spec_from_file_location("btc_ret24_short1_candidate", _CANDIDATE_PATH)
candidate = importlib.util.module_from_spec(_CANDIDATE_SPEC)
assert _CANDIDATE_SPEC.loader is not None
_CANDIDATE_SPEC.loader.exec_module(candidate)


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

    def test_short1_candidate_is_branch_specific_and_frozen(self):
        threshold = candidate.SHORT_1_BTC_RET24_THRESHOLD
        self.assertTrue(candidate.accepts_short1_regime("short_1", threshold))
        self.assertFalse(candidate.accepts_short1_regime("short_1", threshold - 1e-9))
        self.assertFalse(candidate.accepts_short1_regime("short_1", None))
        self.assertTrue(candidate.accepts_short1_regime("short_new", None))


if __name__ == "__main__":
    unittest.main()
