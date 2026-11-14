"""Vol-scaled floor-25 with a Kelly-shaped volatility curve (H1)."""
from E0V1E64_V26_VOLSCALE_CD6 import E0V1E64_V26_VOLSCALE_CD6


class E0V1E64_V26_KELLYVOL_CD6(E0V1E64_V26_VOLSCALE_CD6):
    vol_scale = ((0.006, 0.60), (0.009, 0.65), (0.012, 1.00),
                 (0.016, 1.60), (0.020, 2.40), (9.9, 0.65))
