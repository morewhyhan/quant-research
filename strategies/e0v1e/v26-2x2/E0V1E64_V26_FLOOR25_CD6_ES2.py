"""Floor-25 + cooldown-6 with a 2% equity stop (D2)."""
from E0V1E64_V26_FLOOR25_CD6 import E0V1E64_V26_FLOOR25_CD6
from equity_stop_common import EquityStopMixin


class E0V1E64_V26_FLOOR25_CD6_ES2(EquityStopMixin, E0V1E64_V26_FLOOR25_CD6):
    equity_stop = 0.02
