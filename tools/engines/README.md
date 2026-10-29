# 研究引擎

- [Freqtrade](freqtrade/README.md)：手动指定的外部引擎，只开放研究命令。
- [synthetic.py](synthetic.py)：人工数据上的极简执行时序示例，复用动量计算；不是生产策略或完整历史行情回测器。

统一通过[命令入口](../commands.md)调用。引擎配置留在对应适配器内，不散落 tools 根目录。
