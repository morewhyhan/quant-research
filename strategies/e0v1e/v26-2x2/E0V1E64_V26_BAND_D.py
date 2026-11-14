"""BAND_A baseline with the 0.6-0.9 band cut to 0.65 (P3 continued)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_D(E0V1E64_V26_BAND_A):
    vol_scale = ((0.006, 0.60), (0.009, 0.65), (0.012, 1.00), (0.016, 2.40), (0.020, 1.50), (9.9, 1.20))
