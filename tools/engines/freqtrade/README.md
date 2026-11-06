# Freqtrade 配置

[runner.py](runner.py)调用自行安装的 Freqtrade，可在本机运行，也可从 Windows 调用 WSL。

模板不含已配置的运行环境或账户设置。参考 [config.example.json](config.example.json)，在同目录创建 config.local.json，填写发行版和 Python 路径。local 文件不提交 Git。

运行 python -B -m tools engine freqtrade --version 检查环境。实际回测还需自己的策略、参数和行情，并记录引擎及依赖版本。

启动器只允许版本检查、策略列表和回测等研究命令，不启动实盘。

回测完成后可用 `python -B -m tools engine --chart-output data/private/results/run-001 freqtrade backtesting ...` 自动导出本次结果并生成 `run-001/charts/`。使用 `--chart-strategy` 选择多策略结果。该流程仍是研究回测：不连接实盘、不下单；图表表示已平仓资金，不等同于含浮盈的实时权益。
