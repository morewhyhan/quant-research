"""Read data-only JSON/ZIP. Never extracts or imports archived strategy code."""
import json
import zipfile
from pathlib import Path
from tools.performance.metrics import number
from tools.data.time import timestamp


def read_result(path, strategy=None):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            candidates = [n for n in archive.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
            records = []
            for name in candidates:
                entry = archive.getinfo(name)
                if entry.file_size > 250_000_000:
                    raise ValueError("Result JSON exceeds 250 MB")
                value = json.loads(archive.read(name))
                if isinstance(value, dict) and isinstance(value.get("strategy"), dict):
                    records.append(value)
            if len(records) != 1:
                raise ValueError("ZIP must contain exactly one Freqtrade results document")
            document = records[0]
    else:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(document, dict) and isinstance(document.get("strategy"), dict):
        choices = document["strategy"]
        if strategy is None:
            if len(choices) != 1:
                raise ValueError("Multiple strategies: specify --strategy")
            strategy = next(iter(choices))
        if strategy not in choices:
            raise ValueError(f"Strategy not present: {strategy}")
        result = choices[strategy]
        trades = result["trades"]
        engine = {k: result.get(k) for k in ("profit_total", "profit_factor", "max_drawdown_account", "backtest_start", "backtest_end", "starting_balance")}
    else:
        trades = document if isinstance(document, list) else document["trades"]
        engine = {}
    if not isinstance(trades, list) or any(not isinstance(t, dict) for t in trades):
        raise ValueError("trades must be a list of objects")
    for trade in trades:
        number(trade["profit_abs"], "profit_abs")
    return {"strategy": strategy, "trades": trades, "engine_reported": engine}


def check_bars(bars):
    errors, warnings, dates = [], [], []
    if not isinstance(bars, list) or not bars:
        return {"valid": False, "rows": 0, "errors": ["Expected a nonempty list of OHLC bars"], "warnings": []}
    for i, bar in enumerate(bars):
        try:
            date = timestamp(bar["date"])
            o, h, low, c = [number(bar[key], key) for key in ("open", "high", "low", "close")]
            if min(o, h, low, c) <= 0 or h < max(o, low, c) or low > min(o, h, c):
                raise ValueError("invalid positive OHLC bounds")
            if dates and date <= dates[-1]:
                errors.append(f"row {i}: timestamps are duplicate or not increasing")
            dates.append(date)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"row {i}: {exc}")
    if len(dates) > 2:
        gaps = [(b-a).total_seconds() for a,b in zip(dates, dates[1:])]
        if len(set(gaps)) > 1:
            warnings.append("Irregular time spacing: investigate missing bars and sampling")
    return {"valid": not errors, "rows": len(bars), "errors": errors, "warnings": warnings,
            "limitations": "No proof of historical universe, revisions, funding, volume, or information availability"}
