"""Dispatch for main.py collect | nws | run."""

import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("collect", "nws", "run"):
        print("Usage: python main.py collect | nws | run")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "collect":
        from weather_modeling.cli.collect_forecast import main as collect_main
        collect_main()
    elif cmd == "nws":
        from weather_modeling.cli.collect_nws import main as nws_main
        nws_main()
    else:
        from weather_modeling.cli.run_loop import run_indefinitely, parse_run_args
        data_dir, interval = parse_run_args()
        run_indefinitely(data_dir=data_dir, interval_hours=interval)
