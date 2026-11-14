"""Time-based exit used by the profit-lever study (C1)."""


class TimeGateMixin:
    """Close a trade that has been open past a deadline without enough profit."""

    time_gate_minutes = 180.0
    time_gate_profit = 0.005

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        reason = super().custom_exit(
            pair, trade, current_time, current_rate, current_profit, **kwargs
        )
        if reason:
            return reason
        minutes = (current_time - trade.open_date_utc).total_seconds() / 60.0
        if minutes >= self.time_gate_minutes and current_profit < self.time_gate_profit:
            return "time_gate"
        return None
