"""Floor-25 + cooldown-6 with volatility-scaled stake."""
from E0V1E64_V26_FLOOR25_CD6 import E0V1E64_V26_FLOOR25_CD6
from vol_scale_common import VolScaledStakeMixin


class E0V1E64_V26_VOLSCALE_CD6(VolScaledStakeMixin, E0V1E64_V26_FLOOR25_CD6):
    pass
