"""Experimental: skip loss_half_recovery on extreme 5m expansion."""
import pandas as pd
from E0V1E64_V26_GATED_DYNAMIC_RECOVERY import E0V1E64_V26_GATED_DYNAMIC_RECOVERY


class E0V1E64_V26_GATED_DYNAMIC_RECOVERY_EXTREME_HOLD(E0V1E64_V26_GATED_DYNAMIC_RECOVERY):
    extreme_range_atr = 1.5
    extreme_volume_mult = 2.0

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe = super().populate_indicators(dataframe, metadata)
        dataframe['x_atr14'] = (dataframe['high'] - dataframe['low']).rolling(14).mean()
        dataframe['x_vol20'] = dataframe['volume'].rolling(20).mean()
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        frame, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if len(frame):
            last = frame.iloc[-1]
            rng = float(last['high'] - last['low'])
            atr = float(last['x_atr14']) if pd.notna(last['x_atr14']) else 0.0
            vol = float(last['volume'])
            v20 = float(last['x_vol20']) if pd.notna(last['x_vol20']) else 0.0
            extreme = (atr > 0 and rng >= self.extreme_range_atr * atr) or (v20 > 0 and vol >= self.extreme_volume_mult * v20)
            if extreme:
                old = self.min_worst_loss
                self.min_worst_loss = -1e9
                try:
                    return super().custom_exit(pair, trade, current_time, current_rate, current_profit, **kwargs)
                finally:
                    self.min_worst_loss = old
        return super().custom_exit(pair, trade, current_time, current_rate, current_profit, **kwargs)