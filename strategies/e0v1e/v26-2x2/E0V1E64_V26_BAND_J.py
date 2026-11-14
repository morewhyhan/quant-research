"""BAND_A with an earlier recovery exit (recover one third)."""
from E0V1E64_V26_BAND_A import E0V1E64_V26_BAND_A


class E0V1E64_V26_BAND_J(E0V1E64_V26_BAND_A):
    recovery_divisor = 3.0
