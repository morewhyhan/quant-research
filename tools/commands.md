# 命令手册

在仓库根目录运行，需要 Python 3.10+。核心工具只用标准库。

## 建研究和实验

~~~powershell
python -B -m tools init-study my-question
python -B -m tools init-experiment my-question run-001
python -B -m tools --help
~~~

研究只创建 report.md，并登记目录。实验创建 experiment.md。已有项目和实验不覆盖。

--kind 可选 mechanism、factor、strategy、replication、optimization、portfolio、data、execution、live、robustness，含义见[按问题选方法](../learning/research-scenarios.md)。

开题默认 strategy，实验默认继承研究类型；旧项目没声明类型时也用 strategy。选择类型只改记录提示，不运行模型或连接账户。

~~~powershell
python -B -m tools init-study my-signal --kind factor
python -B -m tools init-experiment my-signal baseline
python -B -m tools init-experiment my-signal followup --kind robustness --parent baseline --relation supplement
~~~

--parent 指向同项目 experiments 中已有目录或 Markdown 记录。--relation 可选 followup（后续）、replication（复现）、supplement（补测）、correction（修错）、variant（改规则）、out-of-sample（用未参与选参的数据评价）。最后一种仍须说明数据是否真的未参与筛选。

## 检查工具能否运行

~~~powershell
python -B -m unittest discover -s tests -v
python -B -m tools environment
python -B -m tools check-data tests/fixtures/synthetic-bars.json --output data/private/results/check-001
python -B -m tools demo tests/fixtures/synthetic-bars.json --output data/private/results/demo-001
~~~

输入是 JSON 数组，每条含带时区的 date 和正数 open/high/low/close。工具检查价格、时间顺序、重复与间隔。

demo 使用人工价格，仅测试做多、下一根开盘成交、买卖费用和最后平仓。不模拟杠杆、资金费、部分成交或强平，也不代表真实策略业绩。

## 分析自己的结果

以下路径需要换成实际文件；模板不附带回测结果：

~~~powershell
python -B -m tools analyze path/to/result.zip --output data/private/results/analysis-001
python -B -m tools compare path/to/left.zip path/to/right.zip --output data/private/results/compare-001
python -B -m tools verify data/private/results/analysis-001
~~~

支持 Freqtrade ZIP/JSON，也支持交易数组或含 trades 的 JSON。每笔 profit_abs 必须为有效数字。配对还需 pair、布尔值 is_short 和带时区的 open_date；close_date、exit_reason 用于比较退出。

包里有多个策略时，用 --strategy 或 --left-strategy/--right-strategy 指定。工具按左表顺序，为每笔找最近且未配对的交易，不保证全表最优，也不自动查明差异原因。

输出目录必须不存在。每次保存 metrics.json、report.md、manifest.json，按命令另存交易等文件。已建实验的输出可放其中新建的 run/。项目 report.md 写结论，run/report.md 汇总单次计算。

manifest.json 记录所用文件、代码和哈希，供 verify 检查。原文件没变和当前代码没变分开报告，不修改旧哈希来使检查通过。

## 可选：调用 Freqtrade

~~~powershell
python -B -m tools engine freqtrade --version
~~~

先按[配置说明](engines/freqtrade/README.md)安装并配置引擎。只支持研究命令，不启动实盘。
