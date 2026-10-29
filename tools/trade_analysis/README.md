# 逐笔交易分析

[analysis.py](analysis.py)按币种、方向和退出原因分组，汇总每笔盈亏，并列出原回测程序的统计。公式统一放在 [performance](../performance/README.md)。

比较两组交易用 [live_comparison](../live_comparison/README.md)。想知道一笔持仓中途最多浮亏或浮盈多少（MAE/MFE），需要持仓期间的价格，不能只看成交记录。

用法见[命令手册](../commands.md)。
