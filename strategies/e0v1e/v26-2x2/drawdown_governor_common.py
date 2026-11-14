"""Drawdown governor used by the profit-lever study (B4)."""


class DrawdownGovernorMixin:
    """Scale the stake down while equity is below its peak."""

    gov_base = 0.30
    gov_mid = 0.20
    gov_low = 0.12
    gov_dd_mid = 0.08
    gov_dd_low = 0.15
    stake_floor = 1000.0

    def bot_start(self, **kwargs):
        self._peak_equity = None
        super().bot_start(**kwargs)

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        equity = self.wallets.get_total_stake_amount() if self.wallets else max_stake
        peak = self._peak_equity if self._peak_equity else equity
        peak = max(peak, equity)
        self._peak_equity = peak
        drawdown = 1.0 - equity / peak if peak else 0.0

        fraction = self.gov_base
        if drawdown >= self.gov_dd_low:
            fraction = self.gov_low
        elif drawdown >= self.gov_dd_mid:
            fraction = self.gov_mid

        stake = min(max(self.stake_floor, equity * fraction), max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
