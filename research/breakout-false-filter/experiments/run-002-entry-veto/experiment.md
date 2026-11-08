# 实验 2：简单突破否决完整回测

状态：失败

## 关系

父研究：`research/breakout-false-filter`
前序：`run-001-true-false-breakout`

## 变更

只改一个变量：在 2×2 动态 + 恢复版本上，开仓前 6 根内出现不利方向突破且当前仍在区间外时，禁止该方向开仓。

## 配置

- 策略：`E0V1E64_V26_GATED_DYNAMIC_RECOVERY_BREAKOUT_VETO`
- 配置：`data/private/v26-study/config-2x2-1000.json`
- 本金：1,000 USDT
- 区间：2026-01-01 ～ 2026-10-26 19:15 UTC
- 市场：OKX USDT 永续 5m
- 最大持仓：1
- 杠杆、费用、最大持仓与原 2×2 一致

## 命令（工作区）

```text
freqtrade backtesting --strategy E0V1E64_V26_GATED_DYNAMIC_RECOVERY_BREAKOUT_VETO
  --config data/private/v26-study/config-2x2-1000.json
  --timerange 20260101-20261027
```

## 结果

| 版本 | 交易数 | 收益 | PF | 最大回撤 |
|---|---:|---:|---:|---:|
| 2×2 动态 + 恢复基线 | 878 | +1,503.49% | 1.30 | 38.11% |
| 简单突破否决 | 791 | +365.99% | 1.10 | 67.02% |

## 结论

失败。交易级剔除真突破看起来合理，但完整回测中同时删掉了路径关键盈利单，动态仓位和复利路径被破坏，回撤反而扩大。

## 后续

不要直接上线该否决规则。下一步只在高 P(真突破) 时阻断，并保留低概率假突破。
