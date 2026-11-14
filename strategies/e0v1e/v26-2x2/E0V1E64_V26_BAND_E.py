"""BAND_A with the 1.2-1.6 band raised to 3.00 (BAND_E)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_E(E0V1E64_V26_BAND_A):
    vol_scale = ((0.006, 0.60), (0.009, 0.85), (0.012, 1.00), (0.016, 3.00), (0.020, 2.40), (9.9, 1.20))
