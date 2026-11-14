"""BAND_A with the 0.5-0.7% hole cut to 0.40 (BAND_H)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_H(E0V1E64_V26_BAND_A):
    vol_scale = ((0.005, 0.60), (0.007, 0.40), (0.009, 0.85), (0.012, 1.00),
                 (0.016, 1.25), (0.020, 2.40), (9.9, 1.20))
