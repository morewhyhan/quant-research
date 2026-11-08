"""实验代码：V26 动态+恢复版本，加上“未收回的不利突破不进场”。

这不是生产策略。完整回测失败：+365.99%，PF 1.10，回撤 67.02%。
不要把本文件复制回 strategies/。
"""
import pandas as pd
from E0V1E64_V26_GATED_DYNAMIC_RECOVERY import E0V1E64_V26_GATED_DYNAMIC_RECOVERY


class TrueBreakoutEntryVeto(E0V1E64_V26_GATED_DYNAMIC_RECOVERY):
    breakout_lookback = 50
    breakout_recent = 6

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        bh = dataframe['high'].rolling(self.breakout_lookback).max().shift(1)
        bl = dataframe['low'].rolling(self.breakout_lookback).min().shift(1)
        dataframe['bh50'] = bh
        dataframe['bl50'] = bl
        dataframe['up_break'] = (dataframe['close'] > bh).fillna(False)
        dataframe['down_break'] = (dataframe['close'] < bl).fillna(False)
        dataframe['up_break_recent'] = dataframe['up_break'].rolling(self.breakout_recent).max().fillna(0).astype(bool)
        dataframe['down_break_recent'] = dataframe['down_break'].rolling(self.breakout_recent).max().fillna(0).astype(bool)
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        block_short = (dataframe['enter_short'].eq(1) & dataframe['up_break_recent'] & (dataframe['close'] >= dataframe['bh50']))
        block_long = (dataframe['enter_long'].eq(1) & dataframe['down_break_recent'] & (dataframe['close'] <= dataframe['bl50']))
        dataframe.loc[block_short, 'enter_short'] = 0
        dataframe.loc[block_long, 'enter_long'] = 0
        return dataframe