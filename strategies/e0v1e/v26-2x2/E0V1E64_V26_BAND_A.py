"""Vol-scaled floor-25 with the 1.2-1.6 band raised to 2.40 (P3)."""
from E0V1E64_V26_VOLSCALE_CD6 import E0V1E64_V26_VOLSCALE_CD6


class E0V1E64_V26_BAND_A(E0V1E64_V26_VOLSCALE_CD6):
    vol_scale = ((0.006, 0.60), (0.009, 0.85), (0.012, 1.00), (0.016, 2.40), (0.020, 1.50), (9.9, 1.20))
