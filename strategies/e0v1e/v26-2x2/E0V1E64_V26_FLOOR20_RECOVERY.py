"""V26 fixed + recovery, stake = max(1,000, 20% of equity) (profit-lever study)."""
from E0V1E64_V26_GATED_FIXED_RECOVERY import E0V1E64_V26_GATED_FIXED_RECOVERY
from frac_common import FloorFractionalStakeMixin


class E0V1E64_V26_FLOOR20_RECOVERY(FloorFractionalStakeMixin, E0V1E64_V26_GATED_FIXED_RECOVERY):
    stake_fraction = 0.20
    stake_floor = 1000.0
