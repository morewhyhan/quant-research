"""Vol-scaled floor-25 with the >2.0 band cut to 0.65 (P3)."""
from E0V1E64_V26_VOLSCALE_CD6 import E0V1E64_V26_VOLSCALE_CD6


class E0V1E64_V26_BAND_B(E0V1E64_V26_VOLSCALE_CD6):
    vol_scale = ((0.006, 0.60), (0.009, 0.85), (0.012, 1.00), (0.016, 1.50), (0.020, 1.20), (9.9, 0.65))
