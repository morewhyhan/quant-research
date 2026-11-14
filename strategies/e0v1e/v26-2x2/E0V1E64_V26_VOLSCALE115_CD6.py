"""Floor-25 + cooldown-6 with volatility-scaled stake (multipliers x1.15)."""
from E0V1E64_V26_VOLSCALE_CD6 import E0V1E64_V26_VOLSCALE_CD6


class E0V1E64_V26_VOLSCALE115_CD6(E0V1E64_V26_VOLSCALE_CD6):
    vol_scale = ((0.006, 0.69), (0.009, 0.98), (0.012, 1.15),
                 (0.016, 1.44), (0.020, 1.73), (9.9, 1.38))
