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

## 生成入场快照（可选 pandas 环境）

入场快照只读已有 Freqtrade 归档和本地 OHLCV，不导入策略、不访问交易所。`YEAR=PATH` 的年份必须和交易归档、数据根目录一一对应：

~~~powershell
python -B -m tools.trade_analysis.snapshots `
  --archive 2024=path/to/2024.zip --archive 2025=path/to/2025.zip --archive 2026=path/to/2026.zip `
  --data-root 2024=path/to/okx_2024 --data-root 2025=path/to/okx_2025 --data-root 2026=path/to/okx_2026 `
  --output data/private/results/v26-snapshots-001
python -B -m tools.trade_analysis.candidate_eval `
  data/private/results/v26-snapshots-001/snapshots.csv `
  --output data/private/results/v26-snapshots-001
~~~

快照使用开仓时间之前最后一根已闭合 5m K 线；筛选诊断不模拟被过滤后腾出的仓位，也不替代完整回测。

## 自动生成资金曲线和回撤图

`chart` 直接读取已有 Freqtrade ZIP/JSON，生成同一目录下的 `equity-drawdowns.png`、SVG、每条曲线的 CSV、`metrics.json`、`report.md` 和 `manifest.json`。它按平仓 `profit_abs` 累加，不给历史交易重新定价；图中是已平仓资金，不含浮动盈亏或充提调整。每个输入独立使用自己的起始资金，金额刻度独立，回撤刻度统一。

~~~powershell
python -B -m tools chart path/to/v26-2024.zip path/to/v26-2025.zip path/to/v26-2026.zip `
  --strategy E0V1E64_V26 --strategy E0V1E64_V26 --strategy E0V1E64_V26 `
  --label "V26 2024" --label "V26 2025" --label "V26 2026" `
  --output data/private/results/v26-chart-001
~~~

`--initial` 可按输入顺序显式指定起始资金；只有在研究确实要改变资金口径时才使用。Freqtrade 导出的无时区回测起止字段按 UTC 解释，逐笔交易仍要求带时区的成交时间。若 ZIP 含多个策略，必须为对应输入指定 `--strategy`。输出目录已存在时命令拒绝覆盖。

如果希望回测完成后自动生成图：

~~~powershell
python -B -m tools engine --chart-output data/private/results/v26-run-001 `
  --chart-strategy E0V1E64_V26 freqtrade backtesting --config path/to/config.json `
  --strategy E0V1E64_V26 --timerange 20240101-20250101
~~~

`--chart-output` 只接受 `backtesting`，自动拥有导出路径，并且只对这次运行生成的结果作图；回测失败不会生成图。绘图依赖是可选的：`pip install -r tools/performance/requirements-charts.txt`。核心分析和测试不依赖 matplotlib。

## 可选：调用 Freqtrade

~~~powershell
python -B -m tools engine freqtrade --version
~~~

先按[配置说明](engines/freqtrade/README.md)安装并配置引擎。只支持研究命令，不启动实盘。
