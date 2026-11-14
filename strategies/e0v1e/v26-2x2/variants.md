# 研究变体清单

本目录共 34 个策略类：四个冻结版本见 [README](README.md)，其余 30 个是变体。每个变体对应一次实验，结论分三类：**采纳**、**否**、**未运行**。

## 仓位类

| 类名 | 改了什么 | 结论 | 记录 |
| --- | --- | --- | --- |
| `FRAC20/30/40_RECOVERY` | 常数比例 20%／30%／40% | 否：两年不同向 | [run-001](../../../research/profit-levers/experiments/run-001-sizing-and-fees/experiment.md) |
| `FLOOR20/25/30/40/50_RECOVERY` | 地板 + 比例（最低 1,000） | 25% 采纳（v1）；30% 尾部过大；20／40／50 仅探索 | 同上 |
| `FLOOR20_CD6`、`FLOOR30_CD6`、`FLOOR30_CD12` | 冷却 6／12 根 | 6 根采纳；12 根只有 2025 好 | [run-002](../../../research/profit-levers/experiments/run-002-cooldown/experiment.md) |
| `FLOOR15X2_RECOVERY` | 双槽，每槽 `max(500, 15%)` | 否：笔数 +50%，收益 −52% | [run-003](../../../research/profit-levers/experiments/run-003-two-slots/experiment.md) |
| `GOV30_CD6` | 回撤时自动降档 | **未运行**：回撤不可预测，理论不成立 | — |

## 退出类

| 类名 | 改了什么 | 结论 | 记录 |
| --- | --- | --- | --- |
| `FLOOR25_CD6_TG180`、`_TG240` | 时间闸门（≥180／240 分钟且浮盈 <0.5% 平仓） | 否：收益 −22%~−39% | [run-004](../../../research/profit-levers/experiments/run-004-time-gate/experiment.md) |
| `FLOOR25_CD6_ES2`、`_ES3` | 单笔权益止损 2%／3% | 否：收益 −34%~−92%，回撤反升 | [run-005](../../../research/profit-levers/experiments/run-005-equity-stop/experiment.md) |
| `VOLSCALE_TP2`、`_TP3` | 浮盈 +2%／+3% 平一半 | 否：不同向 | [run-008](../../../research/profit-levers/experiments/run-008-partial-tp/experiment.md) |

## 入场与仓位系数

| 类名 | 改了什么 | 结论 | 记录 |
| --- | --- | --- | --- |
| `VOL06_CD6` | 入场 ATR% <0.6 不开仓 | 否：2026 更差、回撤升 | [run-007](../../../research/profit-levers/experiments/run-007-volatility/experiment.md) |
| `VOLSCALE_CD6` | 按入场波动加权（系数 ×1.00） | **采纳（v2）** | 同上 |
| `VOLSCALE115_CD6` | 加权系数整体 ×1.15 | 否：滚动最差 72%，超预算 | 同上 |
| `KELLYVOL_CD6` | 按凯利形状重排系数 | 否：收益 −3%~−7% | [run-011](../../../research/profit-levers/experiments/run-011-band-tuning/experiment.md) |
| `BAND_A` | 1.2–1.6 档 1.25→2.40 | **采纳（v3，当前基准）** | 同上 |
| `BAND_B` | >2.0 档 1.20→0.65 | 否：收益 −16% | 同上 |
| `BAND_C` | 1.2–1.6 档 1.25→1.60 | 否：三项全劣 | 同上 |
| `BAND_D` | 0.6–0.9 档 0.85→0.65 | 平局：收益 −2.9%、回撤 −1.16pp | 同上 |
| `BAND_E` | 1.2–1.6 档 2.40→3.00 | 收益 +24%~+27%，但最差窗口 +2.6pp（24.1%），否 | 同上 |
| `BAND_F` | <0.6 档 0.60→0.40 | 无效：收益 −1%、PF +0.003 | 同上 |
| `BAND_G` | 1.2–1.6 档 2.40→3.60 | 收益 +34%~+43%，PF 不再涨，最差窗口 24.6%，否 | 同上 |

## 信号加权类

| 类名 | 改了什么 | 结论 | 记录 |
| --- | --- | --- | --- |
| `TAGSIZE_CD6` | buy_1 仓位打五折 | 单独否：收益 −5%~−15%，但回撤降 2~6pp | [run-007](../../../research/profit-levers/experiments/run-007-volatility/experiment.md) |
| `TAG12_CD6` | 上面的基础上全体 ×1.2 | 否：收益 +24%/+10%，但滚动最差 62.7% 超预算 | 同上 |
| `GATED_DYNAMIC_RECOVERY_BREAKOUT_VETO` | 未收回不利突破禁止开仓 | 否：完整回测失败 | [run-002 veto](../../../research/breakout-false-filter/experiments/run-002-entry-veto/experiment.md) |

| `F40_CD6` | 地板 40% + 冷却 6 根 | 重建第 3 层，2025 +912.25% | [重建报告](../../../research/profit-levers/report.md) |
| `F40_CD6_V25` | ＋2025 推导的波动曲线 | 第 4 层，2025 +1,031.24% | 同上 |
| `F40_CD6_V25B` | ＋1.2–1.6 档 2.40 | 第 5 层，2025 +1,820.78% | 同上 |
| `F40_V25B_J` | ＋恢复退出 1/3 | 第 6 层，2025 +2,697.38% | 同上 |
| `F40_V25B_RP` | ＋区间位置加权 | 备选，2025 +2,291.17% | 同上 |
| **`F40_FINAL`** | 全部叠加 | **当前版本**：2025 +3,378%、2026 +2,357% | 同上 |

## 公共 mixin

| 文件 | 作用 | 用在哪些类 |
| --- | --- | --- |
| `frac_common.py` | `FractionalStakeMixin`、`FloorFractionalStakeMixin` | FLOOR／FRAC／VOLSCALE 系列 |
| `vol_scale_common.py` | 按入场 ATR% 缩放仓位 | VOLSCALE／BAND／TAG／KELLYVOL |
| `vol_gate_common.py` | 低波动不开仓 | VOL06 |
| `tag_sizing_common.py` | 按 enter_tag 缩放 | TAGSIZE／TAG12 |
| `equity_stop_common.py` | 单笔权益止损 | ES2／ES3 |
| `time_gate_common.py` | 时间闸门 | TG180／TG240 |
| `partial_tp_common.py` | 分批止盈 | TP2／TP3 |
| `drawdown_governor_common.py` | 回撤降档 | GOV30（未跑） |