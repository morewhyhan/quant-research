"""FINAL with the 1.6-2.0 band set to 2 (risk sensitivity)."""
from E0V1E64_V26_F40_FINAL import E0V1E64_V26_F40_FINAL


class E0V1E64_V26_FINAL_B200(E0V1E64_V26_F40_FINAL):
    vol_scale = ((0.006, 0.55), (0.009, 0.85), (0.012, 1.00),
                 (0.016, 2.00), (0.020, 1.75), (9.9, 1.00))
