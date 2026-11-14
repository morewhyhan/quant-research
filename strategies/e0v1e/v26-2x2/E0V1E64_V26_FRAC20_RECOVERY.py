"""V26 fixed + recovery, stake = 20% of equity (profit-lever study)."""
from E0V1E64_V26_GATED_FIXED_RECOVERY import E0V1E64_V26_GATED_FIXED_RECOVERY
from frac_common import FractionalStakeMixin


class E0V1E64_V26_FRAC20_RECOVERY(FractionalStakeMixin, E0V1E64_V26_GATED_FIXED_RECOVERY):
    stake_fraction = 0.20
