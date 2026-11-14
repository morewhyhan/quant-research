# 参数、复现与数据位置

## 参数文件（缺了会静默跑成另一套策略）

每个策略类各需要一份同名参数文件，放在本目录。根目录 `.gitignore` 的 `/strategies/**/*.json` 会把它们全部忽略，公开克隆里没有这些文件，必须从私有区或生产部署包复制，并且 JSON 里的 `strategy_name` 要等于类名。

缺少时 Freqtrade 不报错，直接用类里的默认值运行。默认值和研究参数不在一个量级：`buy_rsi_fast_period` 是 10 对 183、`buy_rsi_period` 20 对 47、`buy_rsi_slow_period` 40 对 81、`short_cti_32` 0.31 对 −0.66。

2026-11-13 复现时踩到过：全用默认值跑 2026 全年得到 1,428 笔、+59.72%、回撤 75.94%；换回研究参数后是 878 笔、+417.66%、回撤 9.72%，与 run-006 逐项一致。

跑之前先预检：

```bash
python -B strategies/e0v1e/v26-2x2/check_params.py
```

脚本只读目录和 JSON；缺文件或 `strategy_name` 不匹配时返回 1，并列出是哪几份。

## 依赖和复现

回测时把本目录作为 Freqtrade 的 `--strategy-path`，显式指定一个策略类；不要加载实盘配置，不要用此目录启动 live 或 dry-run bot。

完整命令、区间、本金、费用和数据范围写在对应的实验记录里，不写在这里。

## 数据与结果在哪

| 内容 | 位置 |
| --- | --- |
| 2024 行情 | `user_data/data/okx_2024`（143 对，全年） |
| 2025 行情 | `user_data/data/okx_2025_full_server_archive`（196 对） |
| 2026 行情 | `user_data/data/okx_2026_combined`（345 对，到 10-26） |
| 回测原始结果 | 仓库外 `backtest_results/`（zip + meta），按实验记录里写的时间戳对应 |
| 私有配置 | `quant-research/data/private/v26-study/`（gitignored） |
