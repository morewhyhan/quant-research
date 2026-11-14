"""BAND_A with short entries boosted at the edges of the 24h range."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A
from range_position_common import RangePositionStakeMixin


class E0V1E64_V26_RANGEPOS_CD6(RangePositionStakeMixin, E0V1E64_V26_BAND_A):
    low_boost = 1.5
    high_boost = 1.3
