"""Two-slot variant: stake = max(500, 15% of equity) per slot, cooldown 6 candles."""
from E0V1E64_V26_GATED_FIXED_RECOVERY import E0V1E64_V26_GATED_FIXED_RECOVERY
from frac_common import FloorFractionalStakeMixin


class E0V1E64_V26_FLOOR15X2_RECOVERY(FloorFractionalStakeMixin, E0V1E64_V26_GATED_FIXED_RECOVERY):
    stake_fraction = 0.15
    stake_floor = 500.0

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]
