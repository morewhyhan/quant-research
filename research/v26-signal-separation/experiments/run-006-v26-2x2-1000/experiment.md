研究类型：strategy（策略）

本次重点：在冻结入场门控上，比较动态／固定仓位和恢复／无恢复退出的四组完整回测。

前次实验：[记录](../run-005-no-recovery-1000/experiment.md)；关系：后续。

# V26 2×2 仓位与恢复退出对照（1,000 USDT）

状态：完成

## 这次要查什么？

本次只比较两个变量：

1. 动态滚仓，还是每笔目标 1,000 USDT 的固定仓位；
2. 是否保留 `loss_half_recovery`。

四组都从 1,000 USDT 开始。这样可以把已经冻结的入场条件改善，和仓位／退出规则的影响分开看。

## 四个策略

代码入口在 [`strategies/e0v1e/v26-2x2/`](../../../../strategies/e0v1e/v26-2x2/README.md)。四个最终类如下：

| 策略类 | 仓位 | `loss_half_recovery` | 参数 |
| --- | --- | --- | --- |
| `E0V1E64_V26_GATED_DYNAMIC_RECOVERY` | V9 动态滚仓 | 开启 | `E0V1E64_V26_GATED_DYNAMIC_RECOVERY.json` |
| `E0V1E64_V26_GATED_DYNAMIC_NO_RECOVERY` | V9 动态滚仓 | 关闭 | `E0V1E64_V26_GATED_DYNAMIC_NO_RECOVERY.json` |
| `E0V1E64_V26_GATED_FIXED_RECOVERY` | 每笔最多 1,000 USDT | 开启 | `E0V1E64_V26_GATED_FIXED_RECOVERY.json` |
| `E0V1E64_V26_GATED_FIXED_NO_RECOVERY` | 每笔最多 1,000 USDT | 关闭 | `E0V1E64_V26_GATED_FIXED_NO_RECOVERY.json` |

四个版本都保留同一个冻结入场改动：`short_new` 要求 BTC 过去 24 小时收益率不低于 `+1.5405078726%`，`buy_1` 要求不低于 `−3.0291256167%`；状态取入场前最后一根已闭合 5m K 线。其他入场分支不改。

固定仓位的实际实现是 `min(1000, max_stake)`。余额高于 1,000 时不随账户继续放大；余额低于 1,000 时使用 Freqtrade 允许的剩余金额。因此“固定”是固定目标金额，不是保证每次都能成交 1,000。

## 用什么代码和数据？

- 交易所和市场：OKX USDT 隔离合约
- 数据：本机 Freqtrade 5m 数据，交易池为配置中的历史列表
- 区间：2026-01-01 00:00 至 2026-10-26 19:15 UTC（命令结束日期写作 `20261027`）
- 初始资金：1,000 USDT
- 最大持仓：1
- 杠杆：沿用研究配置，为 2 倍
- 费用、止损和其他策略参数：四组完全相同，来自各自 JSON 参数文件
- 回测引擎：Freqtrade 2026.5.1
- 私有配置：`data/private/v26-study/config-2x2-1000.json`

## 怎样运行？得到什么？

实际运行的命令为：

```text
freqtrade backtesting -c data/private/v26-study/config-2x2-1000.json \
  --strategy-path strategies/e0v1e/v26-2x2 \
  --strategy-list E0V1E64_V26_GATED_DYNAMIC_RECOVERY E0V1E64_V26_GATED_DYNAMIC_NO_RECOVERY \
    E0V1E64_V26_GATED_FIXED_RECOVERY E0V1E64_V26_GATED_FIXED_NO_RECOVERY \
  --datadir /mnt/c/Users/why/Desktop/ft_userdata/user_data/data/okx_2026_combined \
  --timeframe 5m --timerange 20260101-20261027 --max-open-trades 1 \
  --dry-run-wallet 1000 --export trades --enable-protections --cache day
```

原始结果保存在私有目录：

