"""Explore a predeclared family of BTC 24h regime thresholds.

This script records every threshold generated from 2024 calibration quantiles;
it does not select a winner from 2025/2026.  It is deliberately separate from
the frozen factor definition in ``factor.py``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path


BRANCHES = ("short_1", "short_new", "buy_1")
QUANTILES = (0.6, 0.7, 0.8, 0.9)
BOOTSTRAP_SAMPLES = 2000
RANDOM_SEED = 20261107


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    index = (len(values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def load(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["year"] = int(row["year"])
        row["profit_ratio"] = float(row["profit_ratio"])
        row["btc_ret_24h"] = float(row["btc_ret_24h"])
        row["day"] = row["open_date"][:10]
    return rows


def percentile(values: list[float], q: float) -> float | None:
    return statistics.fmean(values) if values and q == 0.5 else None


def bootstrap_delta(accepted_rows: list[dict], blocked_rows: list[dict]) -> dict:
    if not accepted_rows or not blocked_rows:
        return {"samples": 0, "ci95": [None, None], "p_positive": None}
    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in accepted_rows + blocked_rows:
        by_day[row["day"]].append(row)
    days = list(by_day)
    rng = random.Random(RANDOM_SEED)
    deltas = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sampled_days = [days[rng.randrange(len(days))] for _ in days]
        sample = [row for day in sampled_days for row in by_day[day]]
        accepted = [row["profit_ratio"] for row in sample if row["btc_ret_24h"] >= accepted_rows[0]["threshold"]]
        blocked = [row["profit_ratio"] for row in sample if row["btc_ret_24h"] < accepted_rows[0]["threshold"]]
        if accepted and blocked:
            deltas.append(statistics.fmean(accepted) - statistics.fmean(blocked))
    deltas.sort()
    low = deltas[int((len(deltas) - 1) * 0.025)] if deltas else None
    high = deltas[int((len(deltas) - 1) * 0.975)] if deltas else None
    return {
        "samples": len(deltas),
        "ci95": [low, high],
        "p_positive": (sum(value > 0 for value in deltas) / len(deltas)) if deltas else None,
    }


def compare(rows: list[dict], threshold: float, branch: str) -> dict:
    values = [row for row in rows if row["enter_tag"] == branch]
    accepted_rows = [row | {"threshold": threshold} for row in values if row["btc_ret_24h"] >= threshold]
    blocked_rows = [row | {"threshold": threshold} for row in values if row["btc_ret_24h"] < threshold]
    accepted = [row["profit_ratio"] for row in accepted_rows]
    blocked = [row["profit_ratio"] for row in blocked_rows]
    accepted_wins = [value for value in accepted if value > 0]
    accepted_losses = [value for value in accepted if value < 0]
    blocked_wins = [value for value in blocked if value > 0]
    blocked_losses = [value for value in blocked if value < 0]
    return {
        "accepted_n": len(accepted),
        "blocked_n": len(blocked),
        "accepted_mean": statistics.fmean(accepted) if accepted else None,
        "blocked_mean": statistics.fmean(blocked) if blocked else None,
        "delta_mean": (statistics.fmean(accepted) - statistics.fmean(blocked)) if accepted and blocked else None,
        "accepted_win_rate": (len(accepted_wins) / len(accepted)) if accepted else None,
        "blocked_win_rate": (len(blocked_wins) / len(blocked)) if blocked else None,
        "accepted_profit_factor": (sum(accepted_wins) / -sum(accepted_losses)) if accepted_losses else None,
        "blocked_profit_factor": (sum(blocked_wins) / -sum(blocked_losses)) if blocked_losses else None,
        "accepted_large_loss_rate": (sum(value <= -0.01 for value in accepted) / len(accepted)) if accepted else None,
        "blocked_large_loss_rate": (sum(value <= -0.01 for value in blocked) / len(blocked)) if blocked else None,
        "bootstrap_day_cluster": bootstrap_delta(accepted_rows, blocked_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load(args.input)
    calibration = [row for row in rows if row["year"] == 2024]
    oos = [row for row in rows if row["year"] in (2025, 2026)]
    records = []
    for branch in BRANCHES:
        values = [row["btc_ret_24h"] for row in calibration if row["enter_tag"] == branch]
        for q in QUANTILES:
            threshold = quantile(values, q)
            record = {
                "branch": branch,
                "calibration_year": 2024,
                "quantile": q,
                "threshold": threshold,
                "calibration": compare(calibration, threshold, branch),
                "oos_2025": compare([row for row in oos if row["year"] == 2025], threshold, branch),
                "oos_2026": compare([row for row in oos if row["year"] == 2026], threshold, branch),
                "oos_pooled": compare(oos, threshold, branch),
            }
            records.append(record)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "threshold-grid.json").write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.output / "threshold-grid.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "branch", "quantile", "threshold",
            "calibration_delta", "oos_2025_delta", "oos_2026_delta",
            "oos_2025_accepted_n", "oos_2025_blocked_n",
            "oos_2026_accepted_n", "oos_2026_blocked_n",
                "oos_2025_ci_low", "oos_2025_ci_high",
                "oos_2026_ci_low", "oos_2026_ci_high",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "branch": record["branch"],
                "quantile": record["quantile"],
                "threshold": record["threshold"],
                "calibration_delta": record["calibration"]["delta_mean"],
                "oos_2025_delta": record["oos_2025"]["delta_mean"],
                "oos_2026_delta": record["oos_2026"]["delta_mean"],
                "oos_2025_accepted_n": record["oos_2025"]["accepted_n"],
                "oos_2025_blocked_n": record["oos_2025"]["blocked_n"],
                "oos_2026_accepted_n": record["oos_2026"]["accepted_n"],
                "oos_2026_blocked_n": record["oos_2026"]["blocked_n"],
                "oos_2025_ci_low": record["oos_2025"]["bootstrap_day_cluster"]["ci95"][0],
                "oos_2025_ci_high": record["oos_2025"]["bootstrap_day_cluster"]["ci95"][1],
                "oos_2026_ci_low": record["oos_2026"]["bootstrap_day_cluster"]["ci95"][0],
                "oos_2026_ci_high": record["oos_2026"]["bootstrap_day_cluster"]["ci95"][1],
            })
    (args.output / "README.md").write_text(
        "# BTC 24h regime threshold exploration\n\n"
        "Thresholds are generated only from 2024 calibration quantiles. The full grid is retained; no 2025/2026 winner is selected.\n",
        encoding="utf-8",
    )
    print(args.output.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
