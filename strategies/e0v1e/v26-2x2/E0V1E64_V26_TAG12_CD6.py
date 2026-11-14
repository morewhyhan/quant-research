"""Vol-scaled floor-25 with tag sizing recycled into 1.2x exposure (H2b)."""
from E0V1E64_V26_TAGSIZE_CD6 import E0V1E64_V26_TAGSIZE_CD6


class E0V1E64_V26_TAG12_CD6(E0V1E64_V26_TAGSIZE_CD6):
    tag_multipliers = {"short_1": 1.20, "buy_1": 0.60, "short_new": 1.20, "buy_new": 1.20}
