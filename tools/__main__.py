"""One offline entry point: python -B -m tools --help."""
from __future__ import annotations
import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    from tools.experiments.planning import KINDS, RELATIONS, preface, parent_record, study_kind
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("analyze", help="Analyze an existing data-only result")
    p.add_argument("input"); p.add_argument("--strategy"); p.add_argument("--output", required=True)
    p = sub.add_parser("compare", help="Compare results and match trades")
    p.add_argument("left"); p.add_argument("right"); p.add_argument("--left-strategy"); p.add_argument("--right-strategy")
    p.add_argument("--tolerance", type=float, default=300); p.add_argument("--output", required=True)
    p = sub.add_parser("check-data", help="Check timezone-aware JSON OHLC")
    p.add_argument("input"); p.add_argument("--output", required=True)
    p = sub.add_parser("demo", help="Synthetic software demonstration, not market performance")
    p.add_argument("input"); p.add_argument("--window", type=int, default=3)
    p.add_argument("--fee", type=float, default=0.001); p.add_argument("--output", required=True)
    p = sub.add_parser("init-study", help="Create a study without overwriting")
    p.add_argument("name")
    p.add_argument("--kind", choices=KINDS, default="strategy")
    p = sub.add_parser("init-experiment", help="Create a non-overwriting experiment plan under a study")
    p.add_argument("study"); p.add_argument("name")
    p.add_argument("--kind", choices=KINDS, help="Defaults to the study's declared type")
    p.add_argument("--parent", help="Previous record or experiment folder, relative to this study's experiments")
    p.add_argument("--relation", choices=RELATIONS, default="followup")
    sub.add_parser("environment", help="Inspect local environment without trading")
    p = sub.add_parser("verify", help="Separate evidence integrity from code-version differences")
    p.add_argument("experiment")
    p = sub.add_parser("engine", help="Run a research-only engine command")
    p.add_argument("name", choices=["freqtrade"])
    p.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "engine":
        from tools.engines.freqtrade.runner import main as run_engine
        return run_engine(args.arguments)
    if args.command == "environment":
        print(json.dumps({"python": platform.python_version(),
                          "freqtrade_importable": importlib.util.find_spec("freqtrade") is not None,
                          "core": "Python standard library only", "live_trading": "not supported"}, indent=2))
        return 0
    if args.command in {"init-study", "init-experiment"}:
        for value in ([args.name] if args.command == "init-study" else [args.study, args.name]):
            if not value or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in value):
                raise ValueError("Use a lowercase ASCII slug")
    if args.command == "init-experiment":
        study = ROOT / "research" / args.study
        if not (study / "report.md").is_file():
            raise ValueError("Study does not exist: create the study first")
        dest = study / "experiments" / args.name
        if dest.exists():
            raise ValueError("Experiment already exists")
        template = (ROOT / "research/EXPERIMENT_TEMPLATE.md").read_text(encoding="utf-8")
        body = preface(args.kind or study_kind(study)) + parent_record(study, dest, args.parent, args.relation) + template
        dest.mkdir(parents=True)
        (dest / "experiment.md").write_text(body, encoding="utf-8")
        print(dest)
        return 0
    if args.command == "init-study":
        dest = ROOT / "research" / args.name
        if dest.exists():
            raise ValueError("Study already exists")
        template = (ROOT / "research/TEMPLATE.md").read_text(encoding="utf-8")
        template = preface(args.kind) + template.replace("../learning/research-scenarios.md", "../../learning/research-scenarios.md")
        index = ROOT / "research/README.md"
        listing = index.read_text(encoding="utf-8")
        lines = listing.splitlines()
        last_row = max(i for i, line in enumerate(lines) if line.startswith("|"))
        lines.insert(last_row + 1, f"| {args.name} | [报告]({args.name}/report.md) | — |")
        dest.mkdir()
        (dest / "report.md").write_text(template, encoding="utf-8")
        index.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(dest)
        return 0
    from tools.experiments.storage import dump, save, verify
    if args.command == "verify":
        result = verify(args.experiment)
        print(dump(result))
        return 0 if result["evidence_intact"] else 1
    if args.command == "analyze":
        from tools.data.research_io import read_result
        from tools.trade_analysis.analysis import analyze
        result = read_result(args.input, args.strategy)
        save(args.output, analyze(result), [args.input], {"trades.json": result["trades"]})
    elif args.command == "compare":
        from tools.data.research_io import read_result
        from tools.trade_analysis.analysis import analyze
        from tools.live_comparison.matching import match_trades
        left, right = read_result(args.left, args.left_strategy), read_result(args.right, args.right_strategy)
        save(args.output, {"left": analyze(left), "right": analyze(right),
                           "matching": match_trades(left["trades"], right["trades"], args.tolerance),
                           "interpretation": "Matched-subset differences are not causal contributions"}, [args.left, args.right])
    else:
        bars = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        if args.command == "check-data":
            from tools.data.research_io import check_bars
            quality = check_bars(bars)
            save(args.output, quality, [args.input])
            return 0 if quality["valid"] else 2
        from tools.engines.synthetic import simulate
        from tools.performance.metrics import trade_metrics, equity_metrics
        result = simulate(bars, args.window, args.fee)
        metrics = {"synthetic_example": True,
                   "configuration": {"window": args.window, "fee_per_side": args.fee, "initial": 1000},
                   "trade_metrics": trade_metrics(result["trades"]), "equity": equity_metrics(result["equity"]),
                   "limitations": "Synthetic long-only next-open example; no leverage/funding/impact; forced final close"}
        save(args.output, metrics, [args.input], {"trades.json": result["trades"], "equity.json": result["equity"], "signals.json": result["signals"]})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Research error: {exc}", file=sys.stderr)
        raise SystemExit(1)
