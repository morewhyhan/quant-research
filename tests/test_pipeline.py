import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.performance.metrics import trade_metrics, equity_metrics
from tools.live_comparison.matching import match_trades
from tools.data.time import timestamp
from tools.data.research_io import check_bars, read_result
from tools.engines.synthetic import signals, simulate
from tools.experiments.storage import save, verify


def trade(profit, minute=0):
    return {"pair": "X/Q", "is_short": False, "open_date": f"2024-01-01T00:{minute:02d}:00+00:00", "profit_abs": profit}


class PipelineTests(unittest.TestCase):
    def test_high_win_rate_negative_expectation(self):
        result = trade_metrics([trade(1)] * 9 + [trade(-12)])
        self.assertEqual(result["win_rate"], 0.9)
        self.assertEqual(result["profit_factor"], 0.75)
        self.assertEqual(result["mean_profit_abs"], -0.3)

    def test_no_losses_and_empty_pf_undefined(self):
        self.assertIsNone(trade_metrics([trade(1)])["profit_factor"])
        self.assertIsNone(trade_metrics([])["win_rate"])

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            trade_metrics([trade(float("nan"))])

    def test_equity_peak_drawdown(self):
        result = equity_metrics([100, 200, 100, 150])
        self.assertEqual(result["max_drawdown"], 0.5)
        self.assertEqual(result["total_return"], 0.5)

    def test_matching_is_one_to_one(self):
        result = match_trades([trade(1), trade(2)], [trade(3)])
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["unmatched_left"], 1)

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            timestamp("2024-01-01T00:00:00")

    def test_match_threshold(self):
        self.assertEqual(match_trades([trade(1)], [trade(1, 6)], 300)["matched"], 0)

    def test_ohlc_duplicate_and_bounds_rejected(self):
        bar = {"date": "2024-01-01T00:00:00Z", "open": 100, "close": 110, "high": 109, "low": 99}
        self.assertFalse(check_bars([bar])["valid"])
        bar["high"] = 111
        self.assertFalse(check_bars([bar, bar])["valid"])

    def test_signal_prefix_invariance(self):
        prices = [100, 110, 90, 120, 50]
        for end in range(1, len(prices)+1):
            self.assertEqual(signals(prices[:end], 1), signals(prices, 1)[:end])

    def test_next_open_execution_and_fees(self):
        prices = [100, 110, 121]
        bars = [{"date": f"2024-01-0{i+1}T00:00:00Z", "open": prices[i-1] if i else p,
                 "close": p, "high": p+1, "low": min(prices[i-1] if i else p, p)-1} for i,p in enumerate(prices)]
        result = simulate(bars, window=1, fee=0.01)
        self.assertEqual(result["trades"][0]["open_date"], bars[2]["date"])
        expected = 1000 / (110*1.01) * 121 * 0.99
        self.assertAlmostEqual(result["equity"][-1], expected)
        self.assertAlmostEqual(result["trades"][0]["profit_abs"], expected-1000)

    def test_zip_reader_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"result.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("results.json", json.dumps({"strategy": {"A": {"trades": [trade(1)]}, "B": {"trades": []}}}))
                z.writestr("results_config.json", "{}")
                z.writestr("untrusted_strategy.py", "raise RuntimeError('never executed')")
            with self.assertRaises(ValueError):
                read_result(path)
            self.assertEqual(len(read_result(path, "A")["trades"]), 1)

    def test_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                save(temp, {}, [])

    def test_artifact_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "experiment"
            save(output, {"test": True}, [])
            self.assertTrue(verify(output)["intact_against_current_files"])
            (output / "metrics.json").write_text("{}", encoding="utf-8")
            self.assertFalse(verify(output)["intact_against_current_files"])


if __name__ == "__main__":
    unittest.main()
