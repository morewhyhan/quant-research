"""Rebuild chain with 24h range-position sizing on shorts."""
from E0V1E64_V26_F40_CD6_V25B import E0V1E64_V26_F40_CD6_V25B
from range_position_common import RangePositionStakeMixin


class E0V1E64_V26_F40_V25B_RP(RangePositionStakeMixin, E0V1E64_V26_F40_CD6_V25B):
    low_boost = 1.5
    high_boost = 1.3
