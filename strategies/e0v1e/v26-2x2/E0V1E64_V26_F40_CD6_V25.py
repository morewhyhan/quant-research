"""Floor-40 + cooldown-6 + volatility curve derived from 2025 only."""
from E0V1E64_V26_F40_CD6 import E0V1E64_V26_F40_CD6
from vol_scale_common import VolScaledStakeMixin


class E0V1E64_V26_F40_CD6_V25(VolScaledStakeMixin, E0V1E64_V26_F40_CD6):
    vol_scale = ((0.006, 0.55), (0.009, 0.85), (0.012, 1.00),
                 (0.016, 1.10), (0.020, 1.75), (9.9, 1.00))
