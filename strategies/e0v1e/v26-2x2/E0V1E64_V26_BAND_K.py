"""BAND_A with a later recovery exit (recover two thirds)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_K(E0V1E64_V26_BAND_A):
    recovery_divisor = 1.5
