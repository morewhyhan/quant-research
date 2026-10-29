import importlib.util
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


momentum = load("momentum", "tools/data/momentum.py")
volatility = load("volatility", "tools/data/volatility.py")


class ResearchBasics(unittest.TestCase):
    def test_momentum_window_and_zero_price(self):
        result = momentum.momentum([100, 110, 99], 1)
        self.assertIsNone(result[0])
        self.assertAlmostEqual(result[1], 0.1)
        self.assertAlmostEqual(result[2], -0.1)
        with self.assertRaises(ValueError):
            momentum.momentum([100, 0], 1)

    def test_volatility_sample_and_warmup(self):
        result = volatility.volatility([100, 110, 99], 2)
        self.assertEqual(result[:2], [None, None])
        self.assertAlmostEqual(result[2], math.sqrt(0.02))

if __name__ == "__main__":
    unittest.main()
