"""As V25 but the 1.2-1.6 band raised to 2.40 (band candidate)."""
from E0V1E64_V26_F40_CD6_V25 import E0V1E64_V26_F40_CD6_V25


class E0V1E64_V26_F40_CD6_V25B(E0V1E64_V26_F40_CD6_V25):
    vol_scale = ((0.006, 0.55), (0.009, 0.85), (0.012, 1.00),
                 (0.016, 2.40), (0.020, 1.75), (9.9, 1.00))
