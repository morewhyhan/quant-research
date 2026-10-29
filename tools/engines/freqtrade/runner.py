"""Run research-only Freqtrade commands through an explicitly configured engine."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ALLOWED = {"backtesting", "lookahead-analysis", "recursive-analysis", "list-strategies", "--version"}


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if not args or args[0] not in ALLOWED:
        raise SystemExit("Allowed: --version, list-strategies, backtesting, lookahead-analysis, recursive-analysis. Live trading is not supported.")
    config_path = Path(__file__).with_name("config.local.json")
    if not config_path.is_file():
        raise SystemExit("Configure tools/engines/freqtrade/config.local.json using config.example.json first")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["mode"] == "wsl":
        windows_root = ROOT.as_posix()
        if not ROOT.drive:
            raise SystemExit("WSL adapter requires a Windows drive path")
        wsl_root = "/mnt/" + ROOT.drive[0].lower() + windows_root[2:]
        command = ["wsl.exe", "-d", config["distribution"], "--cd", wsl_root, "--",
                   config["python"], "-m", "freqtrade", *args]
    elif config["mode"] == "native":
        command = [config["python"], "-m", "freqtrade", *args]
    else:
        raise SystemExit("mode must be native or wsl")
    return subprocess.run(command, cwd=ROOT, shell=False, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
