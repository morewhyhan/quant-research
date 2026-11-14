# V26 2×2 strategy family

本目录 34 个策略类：四个冻结版本 + 30 个研究变体。文件各管一件事：

| 文件 | 只做一件事 |
| --- | --- |
| 本文件 | 说明目录结构和四个冻结版本 |
| [rules.md](rules.md) | 仓位与恢复退出的定义 |
| [params.md](params.md) | 参数文件、预检、复现、数据位置 |
| [variants.md](variants.md) | 30 个变体：类名 → 改动 → 结论 → 实验 |

## 四个冻结版本

| 策略类 | 仓位 | `loss_half_recovery` | 用途 |
| --- | --- | --- | --- |
| `E0V1E64_V26_GATED_DYNAMIC_RECOVERY` | 动态滚仓 | 开启 | 动态 + 恢复退出 |
| `E0V1E64_V26_GATED_DYNAMIC_NO_RECOVERY` | 动态滚仓 | 关闭 | 动态 + 无恢复退出 |
| `E0V1E64_V26_GATED_FIXED_RECOVERY` | 每次最多 1,000 USDT | 开启 | 固定 + 恢复退出 |
| `E0V1E64_V26_GATED_FIXED_NO_RECOVERY` | 每次最多 1,000 USDT | 关闭 | 固定 + 无恢复退出 |

四个版本的仓位与退出定义见 [rules.md](rules.md)；结果见 [run-006](../../../research/v26-signal-separation/experiments/run-006-v26-2x2-1000/experiment.md)。

## 当前锁定版本

`E0V1E64_V26_BAND_A`，业绩与系数见 [profit-levers 报告](../../../research/profit-levers/report.md)；谱系见 [E0V1E 策略族说明](../README.md)。

这是研究版本，不代表已批准上线。
