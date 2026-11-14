# E0V1E 策略族

5 分钟 K 线、OKX USDT 永续、均值回归、单持仓、1 倍杠杆。本文件只做一件事：**列出这条族谱有过哪些版本、代码在哪**。

| 阶段 | 时间 | 版本 | 代码 | 研究结论 |
| ---: | --- | --- | --- | --- |
| 1 | 2026-06 ~ 09 | V1 – V21 | [legacy sources](../../research/legacy-e0v1e/sources/versions/) | [归档报告](../../research/legacy-e0v1e/report.md) |
| 2 | 2026-09 ~ 10 | V26 2×2（四格） | [v26-2x2](v26-2x2/README.md) | [run-006](../../research/v26-signal-separation/experiments/run-006-v26-2x2-1000/experiment.md) |
| 3 | 2026-11-13 | 固定仓位基准 | `FLOOR25_CD6` | [fixed-stake-baseline](../../research/fixed-stake-baseline/report.md) |
| 4 | 2026-11-14 | 收益杠杆（重建） | `F40_FINAL` | [profit-levers](../../research/profit-levers/report.md) |

BAND_A 三年：2024 +272.34%（PF 1.309）、2025 +999.18%（1.651）、2026 +755.82%（1.531）。|

**当前锁定：`E0V1E64_V26_F40_FINAL`**

- 代码：[E0V1E64_V26_F40_FINAL.py](v26-2x2/E0V1E64_V26_F40_FINAL.py)
- 继承链：`F40_FINAL` → `F40_CD6_V25B` → `F40_CD6` → `FLOOR40_RECOVERY` → `GATED_FIXED_RECOVERY`
- 业绩与系数：见 [profit-levers 报告](../../research/profit-levers/report.md)

## 研究纪律（本策略专用）

这条策略目前只有 2025、2026 两年可用数据，所以选参和验证必须分开：

| 角色 | 年份 | 允许做什么 |
| --- | --- | --- |
| **训练** | 2025 | 看结果、比方案、定参数 |
| **验证** | 2026 | 只跑一次，不改任何参数 |
| 2024 及更早 | — | 不作依据：可交易币对少、流动性低 |

1. 选参只用 2025。选择时看 2026，等于用考题做练习，结论作废。
2. 按 2025 的目标函数排序，依次验证，取第一个通过的；不通过就往下，不回头调参。
3. 验证判据在跑 2026 之前写死，例如「PF ≥ 1.40、回撤 ≤ 2025 的 +3 个百分点、收益为正」。
4. 两年效果要接近；收益差一倍或回撤差 10 个百分点，都算不通过。
5. 统计描述也一样：分桶、分组、相关系数只用 2025 算。
6. 不通过的方案保留记录，不改数字。

旧结论 `BAND_A`（2025 +999%、2026 +756%）已作废：它的地基（地板比例、波动阈值）是用 2025 和 2026 合并数据选的。

按协议重建后的当前版本是 `E0V1E64_V26_F40_FINAL`：从干净的「固定＋恢复」起点出发，七层全部只用 2025 训练，2026 只做验证。详见 [profit-levers 报告](../../research/profit-levers/report.md)。

## 下一代怎么加

新建变体类放在 [v26-2x2](v26-2x2/README.md)，在该文件的变体表登记一行；四个 2×2 冻结版本不要改。参数文件被 `.gitignore` 忽略，跑之前执行 `python -B check_params.py`。

这是研究版本，未部署到服务器。