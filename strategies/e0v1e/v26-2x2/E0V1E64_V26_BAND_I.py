"""BAND_A with the >2.6% tail cut to 0.65 (BAND_I)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_I(E0V1E64_V26_BAND_A):
    vol_scale = ((0.006, 0.60), (0.009, 0.85), (0.012, 1.00), (0.016, 1.25),
                 (0.020, 2.40), (0.026, 1.20), (9.9, 0.65))
