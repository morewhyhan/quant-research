# BTC 24 小时收益 × 入场分支：有效性复核

状态：完成

方法：robustness（稳健性）+ factor（因子验证）

前次实验：[run-007 BTC 24 小时收益因子审计](../run-007-factor-btc-ret24/experiment.md)；关系：用冻结定义做时间外评价。

## 这次要查什么？

这次不重新选阈值，只检验已冻结的两个分支规则能否称为有效因子：

```text
short_new: btc_ret_24h >= +1.5405078726%
buy_1:     btc_ret_24h >= -3.0291256167%
```

比较每个分支的“接受组”和“阻断组”在 2025、2026 的平均单笔收益差，并按开仓日期做 bootstrap，避免把同一天的同步信号当成完全独立样本。

严格通过条件在运行前固定为：

1. 2025、2026 两个时间外年度的平均收益差都大于 0；
2. 两年合并后的日期簇 bootstrap 95% 区间下界大于 0。

这个条件只回答“条件分离是否稳定”，不等价于完整账户 alpha；完整账户还需要模拟过滤后释放的持仓位和替代交易。

## 用什么代码和数据？

- 因子定义代码：[factor.py](../../../../factors/btc-ret24-entry-gate/factor.py)
- 本次验证代码：[validate.py](../../../../factors/btc-ret24-entry-gate/validate.py)
- 输入：[snapshots.csv](../../../../data/private/results/v26-signal-snapshots-002/snapshots.csv)
- 输入内容：V26 三段归档的 2,750 笔已执行交易，包含入场前 BTC 24h 收益、`enter_tag` 和 Freqtrade `profit_ratio`。
- 时间：2024、2025、2026（2026 数据截至归档的 2026-10-26）；时间戳为 UTC。
- 交易所和市场：原归档的 OKX USDT 合约，5m 决策尺度。
- 成交假设：直接使用原 Freqtrade 归档结果；原始费用已反映在 `profit_ratio`，本次没有重新构造滑点或资金费。
- 杠杆与本金：本次是入场快照统计，不重新模拟账户，不适用本金和杠杆参数。

## 怎样运行？得到什么？

实际命令（WSL Ubuntu，Python 3.12.3）：

```text
wsl.exe --distribution Ubuntu -- python3 -B factors/btc-ret24-entry-gate/validate.py data/private/results/v26-signal-snapshots-002/snapshots.csv --output data/private/results/v26-factor-btc-ret24-validation-001
```

输出：

- [metrics.json](../../../../data/private/results/v26-factor-btc-ret24-validation-001/metrics.json)
- [block-metrics.csv](../../../../data/private/results/v26-factor-btc-ret24-validation-001/block-metrics.csv)
- [机器生成摘要](../../../../data/private/results/v26-factor-btc-ret24-validation-001/report.md)
- [manifest.json](../../../../data/private/results/v26-factor-btc-ret24-validation-001/manifest.json)

### 样外年度结果

| 分支 | 年份 | 接受／阻断 | 接受均值 | 阻断均值 | 差值 | 日期簇 bootstrap 95% 区间 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `short_new` | 2025 | 19 / 27 | +1.1649% | +0.2920% | +0.8728% | −1.9526% ～ +3.4956% |
| `short_new` | 2026 | 21 / 33 | +0.1163% | −1.4097% | +1.5260% | −1.7138% ～ +4.2822% |
| `buy_1` | 2025 | 165 / 12 | +0.2832% | −1.9672% | +2.2504% | −1.5159% ～ +7.6023% |
| `buy_1` | 2026 | 166 / 11 | +0.7113% | +0.8878% | −0.1765% | −1.9255% ～ +1.4490% |

合并 2025—2026 后：

- `short_new` 差值 +1.2583%，95% 区间 −0.8365% ～ +3.0647%；
- `buy_1` 差值 +1.0997%，95% 区间 −1.1037% ～ +3.8999%。

## 问题与决定

### 结果

- `short_new` 在两个样外年度方向一致，但置信区间跨 0，严格条件未通过；
- `buy_1` 在 2026 年反转，严格条件未通过；
- 完整冻结门控回测的改善不能单独证明因子 alpha，因为过滤会改变持仓容量和替代交易；
- 本次没有发现足够证据把它升级为“已验证有效因子”。

### 决定

因子仓库继续保留 `btc_ret_24h`，但状态保持“候选因子”。最值得继续验证的是 `short_new` 的分支条件；`buy_1` 不再被描述为稳定条件。没有通过真正未触碰的 forward、纸交易、滑点/资金费和容量检查前，不把它接入实盘杠杆逻辑。

### 未执行的阶段

- 没有新建 `short_new-only` 的完整 Freqtrade 账户回测；
- 没有接入服务器、纸交易或真实下单；
- 没有重选阈值，也没有把回测最优阈值重新调高。

这次实验的“失败”不是程序失败，而是严格有效性门槛没有通过；旧结果和本次结果都保留。
