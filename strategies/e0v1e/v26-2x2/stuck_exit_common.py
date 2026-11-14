"""Stuck-position exit derived from the stopping-time study (run-012)."""


class StuckExitMixin:
    """Cut shallow losses that have been open too long, keep deep ones."""

    stuck_rules = ((0.02, 2.0), (0.03, 3.0), (0.04, 4.0), (0.05, 6.0))

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        reason = super().custom_exit(
            pair, trade, current_time, current_rate, current_profit, **kwargs
        )
        if reason:
            return reason
        try:
            held_h = (current_time - trade.open_date_utc).total_seconds() / 3600.0
        except Exception:
            return None
        for loss, hours in self.stuck_rules:
            if current_profit <= -loss and held_h >= hours:
                return "stuck_exit"
        return None
