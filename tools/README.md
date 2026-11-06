# 研究工具

在仓库根目录用 python -B -m tools 运行。完整命令见[命令手册](commands.md)。

| 目录 | 做什么 | 主要文件 |
| --- | --- | --- |
| data | 读取结果，检查开盘、最高、最低、收盘价和时间 | research_io.py、time.py |
| performance | 计算盈亏、PF、回撤，并从 Freqtrade 结果生成资金曲线图 | metrics.py、charts.py |
| trade_analysis | 按币种、方向和退出原因分组；生成无未来数据的入场快照 | analysis.py、snapshots.py、candidate_eval.py |
| live_comparison | 配对两组交易，比较时间差 | matching.py |
| experiments | 建实验记录，保存报告并检查文件 | planning.py、storage.py、report.py |
| engines | 调用 Freqtrade 或运行人工示例 | freqtrade/runner.py、synthetic.py |

__main__.py 负责分发命令，软件测试放在 [tests](../tests/README.md)。研究方法见[按问题选方法](../learning/research-scenarios.md)。

## 已有功能

读取 Freqtrade ZIP/JSON，分析每笔交易和分组结果，配对交易，检查 JSON 行情，生成报告。

verify 分别检查原始文件是否完整、当前代码是否还是当时版本。代码更新不等于旧结果损坏；文件没变也不代表研究结论一定正确。

## 还不能做什么？

现有分析不能自动查清实盘差异，也不能补出缺失的真实费用、资金费和滑点。人工示例不是实际行情回测。

因子 IC（指标与未来收益的相关性）、模型训练、PBO（估计反复选参造成的过拟合）、组合优化、完整期权回测和盘口重放，尚无专用工具。自动监控和实盘交易也未实现。

Freqtrade 仍借用外部安装环境，换电脑后需要重新配置。

资金曲线图是可选能力。安装 `performance/requirements-charts.txt` 后，`python -B -m tools chart ...` 可复用地生成已平仓资金、回撤和 CSV 数据；`engine --chart-output ... freqtrade backtesting ...` 可在一次回测成功后自动接上同一流程。

入场快照和候选筛选诊断需要外部 Freqtrade 环境里已有的 pandas/pyarrow；它们只读取归档和本地 K 线，不连接交易所。
