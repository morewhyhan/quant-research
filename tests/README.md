# 软件测试

~~~powershell
python -B -m unittest discover -s tests -v
~~~

测试通用计算、交易配对、文件读写、命令和文档链接，不依赖真实策略或账户。

- test_research_basics.py：基础价格与波动计算。
- test_pipeline.py：PF、回撤、配对、时间、示例成交和防覆盖。
- test_repository.py：目录、链接、命令和文件校验。
- test_research_scenarios.py：研究类型与前次实验关联。
- test_methodology_translation.py：可选流程原文的文件校验，以及译文的章节、表格、数字和代码路径检查；不代替人工审译。
- fixtures/：人工数据，只用于软件测试。

测试在临时目录生成运行结果，不预填真实研究，也不把测试通过解释为策略盈利。
