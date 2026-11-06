"""Self-contained HTML research reports from data-only Freqtrade results.

The report deliberately uses the same Matplotlib visual language as the
existing chart command.  It embeds SVG charts in one HTML file and keeps the
metrics, manifest, and curve CSV files beside it as auditable evidence.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from io import StringIO
import csv
import json
import math
from pathlib import Path
from statistics import stdev

from tools.data.research_io import read_result
from tools.data.time import timestamp
from tools.performance.charts import closed_curve
from tools.performance.metrics import number, trade_metrics


COLORS = ['#356ab0', '#25836a', '#a77a19', '#8a6996', '#427f8b', '#a66455']


def _options(values, name, count):
    if values is not None and len(values) != count:
        raise ValueError(f'{name} must be supplied once per input, in input order')
    return values or [None] * count


def _consecutive_losses(trades):
    current = longest = 0
    for trade in trades:
        if number(trade['profit_abs'], 'profit_abs') < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _signature(result):
    fields = ('pair', 'is_short', 'open_date', 'close_date', 'exit_reason')
    if any(any(k not in t for k in fields) for t in result['trades']):
        return None
    return sorted(tuple(str(t[k]) for k in fields) for t in result['trades'])


def _month_sequence(start, end):
    year, month = start.year, start.month
    result = []
    while (year, month) <= (end.year, end.month):
        result.append((year, month))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return result


def monthly_returns(rows, initial):
    """Return closed-capital month returns, carrying balance through empty months."""
    if not rows:
        return []
    start, end = rows[0][0], rows[-1][0]
    months = _month_sequence(start, end)
    pointer = 0
    previous = float(initial)
    previous_end = previous
    values = []
    for year, month in months:
        if month == 12:
            next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        month_end = next_month.timestamp() - 1
        while pointer < len(rows) and rows[pointer][0].timestamp() <= month_end:
            previous_end = rows[pointer][1]
            pointer += 1
        end_balance = previous_end if 'previous_end' in locals() else previous
        values.append({'month': f'{year:04d}-{month:02d}',
                       'return_ratio': end_balance / previous - 1 if previous else None,
                       'end_balance': end_balance})
        previous = end_balance
    return values


def _group_stats(trades, field):
    grouped = defaultdict(list)
    for trade in trades:
        value = trade.get(field) or '(未标记)'
        grouped[str(value)].append(trade)
    rows = []
    for group, items in grouped.items():
        metrics = trade_metrics(items)
        rows.append({'group': group, 'trades': metrics['trades'],
                     'win_rate': metrics['win_rate'],
                     'net_profit_abs': metrics['net_profit_abs'],
                     'profit_factor': metrics['profit_factor'],
                     'mean_profit_abs': metrics['mean_profit_abs']})
    return sorted(rows, key=lambda row: row['net_profit_abs'], reverse=True)


def _summary(result, rows, summary, label):
    trade = trade_metrics(result['trades'])
    engine = result['engine_reported']
    value = dict(summary)
    value.update({
        'label': label or result['strategy'] or 'Result',
        'strategy': result['strategy'],
        'wins': trade['wins'],
        'losses': trade['losses'],
        'breakeven': trade['breakeven'],
        'win_rate': trade['win_rate'],
        'profit_factor': engine.get('profit_factor') if engine.get('profit_factor') is not None else trade['profit_factor'],
        'mean_profit_abs': trade['mean_profit_abs'],
        'best_trade_abs': trade['best_trade_abs'],
        'worst_trade_abs': trade['worst_trade_abs'],
        'max_consecutive_losses': _consecutive_losses(result['trades']),
        'account_max_drawdown': engine.get('max_drawdown_account'),
        'account_max_drawdown_abs': engine.get('max_drawdown_abs'),
        'engine_final_balance': engine.get('final_balance'),
        'monthly_returns': monthly_returns(rows, summary['initial']),
        'entry_tags': _group_stats(result['trades'], 'enter_tag'),
        'exit_reasons': _group_stats(result['trades'], 'exit_reason'),
    })
    return value


def _daily_balances(rows):
    """Carry closed capital forward once per UTC day for rolling diagnostics."""
    if not rows:
        return []
    day = rows[0][0].replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = rows[-1][0].replace(hour=0, minute=0, second=0, microsecond=0)
    pointer = 0
    balance = rows[0][1]
    values = []
    while day <= end_day:
        next_day = day + timedelta(days=1)
        while pointer < len(rows) and rows[pointer][0] < next_day:
            balance = rows[pointer][1]
            pointer += 1
        values.append((day, balance))
        day = next_day
    return values


def _rolling_values(rows):
    daily = _daily_balances(rows)
    if len(daily) < 2:
        return []
    balances = [item[1] for item in daily]
    daily_returns = [None] + [balances[i] / balances[i - 1] - 1 for i in range(1, len(balances))]
    values = []
    for i, (date, balance) in enumerate(daily):
        r30 = balance / balances[i - 30] - 1 if i >= 30 else None
        r90 = balance / balances[i - 90] - 1 if i >= 90 else None
        window = [v for v in daily_returns[max(1, i - 29):i + 1] if v is not None]
        volatility = stdev(window) * math.sqrt(365) if len(window) > 1 else None
        values.append({'date': date, 'return_30d': r30, 'return_90d': r90, 'volatility_30d': volatility})
    return values


def _trade_excursions(trades):
    """Calculate price MAE/MFE from exported min/max rates, without repricing."""
    values = []
    for trade in trades:
        required = ('open_rate', 'min_rate', 'max_rate')
        if any(key not in trade or trade[key] in (None, 0) for key in required):
            continue
        open_rate = number(trade['open_rate'], 'open_rate')
        min_rate = number(trade['min_rate'], 'min_rate')
        max_rate = number(trade['max_rate'], 'max_rate')
        if trade.get('is_short'):
            mfe = open_rate / min_rate - 1
            mae = open_rate / max_rate - 1
        else:
            mfe = max_rate / open_rate - 1
            mae = min_rate / open_rate - 1
        values.append({'mae': mae, 'mfe': mfe, 'profit_ratio': trade.get('profit_ratio'),
                       'pair': trade.get('pair', '')})
    return values


def _trade_durations(trades):
    values = []
    for trade in trades:
        duration = trade.get('trade_duration')
        if duration is None and trade.get('open_date') and trade.get('close_date'):
            duration = (timestamp(trade['close_date']) - timestamp(trade['open_date'])).total_seconds() / 60
        if duration is not None:
            values.append(float(duration) / 60)
    return values


def _stake_points(trades):
    points = []
    for trade in trades:
        if trade.get('stake_amount') is None or not trade.get('close_date'):
            continue
        points.append((timestamp(trade['close_date']).astimezone(timezone.utc),
                       number(trade['stake_amount'], 'stake_amount')))
    return points


def _loss_streak(trades):
    cumulative = 0.0
    streak = 0
    result = []
    for index, trade in enumerate(trades, start=1):
        profit = number(trade['profit_abs'], 'profit_abs')
        cumulative += profit
        streak = streak + 1 if profit < 0 else 0
        result.append((index, cumulative, streak))
    return result


def _font_setup(font):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import font_manager
    candidates = [font] if font else ['/mnt/c/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/msyh.ttc']
    chosen = next((path for path in candidates if path and Path(path).is_file()), None)
    if font and not chosen:
        raise ValueError('--font must point to an existing font file')
    if chosen:
        font_manager.fontManager.addfont(chosen)
        family = font_manager.FontProperties(fname=chosen).get_name()
    else:
        family = 'DejaVu Sans'
    return matplotlib, family, chosen


def _svg(fig):
    buffer = StringIO()
    fig.savefig(buffer, format='svg', bbox_inches='tight')
    text = buffer.getvalue()
    return text[text.find('<svg'):]


def _figures(curves, summaries, results, profit_values, font):
    matplotlib, family, chosen = _font_setup(font)
    import matplotlib.pyplot as plt
    from matplotlib import dates
    from matplotlib.ticker import PercentFormatter, StrMethodFormatter

    labels = [item['label'] for item in summaries]
    with plt.rc_context({'font.family': family, 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.unicode_minus': False}):
        # Normalized return is the primary cross-strategy comparison.
        fig, ax = plt.subplots(figsize=(12, 4.8), layout='constrained')
        for (rows, _), summary, color in zip(curves, summaries, COLORS):
            x, capital, _ = zip(*rows)
            ax.step(x, [(v / summary['initial'] - 1) * 100 for v in capital],
                    where='post', color=color, lw=1.35, label=summary['label'])
        ax.axhline(0, color='#888888', ls='--', lw=.8)
        ax.set_title('累计收益率（以各自初始资金归一化）')
        ax.set_ylabel('累计收益率 / %')
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax.legend(loc='upper left', frameon=False, ncol=min(3, len(labels)))
        ax.grid(color='#dddddd', alpha=.55)
        ax.xaxis.set_major_locator(dates.AutoDateLocator(minticks=4, maxticks=9))
        ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m', tz=timezone.utc))
        ax.tick_params(axis='x', rotation=30)
        return_svg = _svg(fig)
        plt.close(fig)

        # Absolute closed capital uses independent panels so fixed versions do not flatten.
        cols = min(2, len(curves))
        rows_count = math.ceil(len(curves) / cols)
        fig, axes = plt.subplots(rows_count, cols, figsize=(7 * cols, 3.8 * rows_count),
                                 squeeze=False, layout='constrained')
        for index, ((points, _), summary, color) in enumerate(zip(curves, summaries, COLORS)):
            ax = axes[index // cols][index % cols]
            x, capital, _ = zip(*points)
            ax.step(x, capital, where='post', color=color, lw=1.3)
            ax.axhline(summary['initial'], color='#888888', ls='--', lw=.8)
            ax.set_title(f"{summary['label']}  |  期末 {summary['final']:,.2f} USDT")
            ax.set_ylabel('已平仓资金 / USDT')
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
            ax.grid(color='#dddddd', alpha=.55)
            ax.xaxis.set_major_locator(dates.AutoDateLocator(minticks=3, maxticks=7))
            ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m', tz=timezone.utc))
            ax.tick_params(axis='x', rotation=30)
        for index in range(len(curves), rows_count * cols):
            axes[index // cols][index % cols].set_visible(False)
        equity_svg = _svg(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(12, 4.8), layout='constrained')
        floor = min(-5, min(-summary['max_relative_drawdown'] * 100 for summary in summaries) * 1.12)
        for (points, _), summary, color in zip(curves, summaries, COLORS):
            x, _, drawdown = zip(*points)
            ax.step(x, [v * 100 for v in drawdown], where='post', color=color, lw=1.2,
                    label=f"{summary['label']} ({summary['max_relative_drawdown']:.2%})")
        ax.axhline(0, color='#888888', lw=.8)
        ax.set_ylim(floor, 0)
        ax.set_title('从历史高点回撤（已平仓资金口径）')
        ax.set_ylabel('回撤 / %')
        ax.legend(loc='lower left', frameon=False, ncol=min(2, len(labels)))
        ax.grid(color='#dddddd', alpha=.55)
        ax.xaxis.set_major_locator(dates.AutoDateLocator(minticks=4, maxticks=9))
        ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m', tz=timezone.utc))
        ax.tick_params(axis='x', rotation=30)
        drawdown_svg = _svg(fig)
        plt.close(fig)

        months = sorted({item['month'] for summary in summaries for item in summary['monthly_returns']})
        matrix = []
        for summary in summaries:
            lookup = {item['month']: item['return_ratio'] for item in summary['monthly_returns']}
            matrix.append([lookup.get(month, 0.0) * 100 for month in months])
        fig, ax = plt.subplots(figsize=(max(10, .9 * len(months)), max(3.5, .65 * len(labels) + 1.6)),
                               layout='constrained')
        image = ax.imshow(matrix, aspect='auto', cmap='RdYlGn', vmin=min(-20, min(min(row) for row in matrix)),
                          vmax=max(20, max(max(row) for row in matrix)))
        ax.set_xticks(range(len(months)), months, rotation=35, ha='right')
        ax.set_yticks(range(len(labels)), labels)
        ax.set_title('月度收益率热力图（闭合资金）')
        for row_index, row in enumerate(matrix):
            for col_index, value in enumerate(row):
                ax.text(col_index, row_index, f'{value:.1f}%', ha='center', va='center', fontsize=8)
        fig.colorbar(image, ax=ax, label='月收益率 / %')
        monthly_svg = _svg(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 5.3), layout='constrained')
        for summary, color in zip(summaries, COLORS):
            dd = (summary['account_max_drawdown'] if summary['account_max_drawdown'] is not None
                  else summary['max_relative_drawdown']) * 100
            ret = summary['return_ratio'] * 100
            ax.scatter(dd, ret, color=color, s=85, zorder=3)
            ax.annotate(summary['label'], (dd, ret), xytext=(7, 5), textcoords='offset points', fontsize=9)
        ax.set_xlabel('最大账户回撤 / %')
        ax.set_ylabel('累计收益率 / %')
        ax.set_title('风险—收益位置')
        ax.grid(color='#dddddd', alpha=.55)
        risk_svg = _svg(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 4.8), layout='constrained')
        values = [[value * 100 for value in values] for values in profit_values]
        if any(values):
            try:
                ax.boxplot(values, tick_labels=labels, showfliers=False)
            except TypeError:  # Matplotlib < 3.9
                ax.boxplot(values, labels=labels, showfliers=False)
            ax.axhline(0, color='#888888', ls='--', lw=.8)
            ax.set_ylabel('单笔收益率 / %')
            ax.set_title('单笔收益率分布（隐藏离群点，离群点仍保留在原始结果）')
            ax.grid(axis='y', color='#dddddd', alpha=.55)
            ax.tick_params(axis='x', rotation=20)
        else:
            ax.text(.5, .5, '结果中没有 profit_ratio，无法绘制单笔收益率分布', ha='center', va='center')
            ax.set_axis_off()
        trade_svg = _svg(fig)
        plt.close(fig)

        # Rolling return and annualized volatility from the closed-capital path.
        rolling = [_rolling_values(points) for points, _ in curves]
        fig, axes = plt.subplots(2, 1, figsize=(12, 7.4), sharex=True, layout='constrained')
        for values, summary, color in zip(rolling, summaries, COLORS):
            if not values:
                continue
            dates_x = [item['date'] for item in values]
            r30 = [item['return_30d'] * 100 if item['return_30d'] is not None else math.nan for item in values]
            r90 = [item['return_90d'] * 100 if item['return_90d'] is not None else math.nan for item in values]
            vol = [item['volatility_30d'] * 100 if item['volatility_30d'] is not None else math.nan for item in values]
            axes[0].plot(dates_x, r30, color=color, lw=1.05, alpha=.75)
            axes[0].plot(dates_x, r90, color=color, lw=1.55, label=f"{summary['label']} · 90d")
            axes[1].plot(dates_x, vol, color=color, lw=1.25, label=summary['label'])
        axes[0].axhline(0, color='#888888', ls='--', lw=.8)
        axes[0].set_title('滚动收益率（细线 30 天，粗线 90 天）')
        axes[0].set_ylabel('收益率 / %')
        axes[1].set_title('30 天滚动年化波动率')
        axes[1].set_ylabel('波动率 / %')
        for ax in axes:
            ax.grid(color='#dddddd', alpha=.55)
            ax.legend(loc='upper left', frameon=False, ncol=min(3, len(labels)))
            ax.xaxis.set_major_locator(dates.AutoDateLocator(minticks=4, maxticks=9))
            ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m', tz=timezone.utc))
            ax.tick_params(axis='x', rotation=30)
        rolling_svg = _svg(fig)
        plt.close(fig)

        # Price excursion diagnostics: MAE/MFE are taken from Freqtrade's exported min/max rates.
        excursion = [_trade_excursions(result['trades']) for result in results]
        cols = min(2, len(results))
        rows_count = math.ceil(len(results) / cols)
        fig, axes = plt.subplots(rows_count, cols, figsize=(6.8 * cols, 4.4 * rows_count),
                                 squeeze=False, layout='constrained')
        for index, (values, summary, color) in enumerate(zip(excursion, summaries, COLORS)):
            ax = axes[index // cols][index % cols]
            if values:
                winners = [item for item in values if item.get('profit_ratio') is not None and item['profit_ratio'] > 0]
                losers = [item for item in values if item.get('profit_ratio') is not None and item['profit_ratio'] <= 0]
                if winners:
                    ax.scatter([item['mae'] * 100 for item in winners], [item['mfe'] * 100 for item in winners],
                               s=10, alpha=.45, color='#25836a', label='盈利')
                if losers:
                    ax.scatter([item['mae'] * 100 for item in losers], [item['mfe'] * 100 for item in losers],
                               s=10, alpha=.45, color='#a66455', label='亏损')
                ax.axvline(0, color='#888888', ls='--', lw=.7)
                ax.axhline(0, color='#888888', ls='--', lw=.7)
                ax.legend(loc='best', frameon=False)
            else:
                ax.text(.5, .5, '缺少 min_rate / max_rate', ha='center', va='center')
            ax.set_title(summary['label'])
            ax.set_xlabel('MAE：最大不利价格移动 / %')
            ax.set_ylabel('MFE：最大有利价格移动 / %')
            ax.grid(color='#dddddd', alpha=.55)
        for index in range(len(results), rows_count * cols):
            axes[index // cols][index % cols].set_visible(False)
        excursion_svg = _svg(fig)
        plt.close(fig)

        # Holding time and actual stake size are useful execution diagnostics.
        durations = [_trade_durations(result['trades']) for result in results]
        fig, ax = plt.subplots(figsize=(10, 4.8), layout='constrained')
        if any(durations):
            try:
                ax.boxplot(durations, tick_labels=labels, showfliers=False)
            except TypeError:  # Matplotlib < 3.9
                ax.boxplot(durations, labels=labels, showfliers=False)
            ax.set_ylabel('持仓时间 / 小时')
            ax.set_title('持仓时间分布（隐藏离群点）')
            ax.tick_params(axis='x', rotation=20)
            ax.grid(axis='y', color='#dddddd', alpha=.55)
        else:
            ax.text(.5, .5, '缺少持仓时间字段', ha='center', va='center')
            ax.set_axis_off()
        duration_svg = _svg(fig)
        plt.close(fig)

        fig, axes = plt.subplots(2, 1, figsize=(12, 7.4), sharex=False, layout='constrained')
        for result, summary, color in zip(results, summaries, COLORS):
            streak = _loss_streak(result['trades'])
            if streak:
                x, cumulative, loss_streak = zip(*streak)
                axes[0].plot(x, cumulative, color=color, lw=1.05, label=summary['label'])
                axes[1].step(x, loss_streak, where='post', color=color, lw=1.1, label=summary['label'])
        axes[0].set_title('逐笔累计已实现盈亏')
        axes[0].set_ylabel('累计盈亏 / USDT')
        axes[1].set_title('逐笔连续亏损计数')
        axes[1].set_ylabel('连续亏损笔数')
        axes[1].set_xlabel('交易序号')
        for ax in axes:
            ax.grid(color='#dddddd', alpha=.55)
            ax.legend(loc='upper left', frameon=False, ncol=min(3, len(labels)))
        streak_svg = _svg(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(12, 4.8), layout='constrained')
        for result, summary, color in zip(results, summaries, COLORS):
            points = _stake_points(result['trades'])
            if points:
                x, stake = zip(*points)
                ax.step(x, stake, where='post', color=color, lw=1.1, label=summary['label'])
        ax.set_title('每笔实际仓位金额（按平仓时间）')
        ax.set_ylabel('实际仓位 / USDT')
        ax.legend(loc='upper left', frameon=False, ncol=min(3, len(labels)))
        ax.grid(color='#dddddd', alpha=.55)
        ax.xaxis.set_major_locator(dates.AutoDateLocator(minticks=4, maxticks=9))
        ax.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m', tz=timezone.utc))
        ax.tick_params(axis='x', rotation=30)
        stake_svg = _svg(fig)
        plt.close(fig)

    return {'return': return_svg, 'equity': equity_svg, 'drawdown': drawdown_svg,
            'monthly': monthly_svg, 'risk': risk_svg, 'trades': trade_svg,
            'rolling': rolling_svg, 'excursion': excursion_svg, 'duration': duration_svg,
            'streak': streak_svg, 'stake': stake_svg,
            'runtime': {'matplotlib': matplotlib.__version__, 'font': chosen or family}}


def _fmt_number(value, digits=2):
    return '—' if value is None else f'{value:,.{digits}f}'


def _fmt_pct(value, digits=2):
    return '—' if value is None else f'{value:.{digits}%}'


def _table(headers, rows):
    head = ''.join(f'<th>{escape(str(item))}</th>' for item in headers)
    body = []
    for row in rows:
        body.append('<tr>' + ''.join(f'<td>{item}</td>' for item in row) + '</tr>')
    return f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def _attribution_tables(summaries):
    blocks = []
    for summary in summaries:
        tag_rows = []
        for row in summary['entry_tags']:
            tag_rows.append([escape(row['group']), str(row['trades']), _fmt_pct(row['win_rate']),
                             _fmt_number(row['net_profit_abs']), _fmt_number(row['profit_factor'])])
        exit_rows = []
        for row in summary['exit_reasons']:
            exit_rows.append([escape(row['group']), str(row['trades']), _fmt_pct(row['win_rate']),
                              _fmt_number(row['net_profit_abs']), _fmt_number(row['profit_factor'])])
        blocks.append(f'''<details class="subreport"><summary>{escape(summary['label'])}：入场与退出归因</summary>
        <h4>入场标签</h4>{_table(['标签', '交易数', '胜率', '净盈亏 USDT', 'PF'], tag_rows)}
        <h4>退出原因</h4>{_table(['退出原因', '交易数', '胜率', '净盈亏 USDT', 'PF'], exit_rows)}</details>''')
    return ''.join(blocks)


def _html(metrics, charts):
    summaries = metrics['series']
    summary_rows = []
    for item in summaries:
        summary_rows.append([
            escape(item['label']), str(item['trades']), _fmt_pct(item['win_rate']),
            _fmt_number(item['final']), _fmt_pct(item['return_ratio']),
            _fmt_number(item['profit_factor']), _fmt_pct(item['account_max_drawdown']),
            _fmt_pct(item['max_relative_drawdown']), str(item['max_consecutive_losses'])])
    source_rows = []
    for item in metrics['inputs']:
        source_rows.append([escape(item['label']), escape(item['path']), item['strategy'] or '自动选择', escape(item['initial'])])
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>量化策略研究报告：{escape(metrics['title'])}</title>
<style>
:root {{ color-scheme: light; --ink:#1d2733; --muted:#66717f; --line:#dfe4ea; --paper:#fff; --wash:#f5f7fa; --accent:#356ab0; }}
* {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:#eef1f5; font-family:"Microsoft YaHei", "Segoe UI", sans-serif; line-height:1.55; }}
.page {{ max-width:1440px; margin:0 auto; padding:28px 30px 60px; }} header {{ background:var(--paper); border:1px solid var(--line); padding:30px 34px 24px; }}
h1 {{ margin:0 0 8px; font-size:28px; letter-spacing:.01em; }} h2 {{ margin:38px 0 12px; font-size:21px; }} h3 {{ margin:22px 0 8px; font-size:16px; }} h4 {{ margin:18px 0 7px; }}
.subtitle,.note {{ color:var(--muted); }} nav {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:22px; }} nav a {{ color:var(--accent); text-decoration:none; border:1px solid #cbd7e5; background:#f7faff; padding:5px 10px; border-radius:4px; font-size:13px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-top:18px; }} .card {{ background:var(--paper); border:1px solid var(--line); padding:15px 17px; }} .card .label {{ color:var(--muted); font-size:12px; }} .card .value {{ font-size:22px; font-weight:600; margin-top:4px; }}
.panel {{ background:var(--paper); border:1px solid var(--line); padding:18px; margin-top:14px; overflow:auto; }} .chart svg {{ display:block; width:100%; height:auto; }} .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(520px,1fr)); gap:14px; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }} th,td {{ border-bottom:1px solid var(--line); text-align:right; padding:8px 9px; white-space:nowrap; }} th:first-child,td:first-child {{ text-align:left; }} th {{ background:var(--wash); font-weight:600; }}
details {{ background:var(--paper); border:1px solid var(--line); padding:12px 15px; margin-top:12px; }} summary {{ cursor:pointer; font-weight:600; }} code {{ background:#f0f3f6; padding:1px 4px; border-radius:3px; }} .small {{ font-size:12px; color:var(--muted); }} footer {{ margin-top:28px; color:var(--muted); font-size:12px; }}
@media(max-width:700px) {{ .page {{ padding:12px; }} header,.panel {{ padding:14px; }} .grid {{ grid-template-columns:1fr; }} h1 {{ font-size:23px; }} }}
</style></head><body><main class="page">
<header><h1>量化策略研究报告：{escape(metrics['title'])}</h1>
<div class="subtitle">生成时间：{escape(metrics['generated_at'])} · 图表风格沿用研究图表 · 时间统一为 UTC</div>
<nav><a href="#overview">总览</a><a href="#performance">收益与资金</a><a href="#risk">风险</a><a href="#stability">稳定性</a><a href="#diagnostics">交易诊断</a><a href="#attribution">归因</a><a href="#provenance">口径与来源</a></nav></header>
<section id="overview"><h2>总览</h2><div class="cards">
<div class="card"><div class="label">比较策略</div><div class="value">{len(summaries)}</div></div>
<div class="card"><div class="label">共同初始资金</div><div class="value">{_fmt_number(summaries[0]['initial'])} USDT</div></div>
<div class="card"><div class="label">最高累计收益</div><div class="value">{_fmt_pct(max(x['return_ratio'] for x in summaries))}</div></div>
<div class="card"><div class="label">最低账户回撤</div><div class="value">{_fmt_pct(min(x['account_max_drawdown'] for x in summaries if x['account_max_drawdown'] is not None))}</div></div>
</div><div class="panel">{_table(['策略','交易数','胜率','最终余额','收益率','PF','账户最大回撤','闭合资金回撤','最大连续亏损'], summary_rows)}
<p class="note">账户最大回撤来自 Freqtrade 钱包口径；闭合资金回撤由平仓 profit_abs 重新累加。两者不是同一个指标，不能混用。</p></div></section>
<section id="performance"><h2>收益与资金</h2><div class="panel chart"><h3>累计收益率</h3>{charts['return']}</div><div class="panel chart"><h3>绝对资金曲线</h3>{charts['equity']}</div></section>
<section id="risk"><h2>风险</h2><div class="panel chart"><h3>水下回撤</h3>{charts['drawdown']}</div><div class="grid"><div class="panel chart"><h3>风险—收益位置</h3>{charts['risk']}</div><div class="panel"><h3>风险口径</h3><p>本报告没有从历史 K 线重新定价未平仓交易，因此不能生成真正的 mark-to-market 权益曲线。当前结果只包含已平仓资金和引擎报告的账户回撤。</p><p>如果要研究实盘风险，还需要导入逐时钱包权益、未平仓浮盈亏、资金费、手续费和外部充提记录。</p></div></div></section>
<section id="stability"><h2>稳定性</h2><div class="panel chart"><h3>滚动收益与波动率</h3>{charts['rolling']}</div><div class="panel chart"><h3>月度收益热力图</h3>{charts['monthly']}</div><div class="panel"><h3>月份收益数据</h3>{_table(['策略','月份','收益率','月末资金'], [[escape(s['label']), m['month'], _fmt_pct(m['return_ratio']), _fmt_number(m['end_balance'])] for s in summaries for m in s['monthly_returns']])}</div></section>
<section id="diagnostics"><h2>交易诊断</h2><div class="panel chart"><h3>单笔收益率分布</h3>{charts['trades']}</div><div class="panel chart"><h3>MAE / MFE：最大不利与有利价格移动</h3>{charts['excursion']}</div><div class="grid"><div class="panel chart"><h3>持仓时间</h3>{charts['duration']}</div><div class="panel chart"><h3>连续亏损与累计已实现盈亏</h3>{charts['streak']}</div></div><div class="panel chart"><h3>实际仓位金额</h3>{charts['stake']}</div><div class="grid"><div class="panel"><h3>交易统计</h3>{_table(['策略','均值 / USDT','最佳 / USDT','最差 / USDT','最大连续亏损'], [[escape(s['label']), _fmt_number(s['mean_profit_abs']), _fmt_number(s['best_trade_abs']), _fmt_number(s['worst_trade_abs']), str(s['max_consecutive_losses'])] for s in summaries])}</div><div class="panel"><h3>说明</h3><p>单笔收益率分布优先使用 Freqtrade 的 <code>profit_ratio</code>。MAE/MFE 使用 ZIP 中的 <code>min_rate</code>、<code>max_rate</code>，表示价格路径，不重新模拟成交。</p></div></div></section>
<section id="attribution"><h2>入场与退出归因</h2>{_attribution_tables(summaries)}</section>
<section id="provenance"><h2>口径与来源</h2><div class="panel"><p><strong>报告限制：</strong>{escape(metrics['limitations'])}</p>{_table(['标签','输入文件','策略','初始资金'], source_rows)}<p class="small">证据文件：<a href="metrics.json">metrics.json</a> · <a href="manifest.json">manifest.json</a> · 每条资金曲线 CSV 见本目录。HTML 内的图表为 SVG 内嵌，不依赖网络。</p></div></section>
<footer>这是研究报告，不是实盘控制台。未连接交易所、未下单、未修改策略和账户配置。</footer>
</main></body></html>'''
    return html


def render(inputs, output, strategies=None, labels=None, initials=None, font=None, title='策略比较'):
    """Generate a self-contained HTML report and auditable companion files."""
    output = Path(output)
    if output.exists():
        raise ValueError('Output exists: choose a new experiment directory')
    count = len(inputs)
    if not 1 <= count <= 6:
        raise ValueError('Provide one to six result files')
    strategies = _options(strategies, '--strategy', count)
    labels = _options(labels, '--label', count)
    initials = _options(initials, '--initial', count)
    results = [read_result(path, strategy) for path, strategy in zip(inputs, strategies)]
    curves = [closed_curve(result, initial) for result, initial in zip(results, initials)]
    summaries = [_summary(result, rows, summary, label)
                 for result, (rows, summary), label in zip(results, curves, labels)]
    signatures = [_signature(result) for result in results]
    identical = None if any(item is None for item in signatures) else all(item == signatures[0] for item in signatures)
    profit_values = [[float(t['profit_ratio']) for t in result['trades'] if t.get('profit_ratio') is not None]
                     for result in results]
    figures = _figures(curves, summaries, results, profit_values, font)
    sources = [{'label': summary['label'], 'path': str(Path(path)), 'strategy': result['strategy'],
                'initial': str(summary['initial'])}
               for path, result, summary in zip(inputs, results, summaries)]
    metrics = {
        'report': 'strategy-comparison-html', 'title': title,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'series': summaries, 'inputs': sources,
        'identical_entry_exit_path': identical,
        'limitations': 'No repricing; closed-capital curves exclude floating PnL and external cash flows; Freqtrade account drawdown is kept as a separate engine metric.',
    }
    from tools.experiments.storage import digest, dump, save
    save(output, metrics, inputs)
    for index, (rows, _) in enumerate(curves, start=1):
        with (output / f'curve-{index}.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['time_utc', 'closed_capital', 'drawdown_ratio'])
            writer.writerows((date.isoformat(), capital, drawdown) for date, capital, drawdown in rows)
    (output / 'report.html').write_text(_html(metrics, figures), encoding='utf-8')
    manifest_path = output / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['report_runtime'] = figures['runtime']
    for path in [output / 'report.html', *output.glob('curve-*.csv')]:
        manifest['artifact_hashes'][path.name] = digest(path)
    manifest_path.write_text(dump(manifest), encoding='utf-8')
    return summaries
