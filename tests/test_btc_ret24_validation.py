import importlib.util
import pathlib
import unittest


_VALIDATE_PATH = pathlib.Path(__file__).parents[1] / "factors" / "btc-ret24-entry-gate" / "validate.py"
_SPEC = importlib.util.spec_from_file_location("btc_ret24_validate", _VALIDATE_PATH)
validate = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(validate)


class BtcRet24ValidationTests(unittest.TestCase):
    def test_trade_stats_uses_profit_factor_definition(self):
        rows = [
            {"profit_ratio": 0.02},
            {"profit_ratio": 0.01},
            {"profit_ratio": -0.01},
        ]
        result = validate.trade_stats(rows)
        self.assertEqual(result["n"], 3)
        self.assertAlmostEqual(result["win_rate"], 2 / 3)
        self.assertAlmostEqual(result["profit_factor"], 3.0)

    def test_comparison_keeps_branch_specific_threshold(self):
        rows = [
            {"enter_tag": "short_new", "btc_ret_24h": 0.02, "profit_ratio": 0.01, "day": "2025-01-01", "accepted": True},
            {"enter_tag": "short_new", "btc_ret_24h": 0.00, "profit_ratio": -0.01, "day": "2025-01-02", "accepted": False},
        ]
        result = validate.comparison(rows, "2025", "short_new")
        self.assertAlmostEqual(result["threshold"], validate.THRESHOLDS["short_new"])
        self.assertAlmostEqual(result["delta_mean_return"], 0.02)

    def test_bootstrap_is_reproducible(self):
        accepted = [{"profit_ratio": 0.01, "day": "2025-01-01", "accepted": True}]
        blocked = [{"profit_ratio": -0.01, "day": "2025-01-02", "accepted": False}]
        first = validate.bootstrap_delta(accepted, blocked)
        second = validate.bootstrap_delta(accepted, blocked)
        self.assertEqual(first, second)
        self.assertAlmostEqual(first["median"], 0.02)


if __name__ == "__main__":
    unittest.main()
