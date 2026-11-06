# V26 开仓前信号快照

状态：完成

方法：严格无未来数据的开仓快照生成

前次实验及关系：补测；基于 [run-001](../run-001-archive-audit/experiment.md)

## 这次要查什么？

把每笔历史入场当时可见的环境保存下来，为后续分支、市场状态和同步信号研究提供统一输入。只记录，不改变交易。

## 用什么代码和数据？

- 工具：[snapshots.py](../../../../tools/trade_analysis/snapshots.py)。
- 输入：三段 V26 Freqtrade ZIP 与相应 OKX 5m Feather 数据。
- 严格规则：取 `open_date` 之前最后一根已闭合 5m K 线；缺失值保留为空。

## 怎样运行？得到什么？

- 生成 2,750 行快照，币种特征缺失数为 0。
- 每行包含四类 `enter_tag`、方向、收益结果、BTC/币自身 1h/4h/24h 收益、SMA46/120/240 距离、24h 波动、信号簇规模和开仓前已平仓账户状态。
- 私有产物：`data/private/results/v26-signal-snapshots-002/`。
- 筛选诊断：`candidate-filter-only.json`。它只对已经成交的交易做条件筛选，不模拟释放仓位后的替代交易。

## 问题与决定

快照足以检验 BTC 状态与入场分支的交互，但不能把 MFE、MAE、退出原因和最终收益当作入场特征。候选规则必须走完整 Freqtrade 回测。