- `data/private/results/v26-2x2-2026-1000-001/engine/backtest-result-2026-11-06_22-58-14.zip`
- `data/private/results/v26-2x2-2026-1000-001/engine/backtest-result-2026-11-06_22-58-14.meta.json`

下表使用 Freqtrade 的钱包账户口径。收益率是 `(最终余额 / 1,000) - 1`，最大回撤是账户余额从峰值到谷值的最大相对跌幅。

| 策略 | 交易数 | 胜率 | 最终余额 | 收益率 | Profit Factor | 最大账户回撤 | 最大连续亏损 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 动态 + 恢复 | 878 | 75.4% | 16,034.85 | +1,503.49% | 1.30 | 38.11% | 4 |
| 动态 + 无恢复 | 699 | 85.6% | 11,912.53 | +1,091.25% | 1.34 | 27.61% | 3 |
| 固定 + 恢复 | 878 | 75.4% | 5,176.60 | +417.66% | 1.51 | 9.72% | 4 |
| 固定 + 无恢复 | 699 | 85.6% | 4,732.24 | +373.22% | 1.56 | 28.97% | 3 |

四组的交易数和胜负数成对相同：是否恢复退出改变了交易路径和持仓容量；仓位方式只改变资金曲线的金额尺度。固定版本的实际成交仓位范围约为 866.02—1,000 USDT（无恢复）和 987.24—1,000 USDT（恢复）。

四组横向研究报告由仓库的 `report` 工具生成。HTML 内嵌所有图表，沿用原先白底、网格和中文标注的图表风格：

- [`report.html`](../../../../data/private/results/v26-2x2-2026-1000-001/html-report-003/report.html)

HTML 同目录保留可复核数据：

- [`metrics.json`](../../../../data/private/results/v26-2x2-2026-1000-001/html-report-003/metrics.json)
- [`manifest.json`](../../../../data/private/results/v26-2x2-2026-1000-001/html-report-003/manifest.json)
- [`curve-1.csv`—`curve-4.csv`](../../../../data/private/results/v26-2x2-2026-1000-001/html-report-003/)

图中的回撤是“已平仓资金曲线”口径，动态无恢复、固定恢复的图表回撤分别为约 31.77%、25.50%，与 Freqtrade 钱包回撤 27.61%、9.72% 不同。图表不含浮动盈亏和外部充提，不能直接拿去和实盘权益曲线逐点相减。

## 问题与决定

1. **固定仓位显著抑制滚仓造成的资金曲线放大。** 开启恢复退出时，动态版本的账户回撤为 38.11%，固定版本为 9.72%；收益也从 +1,503.49% 降到 +417.66%。这正是仓位风险和信号质量分开的证据。
2. **无恢复退出的胜率更高，但不等于尾部风险消失。** 两个无恢复版本都是 85.6% 胜率、最多连续亏损 3 笔，但固定无恢复的最大账户回撤仍为 28.97%。
3. **恢复退出提高了交易数量，却降低了平均胜率。** 它较早结束部分亏损持仓，释放唯一持仓位；因此它会改变后续信号能否进场，不是单纯的“止损开关”。
4. **当前最平衡的历史版本是固定 + 恢复，而不是收益最高的动态 + 恢复。** 这个判断只针对本次 2026 回测的风险控制，不是未来收益承诺，也不能代替 forward 或纸交易。

## 限制

- 这是同一历史区间的回测，不能证明未来稳定。
- 数据不能重建真实盘口、资金费、滑点和 K 线内成交先后；配置中未额外补造这些缺失项。
- 交易池是历史配置列表，存在上市时间和幸存者偏差。
- 图表是闭合资金，不含未平仓浮盈亏；Freqtrade 回撤是钱包账户口径，二者必须分开读。
- 入场门控阈值已经由历史数据校准，不能把这次结果当作独立样本外验证。

## 下一步

先不要把任一版本直接替换实盘。下一步应使用同一四组版本做独立 forward／paper trading，记录资金费、滑点、成交延迟、同步信号簇和未平仓权益；如果仍需控制连续亏损，优先从固定仓位 + 风险熔断继续验证，而不是直接增加更多入场过滤器。
