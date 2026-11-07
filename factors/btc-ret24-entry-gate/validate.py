"""Validate the frozen BTC 24h x entry-branch factor on archived snapshots.

This is a research-only evaluator.  It does not re-run Freqtrade and it does
not simulate replacement entries after a signal is blocked.  Its purpose is to
check whether the frozen factor keeps the same direction across time blocks,
using only entry-time fields and already recorded trade outcomes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


THRESHOLDS = {
    "short_new": 0.015405078725644741,
    "buy_1": -0.030291256167492262,
}
GATED_BRANCHES = tuple(THRESHOLDS)
BOOTSTRAP_SAMPLES = 2000
RANDOM_SEED = 20261107


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"open_date", "enter_tag", "profit_ratio", "btc_ret_24h"}
    missing = required.difference(rows[0] if rows else {})
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    for row in rows:
        row["profit_ratio"] = float(row["profit_ratio"])
        row["btc_ret_24h"] = float(row["btc_ret_24h"])
        row["date"] = datetime.fromisoformat(row["open_date"].replace("Z", "+00:00"))
        row["year"] = int(row.get("year") or row["date"].year)
        row["quarter"] = f"{row['date'].year}-Q{((row['date'].month - 1) // 3) + 1}"
        row["day"] = row["open_date"][:10]
        row["accepted"] = (
            row["enter_tag"] not in THRESHOLDS
            or row["btc_ret_24h"] >= THRESHOLDS[row["enter_tag"]]
        )
    return rows


def mean(values: Iterable[float]) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def trade_stats(rows: list[dict], extra_roundtrip_bps: float = 0.0) -> dict:
    returns = [row["profit_ratio"] - extra_roundtrip_bps / 10000.0 for row in rows]
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    return {
        "n": len(returns),
        "win_rate": (len(wins) / len(returns)) if returns else None,
        "mean_return": mean(returns),
        "median_return": quantile(returns, 0.5),
        "profit_factor": (gross_profit / gross_loss) if gross_loss else None,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "large_loss_rate": (
            sum(value <= -0.01 for value in returns) / len(returns)
            if returns
            else None
        ),
        "worst_return": min(returns) if returns else None,
    }


def bootstrap_delta(accepted: list[dict], blocked: list[dict]) -> dict:
    """Bootstrap accepted-minus-blocked mean by entry day, not by trade."""

    if not accepted or not blocked:
        return {"samples": 0, "ci95": [None, None], "median": None, "p_positive": None}
    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in accepted + blocked:
        by_day[row["day"]].append(row)
    days = list(by_day)
    rng = random.Random(RANDOM_SEED)
    deltas: list[float] = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sampled_days = [days[rng.randrange(len(days))] for _ in days]
        sample = [row for day in sampled_days for row in by_day[day]]
        accepted_values = [row["profit_ratio"] for row in sample if row["accepted"]]
        blocked_values = [row["profit_ratio"] for row in sample if not row["accepted"]]
        if accepted_values and blocked_values:
            deltas.append(mean(accepted_values) - mean(blocked_values))
    return {
        "samples": len(deltas),
        "ci95": [quantile(deltas, 0.025), quantile(deltas, 0.975)],
        "median": quantile(deltas, 0.5),
        "p_positive": sum(value > 0 for value in deltas) / len(deltas) if deltas else None,
    }


def comparison(rows: list[dict], label: str, branch: str) -> dict:
    accepted = [row for row in rows if row["accepted"]]
    blocked = [row for row in rows if not row["accepted"]]
    accepted_stats = trade_stats(accepted)
    blocked_stats = trade_stats(blocked)
    delta = None
    if accepted_stats["mean_return"] is not None and blocked_stats["mean_return"] is not None:
        delta = accepted_stats["mean_return"] - blocked_stats["mean_return"]
    return {
        "block": label,
        "branch": branch,
        "threshold": THRESHOLDS[branch],
        "accepted": accepted_stats,
        "blocked": blocked_stats,
        "delta_mean_return": delta,
        "bootstrap_day_cluster": bootstrap_delta(accepted, blocked),
    }


def pooled(rows: list[dict], branch: str, label: str) -> dict:
    return comparison([row for row in rows if row["enter_tag"] == branch], label, branch)


def classify(yearly: list[dict], branch: str) -> dict:
    oos = [row for row in yearly if row["branch"] == branch and row["block"] in {"2025", "2026"}]
    positive = [row for row in oos if row["delta_mean_return"] is not None and row["delta_mean_return"] > 0]
    pooled_row = next(row for row in yearly if row["branch"] == branch and row["block"] == "OOS pooled")
    lower = pooled_row["bootstrap_day_cluster"]["ci95"][0]
    strict_pass = bool(oos) and len(positive) == len(oos) and lower is not None and lower > 0
    return {
        "branch": branch,
        "oos_blocks": [row["block"] for row in oos],
        "positive_oos_blocks": [row["block"] for row in positive],
        "strict_pass": strict_pass,
        "classification": "validated_factor" if strict_pass else "candidate_not_validated",
        "reason": (
            "all OOS year deltas positive and day-cluster 95% lower bound above zero"
            if strict_pass
            else "direction or uncertainty criterion failed; keep as candidate"
        ),
    }


def csv_rows(comparisons: list[dict]) -> list[dict]:
    output = []
    for row in comparisons:
        for group_name in ("accepted", "blocked"):
            stats = row[group_name]
            output.append(
                {
                    "block": row["block"],
                    "branch": row["branch"],
                    "group": group_name,
                    "threshold": row["threshold"],
                    **stats,
                    "delta_mean_return": row["delta_mean_return"],
                    "bootstrap_ci_low": row["bootstrap_day_cluster"]["ci95"][0],
                    "bootstrap_ci_high": row["bootstrap_day_cluster"]["ci95"][1],
                    "bootstrap_p_positive": row["bootstrap_day_cluster"]["p_positive"],
                }
            )
    return output


def render_report(metrics: dict, input_path: Path) -> str:
    lines = [
        "# BTC 24 小时收益 × 入场分支：因子有效性复核",
        "",
        "状态：完成（结论：候选因子，未通过严格有效性门槛）",
        "",
        "## 结论",
        "",
        "本次把 2024 年冻结的定义原样带入 2025、2026，并按年度和日期簇 bootstrap 检查方向稳定性。",
        "严格门槛要求：两个样本外年度的接受组平均收益差都为正，且日期簇 bootstrap 的 95% 区间下界大于 0。",
        "当前定义没有通过，因此不能把它升级为已验证有效因子，也不能据此提高杠杆。",
        "",
        "最值得保留的是 `short_new` 的分支条件候选；`buy_1` 在 2026 年的差值反转，因此不应继续作为同一条稳定门控。",
        "这仍是已成交交易上的条件统计，不模拟被阻断后释放的持仓位会带来的替代交易。",
        "",
        "## 数据与口径",
        "",
        f"- 输入：`{input_path.as_posix()}`",
        f"- 样本：{metrics['sample']['rows']} 笔，年份 {', '.join(map(str, metrics['sample']['years']))}",
        "- 收益字段：Freqtrade 归档中的 `profit_ratio`，已包含原始引擎费用；未重建滑点和资金费。",
        "- 接受条件：使用冻结阈值，不重新选参；缺失值本批数据没有出现。",
        "- bootstrap：按开仓日期重采样，避免把同一市场冲击下的多笔交易当作完全独立。",
        "",
        "## 样外年度比较",
        "",
        "| 分支 | 年份 | 接受笔数 | 阻断笔数 | 接受均值 | 阻断均值 | 差值 | 95% 区间 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in metrics["comparisons"]:
        if row["block"] not in {"2025", "2026", "OOS pooled"}:
            continue
        ci = row["bootstrap_day_cluster"]["ci95"]
        ci_text = "—" if ci[0] is None else f"{ci[0]:.4%} ～ {ci[1]:.4%}"
        lines.append(
            f"| `{row['branch']}` | {row['block']} | {row['accepted']['n']} | {row['blocked']['n']} | "
            f"{row['accepted']['mean_return']:.4%} | {row['blocked']['mean_return']:.4%} | "
            f"{row['delta_mean_return']:.4%} | {ci_text} |"
        )
    lines += [
        "",
        "## 判定",
        "",
    ]
    for item in metrics["classifications"]:
        lines.append(f"- `{item['branch']}`：**{item['classification']}**。{item['reason']}。")
    lines += [
        "",
        "## 下一步",
        "",
        "1. 保留 `btc_ret_24h` 的分支交互定义，但将 `short_new` 标记为候选，不进入实盘杠杆逻辑。",
        "2. 对 `short_new` 做真正未触碰的 forward / paper trading，记录被阻断信号和替代交易。",
        "3. 如果 forward 仍保持正向，再做含滑点、资金费和容量约束的完整账户回测。",
        "4. 在上述步骤完成前，杠杆保持基线，不根据这次结果调整。",
        "",
        "这次没有修改策略，也没有连接服务器或下单。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = read_rows(args.input)
    args.output.mkdir(parents=True, exist_ok=False)

    comparisons: list[dict] = []
    for branch in GATED_BRANCHES:
        branch_rows = [row for row in rows if row["enter_tag"] == branch]
        for year in (2024, 2025, 2026):
            comparisons.append(comparison([row for row in branch_rows if row["year"] == year], str(year), branch))
        comparisons.append(pooled([row for row in branch_rows if row["year"] in (2025, 2026)], branch, "OOS pooled"))
        for quarter in sorted({row["quarter"] for row in branch_rows if row["year"] >= 2025}):
            comparisons.append(comparison([row for row in branch_rows if row["quarter"] == quarter], quarter, branch))

    years = sorted({row["year"] for row in rows})
    metrics = {
        "factor": {
            "name": "branch-conditioned BTC 24h return gate",
            "thresholds": THRESHOLDS,
            "decision_time": "last completed BTC 5m candle before entry",
        },
        "sample": {"path": args.input.as_posix(), "rows": len(rows), "years": years},
        "comparisons": comparisons,
        "classifications": [classify(comparisons, branch) for branch in GATED_BRANCHES],
        "protocol": {
            "calibration_year": 2024,
            "oos_years": [2025, 2026],
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "random_seed": RANDOM_SEED,
            "strict_pass_rule": "all OOS year mean deltas > 0 and pooled day-cluster CI95 lower bound > 0",
        },
        "limitations": [
            "Archived executed trades do not model replacement entries after a signal is blocked.",
            "2025/2026 are out-of-time checks but not a completely untouched future experiment because the archive was previously inspected.",
            "Profit ratio includes original engine costs; slippage and funding were not reconstructed.",
            "No full portfolio backtest was run for the short_new-only variant in this experiment.",
        ],
    }
    metrics["input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    (args.output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows_for_csv = csv_rows(comparisons)
    with (args.output / "block-metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_for_csv[0]))
        writer.writeheader()
        writer.writerows(rows_for_csv)
    (args.output / "report.md").write_text(render_report(metrics, args.input), encoding="utf-8")
    manifest = {
        "input": args.input.as_posix(),
        "input_sha256": metrics["input_sha256"],
        "script": Path(__file__).as_posix(),
        "protocol": metrics["protocol"],
        "outputs": ["metrics.json", "block-metrics.csv", "report.md", "manifest.json"],
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
