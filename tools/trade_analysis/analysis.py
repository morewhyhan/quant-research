"""Trade diagnostics and one-to-one timestamp matching, not causal attribution."""
from collections import defaultdict
from tools.performance.metrics import trade_metrics


def analyze(result):
    return {"strategy": result["strategy"], "trade_metrics": trade_metrics(result["trades"]),
            "by_side": groups(result["trades"], "side"),
            "by_exit": groups(result["trades"], "exit_reason"),
            "by_pair": groups(result["trades"], "pair"),
            "engine_reported": result["engine_reported"],
            "limitations": ["profit_abs is supplied, without independent fee/funding reconstruction",
                            "Trade statistics are not daily account returns or volatility",
                            "Engine returns/drawdown are not independently reconstructed",
                            "No proof of alpha, absence of leakage, or future profitability"]}


def groups(trades, field):
    buckets = defaultdict(list)
    for trade in trades:
        value = ("short" if trade.get("is_short") else "long") if field == "side" else str(trade.get(field, "unknown"))
        buckets[value].append(trade)
    return {key: trade_metrics(value) for key, value in sorted(buckets.items())}
