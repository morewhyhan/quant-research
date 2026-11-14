"""Per-trade equity stop used by the profit-lever study (D2)."""


class EquityStopMixin:
    """Close a trade once its loss reaches a share of current equity."""

    equity_stop = 0.03

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        reason = super().custom_exit(
            pair, trade, current_time, current_rate, current_profit, **kwargs
        )
        if reason:
            return reason
        equity = self.wallets.get_total_stake_amount() if self.wallets else 0.0
        if equity and equity > 0 and trade.stake_amount:
            if current_profit * trade.stake_amount / equity <= -self.equity_stop:
                return "equity_stop"
        return None
