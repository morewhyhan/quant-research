# 实验保存与报告

- [storage.py](storage.py)：只创建新输出目录，记录输入、当次研究代码和输出文件的校验值；核对时区分证据完整与代码版本差异。
- [planning.py](planning.py)：研究类型提示与前次实验关联，检查关联路径和记录存在；不执行回测或模型。
- [report.py](report.py)：把计算结果整理成 Markdown，不修改原始结果，不额外推导交易优势。

保存的输出文件归属于对应研究，不放在工具源码目录。公开可分享的小型证据可以放 research/<问题>/experiments/<实验>；私密或大型输出文件放 data/private/results，并从实验说明链接过去。
