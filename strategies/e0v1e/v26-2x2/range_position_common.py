"""Position-in-range sizing used by the profit-lever study."""
from datetime import timedelta


class RangePositionStakeMixin:
    """Scale the stake by where price sits inside its 24h range."""

    low_boost = 1.5
    high_boost = 1.3
    low_cut = 0.20
    high_cut = 0.80

    def _range_position(self, pair, current_time):
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or frame.empty:
            return None
        cutoff = current_time - timedelta(minutes=5)
        window = frame.loc[frame["date"] <= cutoff].tail(288)
        if len(window) < 100:
            return None
        close = float(window["close"].iloc[-1])
        hi = float(window["high"].max())
        lo = float(window["low"].min())
        if hi <= lo:
            return None
        return (close - lo) / (hi - lo)

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        base = super().custom_stake_amount(
            pair, current_time, current_rate, proposed_stake, min_stake,
            max_stake, leverage, entry_tag, side, **kwargs
        )
        pos = self._range_position(pair, current_time)
        if pos is None or side != "short":
            return base
        if pos < self.low_cut:
            mult = self.low_boost
        elif pos > self.high_cut:
            mult = self.high_boost
        else:
            mult = 1.0
        stake = min(base * mult, max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
