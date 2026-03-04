"""
Weather data collection: Open-Meteo, NWS climate reports, and AAA gas prices.

Usage:
  python main.py collect  # Fetch and save Open-Meteo forecast to data/forecast_*.csv
  python main.py nws      # Scrape NWS Climate (CLI) reports into data/nws_daily.csv
  python main.py nws --historical   # Also scrape version links for historical backfill
  python main.py run     # Run indefinitely: every N hours check for today's gas data, fetch if missing
"""

import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("collect", "nws", "run"):
        print("Usage: python main.py collect | nws | run")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "collect":
        from collect_forecast import main as collect_main
        collect_main()
    elif cmd == "nws":
        from collect_nws import main as nws_main
        nws_main()
    else:
        from run_loop import run_indefinitely, _parse_run_args
        data_dir, interval = _parse_run_args()
        run_indefinitely(data_dir=data_dir, interval_hours=interval)


if __name__ == "__main__":
    main()
