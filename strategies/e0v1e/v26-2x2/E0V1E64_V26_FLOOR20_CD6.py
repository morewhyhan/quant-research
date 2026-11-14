"""Floor-20 sizing with a 6-candle cooldown (profit-lever study)."""
from E0V1E64_V26_FLOOR20_RECOVERY import E0V1E64_V26_FLOOR20_RECOVERY


class E0V1E64_V26_FLOOR20_CD6(E0V1E64_V26_FLOOR20_RECOVERY):
    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]
