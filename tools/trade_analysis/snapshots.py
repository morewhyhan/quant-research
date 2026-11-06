"""Build entry-time, no-lookahead snapshots for archived Freqtrade trades.

This module is deliberately data-only.  It reads Freqtrade result archives and
local OHLCV files; it never imports a strategy or contacts an exchange.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import pandas as pd

from tools.data.research_io import read_result


def _pair_filename(pair: str) -> str:
    return pair.replace("/", "_").replace(":", "_") + "-5m-futures.feather"


def _read_candles(path: Path) -> pd.DataFrame:
    frame = pd.read_feather(path)
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame = frame.sort_values("date").drop_duplicates("date").set_index("date")
    close = frame["close"].astype(float)
    log_return = close.pct_change().where(close.gt(0))
    frame["ret_1h"] = close / close.shift(12) - 1
    frame["ret_4h"] = close / close.shift(48) - 1
    frame["ret_24h"] = close / close.shift(288) - 1
    for window in (46, 120, 240):
        frame[f"sma{window}_gap"] = close / close.rolling(window).mean() - 1
    frame["vol_24h"] = log_return.rolling(288).std()
    return frame


def _at_or_before_strict(frame: pd.DataFrame, when: pd.Timestamp) -> pd.Series | None:
    """Return the last fully closed candle strictly before an entry timestamp."""
    position = frame.index.searchsorted(when, side="left") - 1
    if position < 0:
        return None
    return frame.iloc[position]


def _entry_equity(trades: list[dict], starting_balance: float) -> tuple[list[float], list[float]]:
    ordered = sorted(
        trades,
        key=lambda row: (pd.Timestamp(row["close_date"], tz="UTC"), pd.Timestamp(row["open_date"], tz="UTC")),
    )
    balance = float(starting_balance)
    peak = balance
    closed = []
    rows = []
    for row in ordered:
        balance += float(row["profit_abs"])
        peak = max(peak, balance)
        closed.append((pd.Timestamp(row["close_date"], tz="UTC"), balance, peak))
    for row in trades:
        opened = pd.Timestamp(row["open_date"], tz="UTC")
        prior = [item for item in closed if item[0] < opened]
        if prior:
            _, value, high = prior[-1]
        else:
            value, high = starting_balance, starting_balance
        rows.append((value, 1 - value / high if high else 0.0))
    return [row[0] for row in rows], [row[1] for row in rows]


def _archive_metadata(path: Path, strategy: str) -> tuple[list[dict], dict]:
    result = read_result(path, strategy)
    return result["trades"], result["engine_reported"]


def build_snapshots(
    archives: dict[str, Path],
    data_roots: dict[str, Path],
    output: Path,
    strategy: str = "E0V1E64_V26",
) -> dict:
    """Write ``snapshots.csv`` and a manifest; return the manifest."""
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    files_read: set[str] = set()
    missing: Counter[str] = Counter()

    for year, archive in sorted(archives.items()):
        trades, engine = _archive_metadata(archive, strategy)
        root = data_roots[year]
        btc_path = root / "futures" / "BTC_USDT_USDT-5m-futures.feather"
        btc = _read_candles(btc_path)
        files_read.add(str(btc_path))
        coin_cache: dict[str, pd.DataFrame | None] = {}
        ordered = sorted(trades, key=lambda row: (row["open_date"], row["close_date"]))
        entry_equity, entry_dd = _entry_equity(ordered, float(engine.get("starting_balance") or 0))
        cluster_counts = Counter((row["open_date"], row.get("enter_tag", "")) for row in ordered)
        for trade, equity, drawdown in zip(ordered, entry_equity, entry_dd):
            opened = pd.Timestamp(trade["open_date"], tz="UTC")
            btc_row = _at_or_before_strict(btc, opened)
            pair = str(trade["pair"])
            coin_path = root / "futures" / _pair_filename(pair)
            coin = None
            if coin_path.is_file():
                cache_key = str(coin_path)
                if cache_key not in coin_cache:
                    coin_cache[cache_key] = _read_candles(coin_path)
                    files_read.add(cache_key)
                coin = coin_cache[cache_key]
            else:
                missing[_pair_filename(pair)] += 1
            coin_row = _at_or_before_strict(coin, opened) if coin is not None else None
            row = {
                "year": int(year),
                "pair": pair,
                "side": "short" if trade.get("is_short") else "long",
                "enter_tag": trade.get("enter_tag", ""),
                "open_date": opened.isoformat(),
                "close_date": pd.Timestamp(trade["close_date"], tz="UTC").isoformat(),
                "profit_ratio": float(trade["profit_ratio"]),
                "profit_abs": float(trade["profit_abs"]),
                "exit_reason": trade.get("exit_reason", ""),
                "entry_closed_equity": equity,
                "entry_drawdown": drawdown,
                "stake_exposure": float(trade.get("stake_amount", 0) or 0) / equity if equity else None,
                "cluster_size_same_timestamp_tag": cluster_counts[(trade["open_date"], trade.get("enter_tag", ""))],
            }
            for prefix, source in (("btc", btc_row), ("coin", coin_row)):
                for name in ("ret_1h", "ret_4h", "ret_24h", "sma46_gap", "sma120_gap", "sma240_gap", "vol_24h"):
                    row[f"{prefix}_{name}"] = None if source is None else float(source[name]) if pd.notna(source[name]) else None
            rows.append(row)

    frame = pd.DataFrame(rows).sort_values(["open_date", "year", "pair"]).reset_index(drop=True)
    frame.to_csv(output / "snapshots.csv", index=False)
    manifest = {
        "strategy": strategy,
        "archives": {year: str(path) for year, path in archives.items()},
        "data_roots": {year: str(path) for year, path in data_roots.items()},
        "rows": len(frame),
        "missing_coin_files": dict(missing),
        "files_read": len(files_read),
        "lookahead_rule": "For every trade, use the last 5m candle with date strictly before open_date.",
        "features": [
            "BTC and coin return over 1h, 4h, 24h",
            "BTC and coin distance from 46/120/240-period SMA",
            "BTC and coin 24h rolling 5m return volatility",
            "same-timestamp and same-entry-tag cluster size",
            "closed-equity state before entry",
        ],
        "limitations": [
            "A snapshot describes information available before the archived entry; it does not rerun the strategy.",
            "Missing candles remain null; they are not filled with future values.",
            "MFE, MAE, exit reason and profit are outcomes and must not be used as entry features.",
            "This artifact contains private historical data and is written under data/private by the caller.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _mapping(values: list[str]) -> dict[str, Path]:
    result = {}
    for value in values:
        year, separator, path = value.partition("=")
        if not separator or not year or not path:
            raise ValueError("Use YEAR=PATH")
        result[year] = Path(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", action="append", required=True, help="YEAR=Freqtrade ZIP")
    parser.add_argument("--data-root", action="append", required=True, help="YEAR=Freqtrade data root")
    parser.add_argument("--output", required=True)
    parser.add_argument("--strategy", default="E0V1E64_V26")
    args = parser.parse_args()
    manifest = build_snapshots(_mapping(args.archive), _mapping(args.data_root), Path(args.output), args.strategy)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
