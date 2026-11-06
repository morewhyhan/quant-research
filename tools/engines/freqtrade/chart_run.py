"""Run an exported backtest then render its actual result, without polling old files."""
from pathlib import Path
from tools.engines.freqtrade.runner import main as run_engine
from tools.data.research_io import read_result


def run(arguments, output, strategy=None):
    if not arguments or arguments[0] != 'backtesting':
        raise ValueError('--chart-output requires backtesting')
    if any(a.split('=', 1)[0] in {'--export', '--export-filename', '--backtest-filename', '--backtest-directory'} for a in arguments):
        raise ValueError('Automatic chart export owns result paths; remove custom export arguments')
    try:
        import matplotlib  # Fail before starting an expensive run.
    except ImportError as exc:
        raise ValueError('Install tools/performance/requirements-charts.txt first') from exc
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output exists: choose a new run directory')
    engine_dir = output / 'engine'
    engine_dir.mkdir(parents=True)
    # Freqtrade 2026.5 removed the need for a caller-owned filename.  The
    # directory flag keeps the engine's result and metadata together without
    # relying on its deprecated --export-filename alias.
    code = run_engine([*arguments, '--export', 'trades', '--backtest-directory', str(engine_dir)])
    if code:
        return code
    candidates = list(engine_dir.glob('*.zip')) or list(engine_dir.glob('*.json'))
    valid = []
    for path in candidates:
        try:
            read_result(path, strategy)
            valid.append(path)
        except (ValueError, KeyError, TypeError):
            continue
    if len(valid) != 1:
        raise ValueError('Expected one exported result. For multiple strategies supply --chart-strategy; inspect engine/ for details')
    from tools.performance.charts import render
    render(valid, output/'charts', [strategy] if strategy else None)
    return 0
