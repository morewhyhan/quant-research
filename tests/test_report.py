import importlib.util
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.report import monthly_returns


class ReportTests(unittest.TestCase):
    def test_monthly_returns_carries_balance_through_empty_month(self):
        rows = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc), 100.0, 0.0),
            (datetime(2024, 1, 15, tzinfo=timezone.utc), 110.0, 0.0),
            (datetime(2024, 3, 5, tzinfo=timezone.utc), 99.0, 0.0),
        ]
        values = monthly_returns(rows, 100.0)
        self.assertEqual([item['month'] for item in values], ['2024-01', '2024-02', '2024-03'])
        self.assertAlmostEqual(values[0]['return_ratio'], 0.10)
        self.assertAlmostEqual(values[1]['return_ratio'], 0.0)
        self.assertAlmostEqual(values[2]['return_ratio'], -0.10)

    @unittest.skipUnless(importlib.util.find_spec('matplotlib'), 'optional chart dependency not installed')
    def test_report_writes_html_and_evidence_files(self):
        from tools.performance.report import render
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'result.json'
            source.write_text(json.dumps({'strategy': {'Test': {
                'trades': [
                    {'profit_abs': 10.0, 'profit_ratio': 0.1, 'close_date': '2024-01-02T00:00:00Z',
                     'open_date': '2024-01-01T23:00:00Z', 'pair': 'AAA/USDT', 'is_short': False,
                     'exit_reason': 'take_profit', 'enter_tag': 'buy_1', 'stake_amount': 100.0},
                    {'profit_abs': -5.0, 'profit_ratio': -0.05, 'close_date': '2024-02-02T00:00:00Z',
                     'open_date': '2024-02-01T23:00:00Z', 'pair': 'AAA/USDT', 'is_short': False,
                     'exit_reason': 'stop_loss', 'enter_tag': 'buy_1', 'stake_amount': 100.0},
                ],
                'starting_balance': 100.0, 'final_balance': 105.0,
                'backtest_start': '2024-01-01T00:00:00Z', 'backtest_end': '2024-03-01T00:00:00Z',
                'profit_factor': 2.0, 'max_drawdown_account': 0.05,
                'stake_currency': 'USDT', 'stake_amount': 'unlimited',
            }}}, ensure_ascii=False), encoding='utf-8')
            output = root / 'report'
            render([source], output, ['Test'], ['Test'], [100.0], title='测试报告')
            self.assertTrue((output / 'report.html').is_file())
            self.assertTrue((output / 'manifest.json').is_file())
            self.assertTrue((output / 'curve-1.csv').is_file())
            self.assertIn('测试报告', (output / 'report.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
