"""Full Kelly (all-in) with a CPPI drawdown brake, alpha = 0.5."""
from E0V1E64_V26_F40_FINAL import E0V1E64_V26_F40_FINAL
from drawdown_brake_common import DrawdownBrakeMixin


class E0V1E64_V26_KELLY_BRAKE(DrawdownBrakeMixin, E0V1E64_V26_F40_FINAL):
    stake_fraction = 1.00
    brake_alpha = 0.5
