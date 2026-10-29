"""Minimal long-only, next-open research example. Not a Freqtrade substitute."""
from tools.data.research_io import check_bars
from tools.performance.metrics import number
from tools.data.momentum import momentum


def signals(closes, window):
    return [0 if value is None else (1 if value > 0 else -1)
            for value in momentum(closes, window)]


def simulate(bars, window=3, fee=0.001, initial=1000):
    quality = check_bars(bars)
    if not quality["valid"]:
        raise ValueError(str(quality["errors"]))
    fee, initial = number(fee, "fee"), number(initial, "initial")
    if not 0 <= fee < 1 or initial <= 0:
        raise ValueError("Require 0 <= fee < 1 and positive initial capital")
    sig = signals([b["close"] for b in bars], window)
    cash, position, entry = initial, 0.0, None
    trades, equity = [], [initial]

    def exit_at(price, date, reason):
        nonlocal cash, position, entry
        cash = position * price * (1-fee)
        profit = cash - entry["stake_amount"]
        trades.append({**entry, "close_date": date, "close_rate": price,
                       "profit_abs": profit, "profit_ratio": profit / entry["stake_amount"],
                       "exit_reason": reason})
        position, entry = 0.0, None

    for i, bar in enumerate(bars):
        decision = sig[i-1] if i else 0  # previous completed bar only
        if position and decision < 0:
            exit_at(bar["open"], bar["date"], "negative_momentum_next_open")
        elif not position and decision > 0:
            entry = {"pair": "SYNTHETIC/QUOTE", "is_short": False, "open_date": bar["date"],
                     "open_rate": bar["open"], "stake_amount": cash}
            position = cash / (bar["open"] * (1+fee))
            cash = 0.0
        equity.append(cash + position * bar["close"])
    if position:
        exit_at(bars[-1]["close"], bars[-1]["date"], "forced_end_of_sample_close")
        equity[-1] = cash
    return {"trades": trades, "equity": equity, "signals": sig, "quality": quality}
