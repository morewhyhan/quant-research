"""Floor-30 with a drawdown governor and a 6-candle cooldown (B4)."""
from E0V1E64_V26_FLOOR25_CD6 import E0V1E64_V26_FLOOR25_CD6
from drawdown_governor_common import DrawdownGovernorMixin


class E0V1E64_V26_GOV30_CD6(DrawdownGovernorMixin, E0V1E64_V26_FLOOR25_CD6):
    gov_base = 0.30
    gov_mid = 0.20
    gov_low = 0.12
