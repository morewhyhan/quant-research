import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.performance.charts import closed_curve


def result(trades, **extra):
    return {'strategy': 'Test', 'trades': trades, 'engine_reported': {
        'starting_balance': 100, 'backtest_start': '2024-01-01T00:00:00Z',
        'backtest_end': '2024-01-03T00:00:00Z', **extra}}


class ChartTests(unittest.TestCase):
    def test_simultaneous_closes_do_not_create_artificial_peak(self):
        rows, metrics = closed_curve(result([
            {'close_date': '2024-01-02T00:00:00Z', 'profit_abs': 100},
            {'close_date': '2024-01-02T00:00:00Z', 'profit_abs': -100}]))
        self.assertEqual(metrics['max_relative_drawdown'], 0)
        self.assertEqual(metrics['final'], 100)

    def test_drawdown_uses_initial_and_running_high(self):
        _, m = closed_curve(result([
            {'close_date': '2024-01-02T00:00:00Z', 'profit_abs': -20},
            {'close_date': '2024-01-03T00:00:00Z', 'profit_abs': 10}]))
        self.assertAlmostEqual(m['max_relative_drawdown'], .2)
        self.assertAlmostEqual(m['return_ratio'], -.1)

    def test_empty_and_open_results(self):
        _, m = closed_curve(result([]))
        self.assertEqual(m['return_ratio'], 0)
        with self.assertRaises(ValueError):
            closed_curve(result([{'is_open': True, 'profit_abs': 2}]))

    def test_reconciliation_must_not_silently_ignore_missing_pnl(self):
        with self.assertRaises(ValueError):
            closed_curve(result([], final_balance=110))

    def test_missing_initial_and_invalid_dates(self):
        r = result([])
        r['engine_reported'].pop('starting_balance')
        with self.assertRaises(ValueError):
            closed_curve(r)
        with self.assertRaises(ValueError):
            closed_curve(result([{'close_date': '2024-01-05T00:00:00Z', 'profit_abs': 1}]))

    def test_freqtrade_naive_metadata_is_interpreted_as_utc(self):
        rows, metrics = closed_curve(result([], backtest_start='2024-01-01 00:00:00',
                                             backtest_end='2024-01-02 00:00:00'))
        self.assertEqual(len(rows), 2)
        self.assertTrue(metrics['start'].endswith('+00:00'))

    def test_successful_engine_export_charts_only_this_run(self):
        from tools.engines.freqtrade.chart_run import run
        def fake_engine(args):
            directory = Path(args[args.index('--backtest-directory')+1])
            path = directory / 'backtest-result.json'
            r = result([])
            path.write_text(json.dumps({'strategy': {'Test': {
                **r['engine_reported'], 'trades': []}}}))
            return 0
        with tempfile.TemporaryDirectory() as temp:
            with patch('tools.engines.freqtrade.chart_run.run_engine', side_effect=fake_engine), patch('tools.performance.charts.render') as render:
                self.assertEqual(run(['backtesting'], Path(temp)/'run'), 0)
                self.assertEqual(render.call_count, 1)

    def test_failed_engine_never_creates_a_chart(self):
        from tools.engines.freqtrade.chart_run import run
        with tempfile.TemporaryDirectory() as temp:
            with patch('tools.engines.freqtrade.chart_run.run_engine', return_value=2), patch('tools.performance.charts.render') as render:
                self.assertEqual(run(['backtesting'], Path(temp)/'run'), 2)
                render.assert_not_called()
