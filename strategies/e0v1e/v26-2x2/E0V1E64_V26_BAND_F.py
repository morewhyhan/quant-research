"""BAND_A with the sub-0.6% band cut to 0.40 (BAND_F)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_F(E0V1E64_V26_BAND_A):
    vol_scale = ((0.006, 0.40), (0.009, 0.85), (0.012, 1.00), (0.016, 2.40), (0.020, 1.50), (9.9, 1.20))
