"""Entry volatility gate used by the profit-lever study."""


class VolGateMixin:
    """Skip entries when the pair is too quiet to mean-revert."""

    min_atr_pct = 0.006

    def populate_indicators(self, dataframe, metadata):
        dataframe = super().populate_indicators(dataframe, metadata)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe = super().populate_entry_trend(dataframe, metadata)
        quiet = dataframe["atr_pct"] < self.min_atr_pct
        dataframe.loc[quiet, "enter_long"] = 0
        dataframe.loc[quiet, "enter_short"] = 0
        return dataframe
