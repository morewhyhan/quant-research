"""Stake rules used by the profit-lever study.

Not part of the frozen 2x2 family. The four 2x2 cells stay untouched; these
mixins only change how much capital one trade may use.
"""


class FractionalStakeMixin:
    """Use a fixed fraction of current equity as stake."""

    stake_fraction = 0.25

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        equity = self.wallets.get_total_stake_amount() if self.wallets else max_stake
        stake = min(equity * self.stake_fraction, max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake


class FloorFractionalStakeMixin:
    """Keep a fixed floor, then grow with equity above that floor."""

    stake_fraction = 0.30
    stake_floor = 1000.0

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        equity = self.wallets.get_total_stake_amount() if self.wallets else max_stake
        stake = max(self.stake_floor, equity * self.stake_fraction)
        stake = min(stake, max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
