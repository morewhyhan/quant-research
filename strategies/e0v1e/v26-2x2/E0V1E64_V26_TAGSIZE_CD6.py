"""Vol-scaled floor-25, with buy_1 sized down to half (H2)."""
from E0V1E64_V26_VOLSCALE_CD6 import E0V1E64_V26_VOLSCALE_CD6
from tag_sizing_common import TagSizingMixin


class E0V1E64_V26_TAGSIZE_CD6(TagSizingMixin, E0V1E64_V26_VOLSCALE_CD6):
    tag_multipliers = {"short_1": 1.0, "buy_1": 0.50, "short_new": 1.0, "buy_new": 1.0}
