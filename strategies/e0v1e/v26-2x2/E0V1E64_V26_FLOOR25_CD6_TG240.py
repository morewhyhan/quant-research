"""Floor-25 + cooldown-6 with a 240-minute time gate (C1)."""
from E0V1E64_V26_FLOOR25_CD6 import E0V1E64_V26_FLOOR25_CD6
from time_gate_common import TimeGateMixin


class E0V1E64_V26_FLOOR25_CD6_TG240(TimeGateMixin, E0V1E64_V26_FLOOR25_CD6):
    time_gate_minutes = 240.0
    time_gate_profit = 0.005
