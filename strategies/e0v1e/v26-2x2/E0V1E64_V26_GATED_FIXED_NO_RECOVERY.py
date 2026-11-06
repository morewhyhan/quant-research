"""V26 2x2: optimized entry gate + fixed 1,000 USDT stake + no recovery exit."""
from E0V1E64_V9 import E0V1E64_V9
from v26_2x2_common import FixedStakeMixin, OptimizedEntryGateMixin


class E0V1E64_V26_GATED_FIXED_NO_RECOVERY(
    FixedStakeMixin, OptimizedEntryGateMixin, E0V1E64_V9
):
    pass
