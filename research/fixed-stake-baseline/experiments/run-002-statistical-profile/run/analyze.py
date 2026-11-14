
"""Statistical profile of the fixed-stake + recovery variant, 2025 and 2026."""
import json, zipfile, math, random
from collections import Counter, defaultdict
import numpy as np

BASE = "/mnt/c/Users/why/Desktop/ft_userdata/backtest_results/"
FILES = {
    "2025": "backtest-result-2026-11-13_19-37-00.zip",
    "2026": "backtest-result-2026-11-13_19-11-36.zip",
}
random.seed(20261113); np.random.seed(20261113)

trades = []
for year, fn in FILES.items():
    z = zipfile.ZipFile(BASE + fn)
    name = [x for x in z.namelist() if x.endswith(".json")][0]
    d = json.loads(z.read(name))
    s = list(d["strategy"].keys())[0]
    for t in d["strategy"][s]["trades"]:
        t = dict(t); t["year"] = year
        trades.append(t)
trades.sort(key=lambda x: x["close_date"])
r = np.array([t["profit_ratio"] for t in trades])
abs_pnl = np.array([t["profit_abs"] for t in trades])
tags = np.array([(t.get("enter_tag") or "") for t in trades])
exits = np.array([(t.get("exit_reason") or "") for t in trades])
pairs = np.array([t["pair"] for t in trades])
short = np.array([bool(t["is_short"]) for t in trades])
dur = np.array([t["trade_duration"] for t in trades])  # minutes
fees = np.array([(t.get("fee_open_cost") or 0) + (t.get("fee_close_cost") or 0) for t in trades])
funding = np.array([(t.get("funding_fees") or 0) for t in trades])

def pf(x):
    g = x[x > 0].sum(); l = -x[x <= 0].sum()
    return float(g / l) if l else float("inf")

