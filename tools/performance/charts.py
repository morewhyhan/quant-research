"""Closed-capital charts from data-only Freqtrade results. No trade repricing."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import math

from tools.data.research_io import read_result
from tools.data.time import timestamp
from tools.performance.metrics import number


def _engine_datetime(value, field):
    """Read Freqtrade's metadata timestamps, whose exporter may omit UTC."""
    if value is None:
        return None
    try:
        return timestamp(value).astimezone(timezone.utc)
    except ValueError:
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
        raise ValueError(f'{field} must be timezone-aware (Freqtrade metadata is assumed UTC when it omits a zone)')


def closed_curve(result, initial=None):
    meta = result['engine_reported']
    initial = number(initial if initial is not None else meta.get('starting_balance'), 'starting balance (or --initial)')
    if initial <= 0:
        raise ValueError('Starting balance must be positive')
    grouped = defaultdict(list)
    for trade in result['trades']:
        if trade.get('is_open') is True or not trade.get('close_date'):
            raise ValueError('Charts require closed trades with close_date; open PnL is not equity')
        grouped[timestamp(trade['close_date']).astimezone(timezone.utc)].append(number(trade['profit_abs'], 'profit_abs'))
    start = _engine_datetime(meta['backtest_start'], 'backtest_start') if meta.get('backtest_start') else (min(grouped) if grouped else None)
    end = _engine_datetime(meta['backtest_end'], 'backtest_end') if meta.get('backtest_end') else (max(grouped) if grouped else start)
    if start is None or end < start or (grouped and (min(grouped) < start or max(grouped) > end)):
        raise ValueError('Need a valid backtest interval covering all closes (empty input needs engine dates)')
    balance = peak = initial
    rows = [(start, initial, 0.0)]
    for date, profits in sorted(grouped.items()):
        balance += math.fsum(profits)
        peak = max(peak, balance)
        rows.append((date, balance, balance / peak - 1))
    if rows[-1][0] != end:
        rows.append((end, balance, balance / peak - 1))
    expected = meta.get('final_balance')
    if expected is not None and initial == meta.get('starting_balance'):
        if not math.isclose(balance, number(expected, 'final_balance'), rel_tol=1e-8, abs_tol=1e-6):
            raise ValueError('Closed PnL does not reconcile with engine final_balance')
    stakes = [number(t['stake_amount'], 'stake_amount') for t in result['trades'] if t.get('stake_amount') is not None]
    summary = dict(strategy=result['strategy'], initial=initial, final=balance,
                   return_ratio=balance / initial - 1, max_relative_drawdown=-min(r[2] for r in rows),
                   trades=len(result['trades']), start=start.isoformat(), end=end.isoformat(),
                   currency=meta.get('stake_currency') or 'quote currency',
                   stake_setting=meta.get('stake_amount'),
                   actual_stake_min=min(stakes) if stakes else None,
                   actual_stake_max=max(stakes) if stakes else None)
    return rows, summary


