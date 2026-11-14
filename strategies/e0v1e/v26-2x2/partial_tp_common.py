"""Partial take-profit used by the profit-lever study (C3)."""


class PartialTPMixin:
    """Close half of the position once, when profit first reaches a trigger."""

    tp_trigger = 0.03
    tp_fraction = 0.5
    position_adjustment_enable = True

    def adjust_trade_position(
        self, trade, current_time, current_rate, current_profit, min_stake, max_stake,
        current_entry_rate=0.0, current_exit_rate=0.0, current_entry_profit=0.0,
        current_exit_profit=0.0, **kwargs
    ):
        if current_profit < self.tp_trigger:
            return None
        if trade.get_custom_data(key="tp_done", default=False):
            return None
        trade.set_custom_data(key="tp_done", value=True)
        amount = trade.stake_amount * self.tp_fraction
        if min_stake is not None and amount < min_stake:
            return None
        return -amount, "partial_tp"
