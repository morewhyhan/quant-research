# Freqtrade 配置

[runner.py](runner.py)调用自行安装的 Freqtrade，可在本机运行，也可从 Windows 调用 WSL。

模板不含已配置的运行环境或账户设置。参考 [config.example.json](config.example.json)，在同目录创建 config.local.json，填写发行版和 Python 路径。local 文件不提交 Git。

运行 python -B -m tools engine freqtrade --version 检查环境。实际回测还需自己的策略、参数和行情，并记录引擎及依赖版本。

启动器只允许版本检查、策略列表和回测等研究命令，不启动实盘。
