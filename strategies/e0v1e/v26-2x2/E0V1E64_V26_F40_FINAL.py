"""Rebuild final candidate: floor-40 + cooldown-6 + 2025 vol curve + band 2.40
+ earlier recovery exit (1/3) + 24h range-position sizing on shorts."""
from E0V1E64_V26_F40_CD6_V25B import E0V1E64_V26_F40_CD6_V25B
from range_position_common import RangePositionStakeMixin


class E0V1E64_V26_F40_FINAL(RangePositionStakeMixin, E0V1E64_V26_F40_CD6_V25B):
    recovery_divisor = 3.0
    low_boost = 1.5
    high_boost = 1.3
