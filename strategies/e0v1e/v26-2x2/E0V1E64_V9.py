"""V9: HPO Round1 candidate: continuous reserve, 55% base, 97% cap, 10% drawdown, gamma 0.5."""
from E0V1E64_V5 import E0V1E64_V5


class E0V1E64_V9(E0V1E64_V5):
    base_fraction = 0.55
    f_cap = 0.97
    d_cap = 0.10
    gamma = 0.5

    @classmethod
    def fraction_for_drawdown(cls, drawdown: float) -> float:
        x = min(max(drawdown, 0.0), cls.d_cap) / cls.d_cap
        return cls.base_fraction + (cls.f_cap - cls.base_fraction) * (x ** cls.gamma)
