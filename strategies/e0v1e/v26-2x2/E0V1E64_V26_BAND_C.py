"""BAND_A baseline with the 1.2-1.6 band raised to 1.60 (P3 continued)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_C(E0V1E64_V26_BAND_A):
    vol_scale = ((0.006, 0.60), (0.009, 0.85), (0.012, 1.00), (0.016, 1.60), (0.020, 2.40), (9.9, 1.20))
