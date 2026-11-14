"""Shared factors for the four V26 2x2 research strategies.

The entry gate is the frozen 2024-calibrated improvement.  Position sizing
and the half-loss-recovery exit are deliberately separate mixins so each
experiment changes one axis at a time.
"""


class OptimizedEntryGateMixin:
    """Keep only the two entry branches supported by the frozen BTC gate."""

    btc_ret24_short_new_min = 0.015405078725644741
    btc_ret24_buy1_min = -0.030291256167492262

    def populate_indicators(self, dataframe, metadata):
        dataframe = super().populate_indicators(dataframe, metadata)
        btc = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.timeframe)
        btc = btc.sort_values("date").set_index("date")
        # Only the previous completed BTC candle is visible at entry.
        btc_ret24 = btc["close"].pct_change(288).shift(1)
        dataframe["btc_ret24"] = dataframe["date"].map(btc_ret24)
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe = super().populate_entry_trend(dataframe, metadata)
        btc_ret24 = dataframe["btc_ret24"]
        tags = dataframe["enter_tag"].fillna("")
        block_short_new = (
            dataframe["enter_short"].eq(1)
            & tags.str.contains("short_new", regex=False)
            & ((btc_ret24 < self.btc_ret24_short_new_min) | btc_ret24.isna())
        )
        block_buy1 = (
            dataframe["enter_long"].eq(1)
            & tags.str.contains("buy_1", regex=False)
            & ((btc_ret24 < self.btc_ret24_buy1_min) | btc_ret24.isna())
        )
        dataframe.loc[block_short_new, "enter_short"] = 0
        dataframe.loc[block_buy1, "enter_long"] = 0
        return dataframe


class RecoveryExitMixin:
    """Optional V26 exit: recover part of a worst loss after a threshold.

    Defaults reproduce the frozen rule: exit once the position has recovered
    half of its worst loss after that loss reached -5%.
    """

    min_worst_loss = -0.05
    recovery_divisor = 2.0

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        reason = super().custom_exit(pair, trade, current_time, current_rate, current_profit, **kwargs)
        state = trade.get_custom_data(key="loss_recovery", default=None)
        worst = current_profit if state is None else min(float(state["worst"]), current_profit)
        trade.set_custom_data(key="loss_recovery", value={"worst": worst})
        if worst <= self.min_worst_loss and current_profit >= worst / self.recovery_divisor:
            return "loss_half_recovery"
        return reason


class FixedStakeMixin:
    """Use up to 1,000 USDT each time; cap to available balance below it."""

    fixed_stake = 1000.0

    def custom_stake_amount(
        self, pair, current_time, current_rate, proposed_stake, min_stake,
        max_stake, leverage, entry_tag, side, **kwargs
    ):
        stake = min(self.fixed_stake, max_stake)
        if min_stake is not None:
            stake = max(stake, min_stake)
        return stake
