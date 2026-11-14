"""F40_FINAL plus the stuck-position exit rule from the stopping-time study."""
from E0V1E64_V26_F40_FINAL import E0V1E64_V26_F40_FINAL
from stuck_exit_common import StuckExitMixin


class E0V1E64_V26_F40_STUCK(StuckExitMixin, E0V1E64_V26_F40_FINAL):
    stuck_rules = ((0.02, 2.0), (0.03, 3.0), (0.04, 4.0), (0.05, 6.0))
