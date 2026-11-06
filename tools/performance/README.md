# 收益与风险计算

[metrics.py](metrics.py)计算胜率、PF、平均盈亏、盈亏金额的标准差、大额亏损占比，以及账户收益和从高点下跌的比例。没有亏损时 PF 返回 null。

分析直接使用存档中的 profit_abs，不重新计算费用和资金费。原回测程序的总收益和回撤另外列出，不冒充工具已重新算过。

盈亏金额的波动不是每日收益率的波动。工具没有用间隔不规则的交易记录计算年化夏普，也不能把单笔收益率直接相加当成复利收益。

用法见[命令手册](../commands.md)，公式见[收益、EV 与 PF](../../learning/returns-and-pf.md)。

`charts.py` 只使用结果包中的已平仓 `profit_abs`，按 UTC 平仓时间分组后累加，避免同一时间多笔交易因文件顺序造成虚假的峰值和回撤。它不会用 K 线重新估值，也不会把充提、浮动仓位或资金费缺失补成账户权益。图表依赖 matplotlib，见 [requirements-charts.txt](requirements-charts.txt)。
