"""检查 V26 2x2 策略族的参数文件是否齐备。

仓库的 .gitignore 忽略 /strategies/**/*.json，参数文件只保存在私有区。
Freqtrade 找不到 <类名>.json 时不会报错，会用类里的默认值运行，跑出来是另一套策略。

用法（仓库根目录）：
    python -B strategies/e0v1e/v26-2x2/check_params.py

返回 0 表示齐全；返回 1 表示缺文件或 strategy_name 与类名不一致。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "E0V1E64_V26_GATED_"

PRIVATE_HINT = "data/private/v26-study/strategies/"


def problems_for(name: str) -> str | None:
    path = HERE / f"{name}.json"
    if not path.is_file():
        return f"缺少 {path.name}，Freqtrade 会用类默认值运行"
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return f"{path.name} 解析失败：{exc}"
    declared = payload.get("strategy_name")
    if declared != name:
        return f"{path.name} 的 strategy_name 是 {declared!r}，应等于类名"
    return None


def main() -> int:
    names = sorted(path.stem for path in HERE.glob(PREFIX + "*.py"))
    if not names:
        print(f"没有在 {HERE} 找到 {PREFIX}*.py 策略类")
        return 1

    failures = {name: reason for name in names if (reason := problems_for(name))}
    for name in names:
        print(f"FAIL {name}: {failures[name]}" if name in failures else f"OK   {name}")

    if not failures:
        print("\n参数文件齐全。")
        return 0

    print(f"\n{len(failures)} 个策略缺少可用参数文件，不要在这种状态下跑回测。")
    print(f"把 {PRIVATE_HINT} 下的同名 JSON 复制到本目录，或从生产部署包取。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
