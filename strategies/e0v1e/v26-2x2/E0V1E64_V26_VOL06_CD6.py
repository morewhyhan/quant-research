"""Floor-25 + cooldown-6 with a 0.6% ATR entry gate."""
from E0V1E64_V26_FLOOR25_CD6 import E0V1E64_V26_FLOOR25_CD6
from vol_gate_common import VolGateMixin


class E0V1E64_V26_VOL06_CD6(VolGateMixin, E0V1E64_V26_FLOOR25_CD6):
    min_atr_pct = 0.006
