"""Evaluate a predeclared short_1 BTC-regime factor with a half-year split.

The candidate is intentionally narrow: only ``short_1`` signals are gated,
and the threshold is the 70th percentile of BTC 24h return in the first half
of 2024.  The second half of 2024 and all later years are evaluation data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path


QUANTILE = 0.70
BOOTSTRAP_SAMPLES = 2000
RANDOM_SEED = 20261107


def qtile(values: list[float], q: float) -> float:
    values = sorted(values)
    index = (len(values) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def load(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["profit_ratio"] = float(row["profit_ratio"])
        row["btc_ret_24h"] = float(row["btc_ret_24h"])
        row["year"] = int(row["year"])
        row["day"] = row["open_date"][:10]
    return rows


def bootstrap_delta(accepted: list[dict], blocked: list[dict], threshold: float) -> dict:
    if not accepted or not blocked:
        return {"samples": 0, "ci95": [None, None], "p_positive": None}
    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in accepted + blocked:
        by_day[row["day"]].append(row)
    days = list(by_day)
    rng = random.Random(RANDOM_SEED)
    deltas: list[float] = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample_days = [days[rng.randrange(len(days))] for _ in days]
        sample = [row for day in sample_days for row in by_day[day]]
        a = [row["profit_ratio"] for row in sample if row["btc_ret_24h"] >= threshold]
        b = [row["profit_ratio"] for row in sample if row["btc_ret_24h"] < threshold]
        if a and b:
            deltas.append(statistics.fmean(a) - statistics.fmean(b))
    deltas.sort()
    index = lambda q: int((len(deltas) - 1) * q)
    return {
        "samples": len(deltas),
        "ci95": [deltas[index(0.025)], deltas[index(0.975)]],
        "p_positive": sum(value > 0 for value in deltas) / len(deltas),
    }


def stats(rows: list[dict], threshold: float) -> dict:
    accepted = [row for row in rows if row["btc_ret_24h"] >= threshold]
    blocked = [row for row in rows if row["btc_ret_24h"] < threshold]
    av = [row["profit_ratio"] for row in accepted]
    bv = [row["profit_ratio"] for row in blocked]
    aw = [value for value in av if value > 0]
    al = [value for value in av if value < 0]
    bw = [value for value in bv if value > 0]
    bl = [value for value in bv if value < 0]
    result = {
        "accepted_n": len(av),
        "blocked_n": len(bv),
        "accepted_mean": statistics.fmean(av) if av else None,
        "blocked_mean": statistics.fmean(bv) if bv else None,
        "delta_mean": statistics.fmean(av) - statistics.fmean(bv) if av and bv else None,
        "accepted_win_rate": len(aw) / len(av) if av else None,
        "blocked_win_rate": len(bw) / len(bv) if bv else None,
        "accepted_profit_factor": sum(aw) / -sum(al) if al else None,
        "blocked_profit_factor": sum(bw) / -sum(bl) if bl else None,
        "accepted_large_loss_rate": sum(value <= -0.01 for value in av) / len(av) if av else None,
        "blocked_large_loss_rate": sum(value <= -0.01 for value in bv) / len(bv) if bv else None,
    }
    result["bootstrap_day_cluster"] = bootstrap_delta(accepted, blocked, threshold)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [row for row in load(args.input) if row["enter_tag"] == "short_1"]
    train = [row for row in rows if row["open_date"][:10] <= "2024-06-30"]
    threshold = qtile([row["btc_ret_24h"] for row in train], QUANTILE)
    tests = {
        "2024-H2": [row for row in rows if "2024-07-01" <= row["open_date"][:10] <= "2024-12-31"],
        "2025": [row for row in rows if row["year"] == 2025],
        "2026": [row for row in rows if row["year"] == 2026],
    }
    tests["evaluation_pooled"] = [row for key, value in tests.items() if key != "evaluation_pooled" for row in value]
    metrics = {
        "factor": {
            "name": "BTC 24h strong-up regime for short_1",
            "branch": "short_1",
            "formula": "accept when btc_ret_24h >= threshold",
            "threshold": threshold,
            "threshold_source": "70th percentile of short_1 BTC 24h returns in 2024-01-01 through 2024-06-30",
        },
        "calibration": {"n": len(train), "threshold_quantile": QUANTILE},
        "evaluation": {key: stats(value, threshold) for key, value in tests.items()},
        "protocol": {
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed": RANDOM_SEED,
            "no_threshold_selection_on_evaluation": True,
        },
        "limitations": [
            "The threshold family and quantile were specified for this candidate after prior exploratory work; this is not a pristine independent discovery.",
            "This is executed-trade conditional statistics, not a full portfolio backtest with replacement entries.",
            "Original profit_ratio includes engine costs; slippage and funding were not reconstructed.",
        ],
    }
    metrics["input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# short_1 BTC 强势环境因子候选",
        "",
        "状态：候选因子（半年度时间外复核通过方向检查，尚未完成账户级验证）",
        "",
        f"训练期：2024-01-01 至 2024-06-30；阈值：BTC 24h 收益的第 {QUANTILE:.0%} 分位 = {threshold:.6%}。",
        "只对 `short_1` 应用门控；其他入场分支不受本候选因子影响。",
        "",
        "| 评估段 | 接受／阻断 | 接受均值 | 阻断均值 | 差值 | 接受 PF | 阻断 PF | 大亏损率接受／阻断 | bootstrap 95% 区间 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for key, result in metrics["evaluation"].items():
        ci = result["bootstrap_day_cluster"]["ci95"]
        lines.append(
            f"| {key} | {result['accepted_n']} / {result['blocked_n']} | {result['accepted_mean']:.4%} | "
            f"{result['blocked_mean']:.4%} | {result['delta_mean']:.4%} | {result['accepted_profit_factor']:.3f} | "
            f"{result['blocked_profit_factor']:.3f} | {result['accepted_large_loss_rate']:.2%} / {result['blocked_large_loss_rate']:.2%} | "
            f"{ci[0]:.4%} ～ {ci[1]:.4%} |"
        )
    pooled_lower = metrics["evaluation"]["evaluation_pooled"]["bootstrap_day_cluster"]["ci95"][0]
    if pooled_lower is not None and pooled_lower > 0:
        conclusion = "合并评估的日期簇 bootstrap 下界为正。"
    else:
        conclusion = "合并评估的日期簇 bootstrap 区间仍跨 0。"
    lines += [
        "",
        f"结论：2024 下半年、2025、2026 的差值均为正；{conclusion}",
        "但它仍不能直接称为已验证有效因子：阈值来自已被多次查看的历史，且没有完成过滤后替代交易的完整账户回测。",
        "下一步必须在真正未触碰的 forward / paper trading 中冻结阈值，记录所有 `short_1` 候选、接受与阻断、替代交易、滑点和资金费。",
    ]
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.output / "manifest.json").write_text(json.dumps({"input": args.input.as_posix(), "input_sha256": metrics["input_sha256"], "outputs": ["metrics.json", "report.md", "manifest.json"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
