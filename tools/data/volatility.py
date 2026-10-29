"""Rolling sample standard deviation of simple returns; not annualized."""

from math import isfinite
from statistics import stdev


def volatility(prices, window):
    """Return rolling return standard deviation aligned with input prices."""
    if not isinstance(window, int) or isinstance(window, bool) or window < 2:
        raise ValueError("window must be an integer of at least two returns")
    values = list(prices)
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not isfinite(x) or x <= 0 for x in values):
        raise ValueError("prices must be positive finite numbers")
    returns = [values[i] / values[i-1] - 1 for i in range(1, len(values))]
    return [None if i < window else stdev(returns[i-window:i]) for i in range(len(values))]
