"""Floor-40 + cooldown-6, rebuild baseline (2025 training)."""
from E0V1E64_V26_FLOOR40_RECOVERY import E0V1E64_V26_FLOOR40_RECOVERY


class E0V1E64_V26_F40_CD6(E0V1E64_V26_FLOOR40_RECOVERY):
    stake_fraction = 0.40
    stake_floor = 1000.0

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]
