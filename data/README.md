# 数据

目前没有真实数据或数据集记录。

data/datasets 保存来源和范围说明，按[数据集模板](datasets/TEMPLATE.md)填写。原始行情、账户配置和大文件放 data/private，不提交 Git。

需要时再建立：

| 位置 | 内容 |
| --- | --- |
| private/market/ | 原始行情 |
| private/live/ | 实盘记录 |
| private/configs/ | 私有参数与配置 |
| private/results/ | 结果包和分析输出 |

实验必须引用具体数据版本。缺少费用、标记价格或历史币池等信息时，写清缺失和影响，不把文件存在当成数据完整。

公开前检查结果包和配置是否含敏感信息。模板中的人工测试数据在 tests/fixtures，不是市场数据。
