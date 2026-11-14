"""Floor-30 sizing with a shorter cooldown (12 candles) for the profit-lever study."""
from E0V1E64_V26_FLOOR30_RECOVERY import E0V1E64_V26_FLOOR30_RECOVERY


class E0V1E64_V26_FLOOR30_CD12(E0V1E64_V26_FLOOR30_RECOVERY):
    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 12}]
