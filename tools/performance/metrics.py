"""Explicit trade-level and equity-level metrics; standard library only."""
from math import isfinite
from statistics import mean, stdev


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def trade_metrics(trades):
    profits = [number(t["profit_abs"], "profit_abs") for t in trades]
    winners = [p for p in profits if p > 0]
    losers = [p for p in profits if p < 0]
    gain, loss = sum(winners), -sum(losers)
    return {
        "trades": len(profits), "wins": len(winners), "losses": len(losers),
        "breakeven": sum(p == 0 for p in profits),
        "win_rate": len(winners) / len(profits) if profits else None,
        "net_profit_abs": sum(profits), "gross_winning_abs": gain,
        "gross_losing_abs": loss, "profit_factor": gain / loss if loss else None,
        "mean_profit_abs": mean(profits) if profits else None,
        "mean_win_abs": mean(winners) if winners else None,
        "mean_loss_abs": mean(losers) if losers else None,
        "trade_profit_abs_sample_stdev": stdev(profits) if len(profits) > 1 else None,
        "worst_trade_abs": min(profits) if profits else None,
        "best_trade_abs": max(profits) if profits else None,
        "largest_five_losses_fraction": -sum(sorted(losers)[:5]) / loss if loss else None,
    }


def equity_metrics(values):
    """Ordered positive mark-to-market equity, no external cash flows assumed."""
    values = [number(v, "equity") for v in values]
    if not values or any(v <= 0 for v in values):
        raise ValueError("equity must contain positive values")
    peak = values[0]
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = max(drawdown, 1 - value / peak)
    return {"total_return": values[-1] / values[0] - 1, "max_drawdown": drawdown,
            "observations": len(values)}
