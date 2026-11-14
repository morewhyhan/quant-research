"""Floor-25 sizing with a 6-candle cooldown (profit-lever study)."""
from E0V1E64_V26_GATED_FIXED_RECOVERY import E0V1E64_V26_GATED_FIXED_RECOVERY
from frac_common import FloorFractionalStakeMixin


class E0V1E64_V26_FLOOR25_CD6(FloorFractionalStakeMixin, E0V1E64_V26_GATED_FIXED_RECOVERY):
    stake_fraction = 0.25
    stake_floor = 1000.0

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]
