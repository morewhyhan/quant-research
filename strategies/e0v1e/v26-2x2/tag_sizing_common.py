"""Signal-quality sizing used by the profit-lever study (H2)."""


class TagSizingMixin:
    """Scale the stake by the entry signal's own Kelly ratio."""

    tag_multipliers = {"short_1": 1.0, "buy_1": 0.50, "short_new": 1.0, "buy_new": 1.0}

    def _tag_multiplier(self, entry_tag):
        tag = entry_tag or ""
        for key, mult in self.tag_multipliers.items():
            if key in tag:
                return mult
        return 1.0

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        base = super().custom_stake_amount(
            pair, current_time, current_rate, proposed_stake, min_stake,
            max_stake, leverage, entry_tag, side, **kwargs
        )
        stake = min(base * self._tag_multiplier(entry_tag), max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
