"""Render summaries without recomputing or changing experiment results."""
import json


def render_report(metrics):
    lines = ["# 实验分析报告", "", "每笔交易和分组结果见 [metrics.json](metrics.json)，所用文件和代码见 [manifest.json](manifest.json)。", ""]
    if "left" in metrics:
        left, right = metrics["left"]["trade_metrics"], metrics["right"]["trade_metrics"]
        lines += ["| 指标 | 左实验 | 右实验 |", "| --- | ---: | ---: |"]
        for key in ("trades", "win_rate", "profit_factor", "net_profit_abs", "mean_profit_abs", "worst_trade_abs"):
            lines.append(f"| {key} | {left[key]} | {right[key]} |")
        matching = metrics["matching"]
        lines += ["", f"匹配 {matching['matched']} 对；左未匹配 {matching['unmatched_left']} 笔，右未匹配 {matching['unmatched_right']} 笔。", "", "按左表顺序找最近且未配对的交易。两边金额不同，不代表差额都由策略改动造成。"]
    elif "trade_metrics" in metrics:
        lines += ["| 逐笔指标 | 数值 |", "| --- | ---: |"]
        lines += [f"| {key} | {value} |" for key, value in metrics["trade_metrics"].items()]
        if metrics.get("synthetic_example"):
            lines += ["", "这是人工数据，不是市场交易业绩。", "", f"示例账户统计：{metrics['equity']}"]
        if metrics.get("engine_reported"):
            lines += ["", "原回测程序报告的数字，本工具没有重算：", "", "```json", json.dumps(metrics["engine_reported"], ensure_ascii=False, indent=2), "```"]
    else:
        lines += ["```json", json.dumps(metrics, ensure_ascii=False, indent=2, allow_nan=False), "```"]
    lines += ["", "每笔盈亏金额的波动，不是每日收益率的波动。没有亏损时 PF 为 null。本分析没有重新核算费用、还原真实成交，也不能保证未来收益。", ""]
    return "\n".join(lines)
