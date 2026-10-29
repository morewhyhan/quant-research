"""Historical simple price return; research example, not a trading signal."""

from math import isfinite


def momentum(prices, window):
    """Return current/lagged - 1, with None until window observations exist."""
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError("window must be a positive integer")
    values = list(prices)
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not isfinite(x) or x <= 0 for x in values):
        raise ValueError("prices must be positive finite numbers")
    return [None if i < window else values[i] / values[i-window] - 1 for i in range(len(values))]
