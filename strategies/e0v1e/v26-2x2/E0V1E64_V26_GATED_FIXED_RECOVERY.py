"""V26 2x2: optimized entry gate + fixed 1,000 USDT stake + recovery exit."""
from E0V1E64_V9 import E0V1E64_V9
from v26_2x2_common import FixedStakeMixin, OptimizedEntryGateMixin, RecoveryExitMixin


class E0V1E64_V26_GATED_FIXED_RECOVERY(
    FixedStakeMixin, OptimizedEntryGateMixin, RecoveryExitMixin, E0V1E64_V9
):
    pass
