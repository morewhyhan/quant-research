"""Research definition of the BTC 24h environment candidate.

This module is intentionally independent from the live strategy. It records the
frozen research definition so that later experiments do not silently change the
factor while comparing results.
"""

from __future__ import annotations

from typing import Optional


SHORT_NEW_THRESHOLD = 0.015405078725644741
BUY_1_THRESHOLD = -0.030291256167492262


def threshold_for(enter_tag: str) -> Optional[float]:
    """Return the frozen threshold for a branch, or ``None`` if ungated."""

    if enter_tag == "short_new":
        return SHORT_NEW_THRESHOLD
    if enter_tag == "buy_1":
        return BUY_1_THRESHOLD
    return None


def accepts(enter_tag: str, btc_ret_24h: Optional[float]) -> bool:
    """Apply the research gate without changing any strategy state.

    Ungated branches are accepted. A gated branch with missing BTC state is not
    accepted because the historical experiment used fail-closed semantics.
    """

    threshold = threshold_for(enter_tag)
    if threshold is None:
        return True
    if btc_ret_24h is None:
        return False
    return btc_ret_24h >= threshold
