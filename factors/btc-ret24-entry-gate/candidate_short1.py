"""Frozen research candidate: BTC strong-up regime for the ``short_1`` branch.

This candidate is deliberately separate from ``factor.py``.  It was selected
from the predeclared 2024 quantile grid for a future forward / paper-trading
test.  It is not connected to any live strategy.
"""

from __future__ import annotations

from typing import Optional


# 70th percentile of short_1 BTC 24h returns in the 2024 calibration archive.
# Keep this value frozen for the next forward test; do not tune it on forward data.
SHORT_1_BTC_RET24_THRESHOLD = 0.004153278554082939


def accepts_short1_regime(enter_tag: str, btc_ret_24h: Optional[float]) -> bool:
    """Gate only ``short_1`` signals; leave other branches unchanged."""

    if enter_tag != "short_1":
        return True
    if btc_ret_24h is None:
        return False
    return btc_ret_24h >= SHORT_1_BTC_RET24_THRESHOLD
