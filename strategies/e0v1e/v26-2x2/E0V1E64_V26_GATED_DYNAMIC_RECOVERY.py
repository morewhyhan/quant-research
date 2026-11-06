"""V26 2x2: optimized entry gate + dynamic compounding + recovery exit."""
from E0V1E64_V9 import E0V1E64_V9
from v26_2x2_common import OptimizedEntryGateMixin, RecoveryExitMixin


class E0V1E64_V26_GATED_DYNAMIC_RECOVERY(
    OptimizedEntryGateMixin, RecoveryExitMixin, E0V1E64_V9
):
    pass
