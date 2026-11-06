"""Evaluate a frozen entry filter on snapshots without pretending to rerun trades."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


SHORT_BTC24_MIN = 0.015405078725644741
BUY_BTC24_MIN = -0.030291256167492262


def _max_loss_run(values: pd.Series) -> int:
    current = longest = 0
    for value in values:
        current = current + 1 if value <= 0 else 0
        longest = max(longest, current)
    return longest


def evaluate(path: Path, output: Path) -> dict:
    frame = pd.read_csv(path, parse_dates=["open_date", "close_date"])
    frame["blocked_by_envgate"] = (
        (frame["enter_tag"].eq("short_new") & (frame["btc_ret_24h"].lt(SHORT_BTC24_MIN) | frame["btc_ret_24h"].isna()))
        | (frame["enter_tag"].eq("buy_1") & (frame["btc_ret_24h"].lt(BUY_BTC24_MIN) | frame["btc_ret_24h"].isna()))
    )
    rows = []
    for year, group in frame.groupby("year", sort=True):
        for sample, subset in (("baseline", group), ("accepted", group.loc[~group.blocked_by_envgate]), ("blocked", group.loc[group.blocked_by_envgate])):
            values = subset["profit_ratio"]
            gains = values.loc[values.gt(0)].sum()
            losses = -values.loc[values.lt(0)].sum()
            rows.append({
                "year": int(year),
                "sample": sample,
                "n": int(len(subset)),
                "coverage_of_archived_trades": float(len(subset) / len(group)) if len(group) else None,
                "mean_profit_ratio": float(values.mean()) if len(values) else None,
                "win_rate": float(values.gt(0).mean()) if len(values) else None,
                "equal_stake_profit_factor": float(gains / losses) if losses else None,
                "large_loss_rate": float(values.le(-0.01).mean()) if len(values) else None,
                "max_consecutive_nonpositive": _max_loss_run(values),
            })
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "rule": {
            "short_new": f"btc_ret_24h >= {SHORT_BTC24_MIN:.12f}",
            "buy_1": f"btc_ret_24h >= {BUY_BTC24_MIN:.12f}",
            "calibration": "thresholds fixed from 2024 buckets before applying to later years",
        },
        "rows": rows,
        "interpretation": "Filter-only diagnostic on already executed trades. It does not model replacement entries, freed capacity, fees, or changed account path. Full Freqtrade runs are required for strategy claims.",
    }
    (output / "candidate-filter-only.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(Path(args.input), Path(args.output)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
