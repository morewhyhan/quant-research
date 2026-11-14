"""Volatility-scaled sizing used by the profit-lever study."""
from datetime import timedelta


class VolScaledStakeMixin:
    """Scale the stake by the pair's ATR% at the previous closed candle."""

    vol_scale = ((0.006, 0.60), (0.009, 0.85), (0.012, 1.00),
                 (0.016, 1.25), (0.020, 1.50), (9.9, 1.20))

    def _vol_multiplier(self, pair, current_time):
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or frame.empty:
            return 1.0
        cutoff = current_time - timedelta(minutes=5)
        row = frame.loc[frame["date"] <= cutoff]
        if row.empty:
            return 1.0
        last = row.iloc[-1]
        close = float(last["close"]) if last["close"] else 0.0
        if close <= 0:
            return 1.0
        atr_pct = float(last["atr"]) / close
        for edge, mult in self.vol_scale:
            if atr_pct < edge:
                return mult
        return 1.0

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        base = super().custom_stake_amount(
            pair, current_time, current_rate, proposed_stake, min_stake,
            max_stake, leverage, entry_tag, side, **kwargs
        )
        stake = min(base * self._vol_multiplier(pair, current_time), max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
