"""Vol-scaled floor-25 with a one-shot 3% partial take-profit."""
from E0V1E64_V26_VOLSCALE_CD6 import E0V1E64_V26_VOLSCALE_CD6
from partial_tp_common import PartialTPMixin


class E0V1E64_V26_VOLSCALE_TP3(PartialTPMixin, E0V1E64_V26_VOLSCALE_CD6):
    tp_trigger = 0.03
    tp_fraction = 0.5
