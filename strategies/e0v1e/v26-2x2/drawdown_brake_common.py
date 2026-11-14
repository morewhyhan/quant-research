"""CPPI-style drawdown brake used by the profit-lever study."""


class DrawdownBrakeMixin:
    """Scale the stake by the cushion above a floor tied to the running peak."""

    brake_alpha = 0.5

    def bot_start(self, **kwargs):
        self._eq_peak = None
        super().bot_start(**kwargs)

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        base = super().custom_stake_amount(
            pair, current_time, current_rate, proposed_stake, min_stake,
            max_stake, leverage, entry_tag, side, **kwargs
        )
        equity = self.wallets.get_total_stake_amount() if self.wallets else max_stake
        peak = self._eq_peak if self._eq_peak else equity
        peak = max(peak, equity)
        self._eq_peak = peak
        alpha = self.brake_alpha
        if alpha and alpha > 0 and peak > 0:
            cushion = equity - alpha * peak
            brake = max(0.0, min(1.0, cushion / (peak * (1.0 - alpha))))
        else:
            brake = 1.0
        stake = min(base * brake, max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
