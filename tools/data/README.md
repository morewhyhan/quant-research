# 数据读取与检查

[research_io.py](research_io.py)读取 Freqtrade ZIP/JSON 或按指定格式整理的交易 JSON，不执行包内策略代码。它检查开盘、最高、最低和收盘价（OHLC）是否合理，时间是否有序、重复或间隔异常。[time.py](time.py)统一处理带时区的时间。

这里只放通用数据处理。数据来源与缺失见 [data](../../data/README.md)，操作见[命令手册](../commands.md)。

momentum.py 和 volatility.py 是示例工具与测试所用的基础计算，不是预装的真实因子研究。
