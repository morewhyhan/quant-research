# 逐笔交易分析

[analysis.py](analysis.py)按币种、方向和退出原因分组，汇总每笔盈亏，并列出原回测程序的统计。公式统一放在 [performance](../performance/README.md)。

比较两组交易用 [live_comparison](../live_comparison/README.md)。想知道一笔持仓中途最多浮亏或浮盈多少（MAE/MFE），需要持仓期间的价格，不能只看成交记录。

研究入场环境时，用 [snapshots.py](snapshots.py) 从 Freqtrade 归档和本地 5m K 线生成开仓前快照。它严格取 `open_date` 之前的最后一根已闭合 K 线，并把缺失保留为 null。用 [candidate_eval.py](candidate_eval.py) 可以把冻结的入场门控应用到已成交表做筛选诊断；这不是完整回测，不能替代 Freqtrade 的结果。

用法见[命令手册](../commands.md)。
