"""Research-type prompts and experiment lineage; not execution engines."""
import os
from pathlib import Path
from urllib.parse import quote

KINDS = {
    "mechanism": ("机制", "用公式、手算和反例解释规则，不强填交易指标。"),
    "factor": ("因子", "写清当时知道什么，检查信号后固定时间的涨跌，不用扛单胜率代替预测准确率。"),
    "strategy": ("策略", "比较完整交易、账户变化、成本和仓位，其他条件尽量相同。"),
    "replication": ("复现", "注明原来源，先还原规则，再单独测试改版。"),
    "optimization": ("优化", "记下候选参数、尝试次数和预算，再用未参与选参的数据评价。"),
    "portfolio": ("组合与仓位", "算共享资金、同向风险、调仓和费用，看策略是否会一起亏。"),
    "data": ("数据", "写清来源、覆盖时间、缺失和用途，不强填 PF。"),
    "execution": ("执行", "逐步检查信号、下单、确认、成交和撤单，判断能否按预期成交。"),
    "live": ("实盘诊断", "统一版本、时区、起始持仓和订单，再查差异；选择此类型不授权连接账户或交易。"),
    "robustness": ("稳健性", "换时期、提高成本或检查不利情况，看结果还是否成立。"),
}
RELATIONS = {
    "followup": "后续", "replication": "复现", "supplement": "补测",
    "correction": "修错", "variant": "规则变体", "out-of-sample": "样本外评价",
}


def preface(kind):
    label, focus = KINDS[kind]
    return f"研究类型：{kind}（{label}）\n\n本次重点：{focus}\n\n"


def study_kind(study):
    for line in (Path(study) / "report.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("研究类型："):
            kind = line.split("：", 1)[1].split("（", 1)[0].strip()
            if kind in KINDS:
                return kind
    return "strategy"  # Legacy projects without a declared type keep old behavior.


def parent_record(study, destination, parent, relation):
    if not parent:
        if relation != "followup":
            raise ValueError("--relation requires --parent")
        return "前次实验：无；这是独立起点。\n\n"
    base = (Path(study) / "experiments").resolve()
    supplied = Path(parent)
    if supplied.is_absolute():
        raise ValueError("Parent must be relative to this study's experiments")
    candidate = (base / supplied).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError("Parent escapes this study's experiments")
    if candidate.is_dir():
        candidate = (candidate / "experiment.md").resolve()
    if not candidate.is_relative_to(base):
        raise ValueError("Parent record escapes this study's experiments")
    if not candidate.is_file():
        raise ValueError("Parent experiment record does not exist")
    relative = Path(os.path.relpath(candidate, destination)).as_posix()
    return f"前次实验：[记录]({quote(relative, safe='/._~-')})；关系：{RELATIONS[relation]}。\n\n"