def render(inputs, output, strategies=None, labels=None, initials=None, font=None):
    """Render up to six independent results; preserve evidence via normal save/verify."""
    output = Path(output)
    if output.exists():
        raise ValueError('Output exists: choose a new experiment directory')
    count = len(inputs)
    if not 1 <= count <= 6:
        raise ValueError('Provide one to six result files')
    def options(values, name):
        if values is not None and len(values) != count:
            raise ValueError(f'{name} must be supplied once per input, in input order')
        return values or [None] * count
    strategies, labels, initials = [options(v, n) for v, n in
                                    ((strategies, '--strategy'), (labels, '--label'), (initials, '--initial'))]
    results = [read_result(p, s) for p, s in zip(inputs, strategies)]
    curves = [closed_curve(r, i) for r, i in zip(results, initials)]
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import font_manager, dates
        from matplotlib.ticker import StrMethodFormatter
    except ImportError as exc:
        raise ValueError('Chart dependency missing: pip install -r tools/performance/requirements-charts.txt') from exc
    # Portable preference order; WSL can use Windows fonts without a per-user path.
    candidates = [font] if font else ['/mnt/c/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/msyh.ttc']
    chosen = next((p for p in candidates if p and Path(p).is_file()), None)
    if font and not chosen:
        raise ValueError('--font must point to an existing font file')
    if chosen:
        font_manager.fontManager.addfont(chosen)
        family = font_manager.FontProperties(fname=chosen).get_name()
    else:
        family = 'DejaVu Sans'
    chinese = bool(chosen)
    captions = ('已平仓资金 / ', '相对历史高点回撤 / %', '期末', '收益', '最大相对回撤') if chinese else (
        'Closed capital / ', 'Drawdown from running peak / %', 'Final', 'Return', 'Max relative drawdown')
    summaries = []
    for result, (_, summary), label in zip(results, curves, labels):
        summary['label'] = label or result['strategy'] or 'Result'
        summaries.append(summary)
    # Identity is checked independently of file ordering; equal timestamps remain grouped in equity.
    def signature(r):
        fields = ('pair', 'is_short', 'open_date', 'close_date', 'exit_reason')
        if any(any(k not in t for k in fields) for t in r['trades']):
            return None
        return sorted((tuple(str(t[k]) for k in fields) for t in r['trades']))
    signatures = [signature(r) for r in results]
    identical = None if any(s is None for s in signatures) else all(s == signatures[0] for s in signatures)
    cols = min(count, 3)
    bands = math.ceil(count / cols)
    colors = ['#356ab0', '#25836a', '#a77a19', '#8a6996', '#427f8b', '#a66455']
    with plt.rc_context({'font.family': family, 'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.unicode_minus': False}):
        fig, axes = plt.subplots(2 * bands, cols, figsize=(6.2 * cols, 7.4 * bands), squeeze=False, layout='constrained')
        dd_floor = min(-5, min(-s['max_relative_drawdown'] * 100 for s in summaries) * 1.12)
        for index, ((rows, summary), color) in enumerate(zip(curves, colors)):
            band, col = divmod(index, cols)
            ax, ddax = axes[2*band, col], axes[2*band+1, col]
            x, y, dd = zip(*rows)
            ax.step(x, y, where='post', color=color, lw=1.25)
            ax.axhline(summary['initial'], color='#888888', ls='--', lw=.8)
            ax.set_ylim(min(0, min(y)*1.1), max(y)*1.22)
            ax.set_title(summary['label'], fontsize=13)
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
            ax.set_ylabel(captions[0] + summary['currency'])
            ax.text(.025, .96, f"{captions[2]} {summary['final']:,.2f}\n{captions[3]} {summary['return_ratio']:.2%}",
                    transform=ax.transAxes, va='top', bbox=dict(facecolor='white', alpha=.85, edgecolor='none'))
            ddax.fill_between(x, [v*100 for v in dd], 0, step='post', color=color, alpha=.65)
            ddax.set_ylim(dd_floor, 0)
            ddax.set_title(f"{captions[4]} {summary['max_relative_drawdown']:.2%}")
            ddax.set_ylabel(captions[1])
            for a in (ax, ddax):
                locator = dates.AutoDateLocator(minticks=3, maxticks=7)
                a.xaxis.set_major_locator(locator)
                a.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m', tz=timezone.utc))
                a.tick_params(axis='x', rotation=30)
                a.grid(color='#dddddd', alpha=.55)
        for index in range(count, bands*cols):
            band, col = divmod(index, cols)
            axes[band*2, col].set_visible(False)
            axes[band*2+1, col].set_visible(False)
        note = ('回测已平仓资金；不含浮仓和外部现金流调整；UTC\n线性坐标，各列金额刻度独立；回撤刻度统一'
                if chinese else 'Backtest closed capital; excludes floating PnL and cash-flow adjustments; UTC\nLinear independent capital scales; common drawdown scale')
        fig.suptitle(note, fontsize=14)
        from tools.experiments.storage import save, digest, dump
        try:
            save(output, {'chart': 'closed-capital', 'series': summaries,
                          'identical_entry_exit_path': identical,
                          'limitations': 'No repricing; comparison conditions may differ; closed PnL, not mark-to-market equity'}, inputs)
            fig.savefig(output/'equity-drawdowns.png', dpi=160)
            fig.savefig(output/'equity-drawdowns.svg')
            for i, (rows, _) in enumerate(curves):
                with (output/f'curve-{i+1}.csv').open('w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['time_utc', 'closed_capital', 'drawdown_ratio'])
                    writer.writerows((d.isoformat(), e, dd) for d,e,dd in rows)
            manifest_path = output/'manifest.json'
            manifest = __import__('json').loads(manifest_path.read_text())
            manifest['chart_runtime'] = {'matplotlib': matplotlib.__version__, 'font': chosen or family}
            for p in [output/'equity-drawdowns.png', output/'equity-drawdowns.svg', *output.glob('curve-*.csv')]:
                manifest['artifact_hashes'][p.name] = digest(p)
            manifest_path.write_text(dump(manifest), encoding='utf-8')
        finally:
            plt.close(fig)
    return summaries