def block(title, rows, header):
    out = ["", "### " + title, "", "| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return out

L = ["# 固定＋恢复：统计画像（2025 + 2026）", "",
     "脚本生成本文件；数字来自两份 Freqtrade 结果包，未经手工修改。", ""]

# --- sample
L += ["## 1. 样本", ""]
L += [f"- 交易数：{len(trades)}（2025 {int((np.array([t['year'] for t in trades])=='2025').sum())}，2026 {int((np.array([t['year'] for t in trades])=='2026').sum())}）"]
L += [f"- 区间：{trades[0]['open_date'][:10]} → {trades[-1]['close_date'][:10]}"]
L += [f"- 币对：{len(set(pairs))}"]
L += [f"- 手续费合计：{fees.sum():.1f} USDT；资金费合计：{funding.sum():.1f} USDT"]
L += [f"- 平均 stake：{np.mean([t['stake_amount'] for t in trades]):.1f} USDT"]

L += ["", "## 2. 单笔收益分布", ""]
qs = np.percentile(r, [1, 5, 25, 50, 75, 95, 99])
skew = float(((r - r.mean()) ** 3).mean() / r.std() ** 3)
kurt = float(((r - r.mean()) ** 4).mean() / r.std() ** 4 - 3)
L += [f"- 均值 {r.mean()*100:.4f}%｜中位数 {np.median(r)*100:.4f}%｜标准差 {r.std()*100:.3f}%"]
L += [f"- 偏度 {skew:.3f}｜超额峰度 {kurt:.3f}"]
L += [f"- 分位：1% {qs[0]*100:.2f}%｜5% {qs[1]*100:.2f}%｜25% {qs[2]*100:.2f}%｜50% {qs[3]*100:.2f}%｜75% {qs[4]*100:.2f}%｜95% {qs[5]*100:.2f}%｜99% {qs[6]*100:.2f}%"]
L += [f"- 最小 {r.min()*100:.2f}%｜最大 {r.max()*100:.2f}%"]

w = r[r > 0]; l = r[r <= 0]
p = len(w) / len(r); q = 1 - p
L += ["", "## 3. 胜率与盈亏结构", ""]
L += [f"- 胜率 {p*100:.2f}%（{len(w)} 胜 / {len(l)} 负）"]
L += [f"- 平均盈利 {w.mean()*100:.3f}%｜平均亏损 {l.mean()*100:.3f}%｜盈亏比 {abs(w.mean()/l.mean()):.3f}"]
L += [f"- Profit Factor {pf(r):.3f}｜期望（每笔）{r.mean()*100:.4f}%"]
L += [f"- 保本胜率 = |L|/(W+|L|) = {abs(l.mean())/(w.mean()+abs(l.mean()))*100:.2f}%，实际 {p*100:.2f}%，余量 {(p-abs(l.mean())/(w.mean()+abs(l.mean())))*100:.2f}pp"]
L += [f"- 最差单笔 {r.min()*100:.2f}%｜最好单笔 {r.max()*100:.2f}%"]

# runs
run_w = run_l = cur_w = cur_l = 0
for x in r:
    if x > 0: cur_w += 1; cur_l = 0
    else: cur_l += 1; cur_w = 0
    run_w = max(run_w, cur_w); run_l = max(run_l, cur_l)
L += [f"- 最长连胜 {run_w}｜最长连亏 {run_l}"]

L += ["", "## 4. 按方向", ""]
rows = []
for name, mask in (("多", ~short), ("空", short)):
    x = r[mask]
    rows.append([name, int(mask.sum()), f"{100*(x>0).mean():.2f}%", f"{x.mean()*100:.4f}%",
                 f"{pf(x):.3f}", f"{abs_pnl[mask].sum():.1f}", f"{100*abs_pnl[mask].sum()/abs_pnl.sum():.1f}%"])
L += block("方向", rows, ["方向", "笔数", "胜率", "EV", "PF", "净盈亏(USDT)", "占总盈亏"])

L += ["", "## 5. 按入场分支", ""]
rows = []
for tag in sorted(set(tags)):
    mask = tags == tag
    if mask.sum() < 5: continue
    x = r[mask]
    rows.append([tag, int(mask.sum()), f"{100*(x>0).mean():.2f}%", f"{x.mean()*100:.4f}%",
                 f"{pf(x):.3f}", f"{abs_pnl[mask].sum():.1f}", f"{100*abs_pnl[mask].sum()/abs_pnl.sum():.1f}%"])
L += block("入场分支", rows, ["enter_tag", "笔数", "胜率", "EV", "PF", "净盈亏(USDT)", "占总盈亏"])

L += ["", "## 6. 按退出原因", ""]
rows = []
for e in sorted(set(exits)):
    mask = exits == e
    x = r[mask]
    rows.append([e, int(mask.sum()), f"{100*(x>0).mean():.2f}%", f"{x.mean()*100:.4f}%",
                 f"{abs_pnl[mask].sum():.1f}", f"{100*abs_pnl[mask].sum()/abs_pnl.sum():.1f}%"])
L += block("退出原因", sorted(rows, key=lambda z: -float(z[4].replace(',', '')))[:12],
           ["exit_reason", "笔数", "胜率", "平均收益", "净盈亏(USDT)", "占总盈亏"])

L += ["", "## 7. 持仓时长", ""]
buckets = [(0, 15), (15, 60), (60, 180), (180, 480), (480, 1440), (1440, 10**9)]
rows = []
for lo, hi in buckets:
    mask = (dur >= lo) & (dur < hi)
    if mask.sum() == 0: continue
    x = r[mask]
    rows.append([f"{lo}–{hi if hi < 10**9 else '∞'} 分钟", int(mask.sum()), f"{100*(x>0).mean():.2f}%",
                 f"{x.mean()*100:.4f}%", f"{abs_pnl[mask].sum():.1f}"])
L += block("时长分桶", rows, ["区间", "笔数", "胜率", "EV", "净盈亏(USDT)"])

# monthly
L += ["", "## 8. 逐月", ""]
month = defaultdict(lambda: [0, 0, 0.0])
for t, x in zip(trades, abs_pnl):
    m = t["close_date"][:7]
    month[m][0] += 1
    month[m][1] += 1 if x > 0 else 0
    month[m][2] += x
rows = [[m, v[0], f"{100*v[1]/v[0]:.1f}%", f"{v[2]:.1f}"] for m, v in sorted(month.items())]
L += block("月度", rows, ["月份", "笔数", "胜率", "净盈亏(USDT)"])

# serial dependence
L += ["", "## 9. 序列相关", ""]
for lag in (1, 2, 3):
    c = float(np.corrcoef(r[:-lag], r[lag:])[0, 1])
    L += [f"- 相邻 {lag} 笔收益相关系数：{c:+.4f}"]
after_win = r[1:][r[:-1] > 0]; after_loss = r[1:][r[:-1] <= 0]
L += [f"- 上一笔盈利后的 EV：{after_win.mean()*100:+.4f}%（{len(after_win)} 笔）"]
L += [f"- 上一笔亏损后的 EV：{after_loss.mean()*100:+.4f}%（{len(after_loss)} 笔）"]

# concentration
L += ["", "## 10. 集中度", ""]
by_pair = defaultdict(float)
for pr_, x in zip(pairs, abs_pnl): by_pair[pr_] += x
top = sorted(by_pair.items(), key=lambda z: -z[1])[:10]
L += [f"- 净盈亏为正的币对：{sum(1 for v in by_pair.values() if v > 0)} / {len(by_pair)}"]
L += [f"- 前 10 币对占总盈亏：{100*sum(v for _, v in top)/abs_pnl.sum():.1f}%"]
share = np.array([abs(v) for v in by_pair.values()]) / np.abs(list(by_pair.values())).sum()
L += [f"- 集中度 HHI：{(share**2).sum():.4f}（1/{(share**2).sum():.1f} ≈ {1/(share**2).sum():.0f} 个等权币对）"]

# bootstrap
L += ["", "## 11. Bootstrap（按平仓日聚类，2000 次）", ""]
days = defaultdict(list)
for t, x in zip(trades, r): days[t["close_date"][:10]].append(x)
clusters = list(days.values())
boot_ev = []; boot_f = []; boot_fc = []
for _ in range(2000):
    sample = []
    for _ in range(len(clusters)):
        sample.extend(clusters[random.randrange(len(clusters))])
    s = np.array(sample); ww = s[s > 0]; ll = s[s <= 0]
    if len(ww) < 5 or len(ll) < 5: continue
    pp = len(ww) / len(s)
    boot_ev.append(s.mean())
    boot_f.append(pp / abs(ll.mean()) - (1 - pp) / ww.mean())
    boot_fc.append(s.mean() / s.var())
L += [f"- 每笔 EV 95% 区间：{100*np.percentile(boot_ev, 2.5):+.4f}% ～ {100*np.percentile(boot_ev, 97.5):+.4f}%"]
L += [f"- 二元凯利 f*：5% {np.percentile(boot_f, 5):.2f}｜中位 {np.percentile(boot_f, 50):.2f}｜95% {np.percentile(boot_f, 95):.2f}"]
L += [f"- 连续凯利 μ/σ²：5% {np.percentile(boot_fc, 5):.2f}｜中位 {np.percentile(boot_fc, 50):.2f}｜95% {np.percentile(boot_fc, 95):.2f}"]

# monte carlo frontier
L += ["", "## 12. 复利前沿（块 bootstrap，2000 条路径）", ""]
rng = np.random.default_rng(20261113)
blocks = 20
rows = []
for f in (0.2, 0.3, 0.4, 0.5, 0.75, 1.0):
    finals = []; dds = []
    for _ in range(2000):
        eq = 1.0; peak = 1.0; mdd = 0.0
        n_done = 0
        while n_done < len(r):
            start = rng.integers(0, len(r) - blocks)
            for x in r[start:start + blocks]:
                eq *= (1 + f * x)
                peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak)
                n_done += 1
                if eq <= 0: break
            if eq <= 0: break
        finals.append(eq); dds.append(mdd)
    rows.append([f"{f:.2f}", f"{np.median(finals):.2f}x", f"{np.percentile(finals,5):.2f}x",
                 f"{100*np.median(dds):.1f}%", f"{100*np.percentile(dds,95):.1f}%"])
L += block("仓位比例 f 与结果", rows, ["f", "中位终值", "5% 分位终值", "中位最大回撤", "95% 分位回撤"])

# equity contribution decay
L += ["", "## 13. 固定仓位的收益衰减", ""]
eq = 1000.0; contrib = []
for x in abs_pnl:
    contrib.append(x / eq); eq += x
deciles = np.array_split(np.array(contrib), 10)
L += ["- 每笔盈亏相对当时权益的比例，按交易顺序十分位：", ""]
L += ["| 十分位 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
L += ["| 每笔均值 | " + " | ".join(f"{100*d.mean():.3f}%" for d in deciles) + " |"]

# half-year stability
L += ["", "## 14. 前后半段", ""]
half = len(r) // 2
L += [f"- 前一半：{len(r[:half])} 笔，EV {r[:half].mean()*100:+.4f}%，胜率 {100*(r[:half]>0).mean():.2f}%"]
L += [f"- 后一半：{len(r[half:])} 笔，EV {r[half:].mean()*100:+.4f}%，胜率 {100*(r[half:]>0).mean():.2f}%"]

open("/mnt/c/Users/why/Desktop/ft_userdata/quant-research/research/fixed-stake-baseline/experiments/run-002-statistical-profile/run/stats.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
